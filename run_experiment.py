"""Main entry point for the ATLAS-methodology-transfer smoke test.

Called by job_sbatch/sbatch-script.sh (that script cd's into this directory and
runs `python run_experiment.py` — do not move this file without updating it there).

Runs ONE SWE-bench Lite instance end to end:
  1. starts `transformers serve` in the background, serving the local model weights
     already downloaded on this machine (no OpenAI/OpenRouter calls -- this hits
     http://localhost:<PORT> only)
  2. waits for it to be ready
  3. pulls (if needed) and starts a Singularity instance for the chosen task
  4. runs the SWEBenchPilot use case against it via the wintermute CLI
  5. tears everything down

Edit the CONFIG block below for each run, or override via environment variables
of the same name (e.g. `TEST_CMD="..." python run_experiment.py`).
"""

import os
import subprocess
import time
import urllib.request

# ---------------------------------------------------------------------------
# CONFIG -- edit these per run (or set as env vars before launching)
# ---------------------------------------------------------------------------

HERE = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(HERE, "src")

# Matches the identifier `huggingface-cli scan-cache` shows for the local weights --
# transformers serve resolves models by this string against the local HF cache.
MODEL = os.environ.get("MODEL", "openai/gpt-oss-20b")

# Deliberately small. gpt-oss runs with "eager" attention here, which materializes a
# full N x N logits tensor per head, and three copies of it are alive at once during
# prefill. On the 44.5 GiB GPU (with ~13 GB of MXFP4 weights) a prompt of ~8.6k tokens
# already needs an 8.8 GiB tensor and OOMs (seen at turn 20 of the first real run).
# Raise this only after switching attention implementation or moving to a bigger GPU.
CONTEXT_SIZE = os.environ.get("CONTEXT_SIZE", "6000")
PORT = os.environ.get("PORT", "8000")

SERVE_CMD = ["transformers", "serve", "--port", PORT]

IMAGE = os.environ["IMAGE"]  # e.g. "docker://swebench/sweb.eval.x86_64.<instance_id>"
INSTANCE_NAME = os.environ.get("INSTANCE_NAME", f"swe_{os.environ.get('SLURM_JOB_ID', 'local')}")
SIF_CACHE = os.environ.get("SIF_CACHE", os.path.join(HERE, ".sif_cache"))
REPO_PATH = os.environ.get("REPO_PATH", "/testbed")
TEST_CMD = os.environ["TEST_CMD"]
ISSUE_TEXT = os.environ["ISSUE_TEXT"]
MAX_TURNS = os.environ.get("MAX_TURNS", "20")

LOG_DIR = os.path.join(HERE, "job_logs")
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(SIF_CACHE, exist_ok=True)
SIF_PATH = os.path.join(SIF_CACHE, f"{INSTANCE_NAME}.sif")

SINGULARITY_BIN = os.environ.get("SINGULARITY_BIN", "singularity")

# `transformers[serving]` and hackingBuddyGPT's copied capability.py need
# incompatible `openai` package versions -- they cannot share one venv. This
# script itself runs under the gptoss venv (for `transformers serve`), but
# wintermute.py must run under a *separate* venv where SE-task/requirements.txt
# is installed. See ~/venv/atlas-hbgpt setup instructions.
WINTERMUTE_PYTHON = os.environ.get(
    "WINTERMUTE_PYTHON", os.path.expanduser("~/venv/atlas-hbgpt/bin/python")
)

# Home quota is tight (50GB, shared with hf_cache/venv/etc.) and no scratch space
# is available -- default to never keeping more than one instance's image around.
# Set KEEP_SIF=1 to skip cleanup (e.g. while iterating on the same instance) if
# you've confirmed you have headroom.
KEEP_SIF = os.environ.get("KEEP_SIF", "0") == "1"


