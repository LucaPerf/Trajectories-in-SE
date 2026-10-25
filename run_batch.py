import os
import json
import subprocess
import sys

import requests

# Dataset indices (SWE-bench Lite) to run, in order, one after another.
INSTANCES = [35, 101]
#INSTANCES = [113]

RUNS_PER_INSTANCE = 40
MAX_TURNS = 40

HERE = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(HERE, "job_logs")
SUMMARY_FILE = os.path.join(LOG_DIR, "last_summary.json")


def send_telegram(text: str) -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID not set, skipping notification.")
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data={"chat_id": chat_id, "text": text},
            timeout=10,
        )
    except requests.RequestException as e:
        print(f"Could not send Telegram notification: {e}")

def run_all():
    total = len(INSTANCES)
    print(f"{total} instances to run.")

    results = []
    for n, index in enumerate(INSTANCES, 1):
        print(f"\n########## Instance {n}/{total}: index {index} ##########")
        cmd = [
            sys.executable, os.path.join(HERE, "main.py"),
            "--index", str(index),
            "--runs", str(RUNS_PER_INSTANCE),
            "--max-turns", str(MAX_TURNS),
        ]
        result = subprocess.run(cmd)
        status = "ok" if result.returncode == 0 else f"crashed (exit {result.returncode})"

        successes, completed = 0, 0
        try:
            with open(SUMMARY_FILE) as f:
                data = json.load(f)
            successes, completed = data["successes"], data["completed"]
        except (OSError, ValueError, KeyError):
            pass

        results.append((index, status))
        print(f"--- index {index}: {status} ---")
        send_telegram(
            f"Run {n}/{total} finished: index {index} ({status}) - "
            f"{successes} successful out of {completed} completed run(s).")

    n_crashed = sum(1 for _, s in results if s != "ok")
    summary = "\n".join(f"index {index}: {status}" for index, status in results)
    print("\n=== Batch summary ===")
    print(summary)

    send_telegram(f"ALL RUNS FINISHED ({total} instances, {n_crashed} crashed)")


import traceback

if __name__ == "__main__":
    try:
        run_all()
    except KeyboardInterrupt:
        send_telegram("Batch manually interrupted")
        raise
    except Exception:
        err = traceback.format_exc()
        send_telegram(f"The batch stopped because of an error:\n{err[-1500:]}")
        raise
