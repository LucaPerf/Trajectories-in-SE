"""Read-only look at a run database produced by main.py (opened with mode=ro, nothing is written).

    python inspect_runs.py job_logs\\astropy__astropy-12907.sqlite3
    python inspect_runs.py job_logs\\astropy__astropy-12907.sqlite3 --run 2 --width 400
"""

import argparse
import sqlite3
from pathlib import Path


def short(text, width):
    text = (text or "").replace("\r", "").replace("\n", " | ").strip()
    return text if len(text) <= width else text[:width] + f"... [{len(text)} chars]"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("db")
    parser.add_argument("--run", type=int, default=None, help="only this run id (default: all runs)")
    parser.add_argument("--width", type=int, default=160, help="max characters shown per text field")
    args = parser.parse_args()

    conn = sqlite3.connect(Path(args.db).resolve().as_uri() + "?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row

    print("== table sizes ==")
    for table in ("runs", "sections", "messages", "tool_calls"):
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"{table:<11} {count} rows")

    print("\n== runs ==")
    runs = conn.execute("SELECT id, model, state, tag, started_at, stopped_at FROM runs ORDER BY id").fetchall()
    for r in runs:
        print(f"run {r['id']}: state={r['state']!r} tag={r['tag']!r} model={r['model']!r} {r['started_at']} -> {r['stopped_at']}")

    for r in runs:
        if args.run is not None and r["id"] != args.run:
            continue
        print(f"\n== run {r['id']} ({r['state']}) ==")
        messages = conn.execute(
            "SELECT id, role, content, tokens_query, tokens_response FROM messages WHERE run_id = ? ORDER BY id", (r["id"],)
        ).fetchall()
        calls = {}
        for c in conn.execute(
            "SELECT message_id, function_name, arguments, state, result_text FROM tool_calls WHERE run_id = ? ORDER BY message_id",
            (r["id"],),
        ):
            calls.setdefault(c["message_id"], []).append(c)
        for m in messages:
            print(f"[msg {m['id']}] role={m['role']} tokens(query/response)={m['tokens_query']}/{m['tokens_response']}")
            print(f"    content: {short(m['content'], args.width)}")
            for c in calls.get(m["id"], []):
                print(f"    tool call: {c['function_name']} {short(c['arguments'], args.width)}")
                print(f"      result ({c['state']}): {short(c['result_text'], args.width)}")


if __name__ == "__main__":
    main()
