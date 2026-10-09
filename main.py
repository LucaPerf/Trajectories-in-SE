"""Local main: runs one SWE-bench Lite instance through the SWEBenchPilot use case, once or several times.

The LLM is the hosted model on the university's Aqueduct server (API calls only, nothing
is downloaded for it). The task environment is a Docker container built from the
instance's official SWE-bench image.

Usage (venv active, Docker Desktop running, API key exported):
    $env:AQUEDUCT_API_KEY = "..."
    python main.py  # instance #0 of SWE-bench Lite, one run
    python main.py --index 5
    python main.py --id astropy__astropy-12907 --max-turns 30
    python main.py --runs 10 --max-turns 10   # ten independent runs in a row (fresh container each time)
"""

import argparse
import os
import shlex
import sqlite3
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# The three things to set
# ---------------------------------------------------------------------------
API_URL = "https://aqueduct.ai.datalab.tuwien.ac.at"  # the default path /v1/chat/completions is appended
MODEL = "deepseek-v4-vision-exp-284b"
API_KEY_ENV = "AQUEDUCT_API_KEY"  # name of the environment variable holding the key
# ---------------------------------------------------------------------------

DATASET = "SWE-bench/SWE-bench_Lite"

# Maximum length of each model reply (every API call has to send one; this is the framework's default).
# Cost and memory are not a concern on the hosted model: raise it if replies get cut off.
MAX_TOKENS = 16384

# SWE-bench images keep the project's Python environment in a conda env called "testbed"
# (checked inside the astropy image: /opt/miniconda3, env "testbed", Python 3.9).
SHELL_PREFIX = "source /opt/miniconda3/bin/activate && conda activate testbed"

HERE = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(HERE, "src")
LOG_DIR = os.path.join(HERE, "job_logs")


def image_ref(instance_id: str) -> str:
    # Official naming: instance_id "<repo>__<name>" -> swebench/sweb.eval.x86_64.<repo>_1776_<name>:latest
    repo_part, name_part = instance_id.split("__", 1)
    return f"swebench/sweb.eval.x86_64.{repo_part}_1776_{name_part}:latest"


def docker(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["docker", *args], capture_output=True, text=True)


def ensure_image(image: str) -> None:
    check = docker("image", "inspect", image)
    if check.returncode == 0:
        return
    if "error during connect" in check.stderr or "Cannot connect" in check.stderr:
        sys.exit("Docker engine is not reachable. Start Docker Desktop and wait for 'Engine running'.")
    print(f"Image {image} not found locally, pulling it (about 1 GB)...")
    if subprocess.run(["docker", "pull", image]).returncode != 0:
        sys.exit(f"docker pull {image} failed")


def load_instance(index: int, instance_id: str):
    from datasets import load_dataset

    ds = load_dataset(DATASET, split="test")
    if instance_id:
        for i, row in enumerate(ds):
            if row["instance_id"] == instance_id:
                return i, row
        sys.exit(f"instance_id '{instance_id}' not found in {DATASET}")
    return index, ds[index]


def build_test_cmd(instance) -> str:
    import json

    fail_to_pass = instance["FAIL_TO_PASS"]
    if isinstance(fail_to_pass, str):
        fail_to_pass = json.loads(fail_to_pass)
    tests = " ".join(shlex.quote(t) for t in fail_to_pass)
    return f"python -m pytest {tests} -rA"