def start_llm_server():
    log_path = os.path.join(LOG_DIR, f"transformers_serve_{INSTANCE_NAME}.log")
    log_file = open(log_path, "w")
    print(f"Starting: {' '.join(SERVE_CMD)}  (log: {log_path})")
    # expandable_segments: the OOM message itself reported ~6.8 GiB reserved-but-unallocated
    # (fragmentation) at the moment of failure.
    env = dict(os.environ, PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True")
    proc = subprocess.Popen(SERVE_CMD, stdout=log_file, stderr=subprocess.STDOUT, env=env)
    return proc, log_file


def wait_for_server(timeout_s=300, interval_s=5):
    url = f"http://localhost:{PORT}/v1/models"
    print(f"Waiting for {url} ...")
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=5) as resp:
                if resp.status == 200:
                    print("Server is up.")
                    return
        except Exception:
            pass
        time.sleep(interval_s)
    raise RuntimeError(f"transformers serve did not respond at {url} after {timeout_s}s")


def prepare_container():
    if not os.path.exists(SIF_PATH):
        print(f"Pulling {IMAGE} -> {SIF_PATH}")
        # --disable-cache: don't retain OCI blobs under ~/.singularity/cache after
        # conversion -- with a 50GB home quota and no scratch space, that cache
        # accumulating across pulls is what caused the earlier "disk quota exceeded".
        subprocess.run([SINGULARITY_BIN, "pull", "--disable-cache", SIF_PATH, IMAGE], check=True)
    print(f"Starting instance {INSTANCE_NAME}")
    subprocess.run([SINGULARITY_BIN, "instance", "start", SIF_PATH, INSTANCE_NAME], check=True)


def run_pilot_task():
    db_path = os.path.join(LOG_DIR, f"swe_pilot_{INSTANCE_NAME}.sqlite3")
    cmd = [
        WINTERMUTE_PYTHON, "-m", "hackingBuddyGPT.cli.wintermute", "SWEBenchPilot",
        f"--conn.image={SIF_PATH}",
        f"--conn.instance_name={INSTANCE_NAME}",
        f"--conn.binary={SINGULARITY_BIN}",
        f"--repo_path={REPO_PATH}",
        f"--test_cmd={TEST_CMD}",
        f"--issue_text={ISSUE_TEXT}",
        f"--llm.model={MODEL}",
        f"--llm.context_size={CONTEXT_SIZE}",
        f"--llm.api_url=http://localhost:{PORT}",
        "--llm.api_key=dummy",
        # NOTE: deliberately not passing --llm.thinking here. configurable.py casts
        # bool parameters via Python's bool(value), so bool("false") == True -- the
        # only way to get the correct False is to omit the flag and let the actual
        # Python bool default (False) flow through untouched.
        f"--max_turns={MAX_TURNS}",
        f"--log_db.connection_string={db_path}",
    ]
    env = dict(os.environ)
    env["PYTHONPATH"] = SRC_DIR + os.pathsep + env.get("PYTHONPATH", "")
    print("Running:", " ".join(cmd))
    subprocess.run(cmd, check=True, env=env)
    print(f"Done. DB: {db_path}")


def cleanup(server_proc, server_log_file):
    print("Cleaning up...")
    try:
        subprocess.run([SINGULARITY_BIN, "instance", "stop", INSTANCE_NAME], check=False)
    except Exception as e:
        print(f"  (instance stop failed: {e})")

    if not KEEP_SIF:
        if os.path.exists(SIF_PATH):
            print(f"Removing {SIF_PATH} (set KEEP_SIF=1 to keep it)")
            os.remove(SIF_PATH)
        subprocess.run([SINGULARITY_BIN, "cache", "clean", "-f"], check=False)

    if server_proc is not None:
        server_proc.terminate()
        try:
            server_proc.wait(timeout=15)
        except subprocess.TimeoutExpired:
            server_proc.kill()
    if server_log_file is not None:
        server_log_file.close()


def main():
    server_proc, server_log_file = None, None
    try:
        server_proc, server_log_file = start_llm_server()
        wait_for_server()
        prepare_container()
        run_pilot_task()
    finally:
        cleanup(server_proc, server_log_file)


if __name__ == "__main__":
    main()
