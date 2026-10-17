"""Run main.py for a list of SWE-bench dataset indices, one after another (never two at once).

"""

import os
import subprocess
import sys

import requests

# Dataset indices (SWE-bench Lite) to run, in order, one after another.
INSTANCES = [7, 11, 21, 25]

RUNS_PER_INSTANCE = 40
MAX_TURNS = 100

HERE = os.path.dirname(os.path.abspath(__file__))


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


def main():
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
        results.append((index, status))
        print(f"--- index {index}: {status} ---")
        send_telegram(f"Run {n}/{total} finished: index {index} ({status})")

    n_crashed = sum(1 for _, s in results if s != "ok")
    summary = "\n".join(f"index {index}: {status}" for index, status in results)
    print("\n=== Batch summary ===")
    print(summary)

    send_telegram(f"ALL RUNS FINISHED ({total} instances, {n_crashed} crashed)")


if __name__ == "__main__":
    main()