def latest_run(db_path: str):
    """(run id, state) of the most recent run in the database, or None."""
    if not os.path.exists(db_path):
        return None
    try:
        conn = sqlite3.connect(Path(db_path).resolve().as_uri() + "?mode=ro", uri=True)
        row = conn.execute("SELECT id, state FROM runs ORDER BY id DESC LIMIT 1").fetchone()
        conn.close()
    except sqlite3.Error:
        return None
    return tuple(row) if row else None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--index", type=int, default=0)
    parser.add_argument("--id", type=str, default="")
    parser.add_argument("--runs", type=int, default=1, help="how many independent runs to do in a row")
    parser.add_argument("--max-turns", type=int, default=20)
    parser.add_argument("--keep-container", action="store_true", help="do not remove the container at the end")
    args = parser.parse_args()

    api_key = os.environ.get(API_KEY_ENV)
    if not api_key:
        sys.exit(f'Environment variable {API_KEY_ENV} is not set. In PowerShell: $env:{API_KEY_ENV} = "..."')

    index, instance = load_instance(args.index, args.id)
    instance_id = instance["instance_id"]
    # automata/trace_extraction.py only sees runs whose tag looks like vm_<n>[_iter_<m>] (a pentest
    # convention). Here "vm_<n>" stands for the SWE-bench instance with dataset index n.
    tag = f"vm_{index}_iter_0"
    image = image_ref(instance_id)
    container = f"swe_{instance_id}"
    print(f"Instance: {instance_id}\nImage:    {image}\nModel:    {MODEL} @ {API_URL}")

    ensure_image(image)

    os.makedirs(LOG_DIR, exist_ok=True)
    patch_path = os.path.join(LOG_DIR, f"{instance_id}.test.patch")
    with open(patch_path, "w", encoding="utf-8", newline="") as f:
        f.write(instance["test_patch"])
    db_path = os.path.join(LOG_DIR, f"{instance_id}.sqlite3")

    cmd = [
        sys.executable, "-m", "hackingBuddyGPT.cli.wintermute", "SWEBenchPilot",
        f"--conn.image={image}",
        f"--conn.container_name={container}",
        f"--conn.shell_prefix={SHELL_PREFIX}",
        "--conn.workdir=/testbed",
        "--repo_path=/testbed",
        f"--test_cmd={build_test_cmd(instance)}",
        f"--test_patch_file={patch_path}",
        f"--issue_text={instance['problem_statement']}",
        f"--llm.model={MODEL}",
        f"--llm.api_url={API_URL}",
        f"--llm.max_tokens={MAX_TOKENS}",
        f"--max_turns={args.max_turns}",
        f"--log_db.connection_string={db_path}",
        f"--log.tag={tag}",
    ]
    # The key travels through the environment (configurable.py reads "llm.api_key"), never the command line.
    env = dict(os.environ)
    env["PYTHONPATH"] = SRC_DIR + os.pathsep + env.get("PYTHONPATH", "")
    env["PYTHONUTF8"] = "1"
    env["llm.api_key"] = api_key

    from transcript import write_transcript

    outcomes = []
    crashed = False
    for i in range(1, args.runs + 1):
        print(f"\n=== Run {i} of {args.runs} ===")
        docker("rm", "-f", container)  # start from a clean container, never a leftover from an earlier run
        try:
            result = subprocess.run(cmd, env=env, check=False)
        finally:
            if not args.keep_container:
                docker("rm", "-f", container)
        if os.path.exists(db_path):
            transcript_path = write_transcript(db_path, os.path.join(HERE, "output"))
            if transcript_path:
                print(f"Readable transcript: {transcript_path}")
        if result.returncode != 0:
            # The agent process exits with 0 even when the task is not solved, so a non-zero code means
            # a crash (API or network problem, ...). Later runs would most likely fail the same way.
            print(f"The agent process crashed (exit code {result.returncode}), stopping the batch.")
            crashed = True
            break
        outcome = latest_run(db_path)
        if outcome:
            outcomes.append(outcome)

    print("\n=== Summary ===")
    for run_id, state in outcomes:
        print(f"run {run_id}: {'SUCCESS' if state == 'got root' else state}")
    successes = sum(1 for _, state in outcomes if state == "got root")
    print(f"{successes} successful out of {len(outcomes)} completed run(s). Database: {db_path}")
    if crashed:
        sys.exit(1)


if __name__ == "__main__":
    main()
