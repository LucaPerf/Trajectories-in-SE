"""Turn a run database into a readable .txt transcript (the database is opened read-only).

main.py calls write_transcript() after every run. To build one from an existing database:

    python transcript.py job_logs\\astropy__astropy-12907.sqlite3              # latest run
    python transcript.py job_logs\\astropy__astropy-12907.sqlite3 --run 1
    python transcript.py job_logs\\astropy__astropy-12907.sqlite3 --full-prompts

Files are written to the "output" folder next to this script.
"""

import argparse
import datetime
import re
import sqlite3
from pathlib import Path
from typing import Optional

HERE = Path(__file__).resolve().parent
DEFAULT_OUT_DIR = HERE / "output"

RULE = "=" * 78
THIN = "-" * 78

LEGEND = """HOW TO READ THIS FILE
Each TURN is one round trip with the model:
  1. prompt   what we send: the task, the available commands and the history of the earlier commands
  2. reply    what the model answered, complete and unedited
  3. command  the single line we extracted from the reply and actually executed in the container
  4. result   what the container printed (this becomes part of the history in the next prompt)
The run ends with a status line: "got root" means the tests passed (that is the framework's name for
any success), anything else is the reason the run stopped."""

# The prompt embeds the commands tried so far between "~~~ bash" and "~~~".
_HISTORY_RE = re.compile(r"You already tried the following commands:\s*~~~ bash\n(.*?)\n~~~", re.DOTALL)


def write_transcript(
    db_path,
    out_dir=DEFAULT_OUT_DIR,
    run_id: Optional[int] = None,
    full_prompts: bool = False,
) -> Optional[Path]:
    """Write the transcript of one run (default: the latest) and return the file path, or None."""
    try:
        conn = sqlite3.connect(Path(db_path).resolve().as_uri() + "?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        if run_id is None:
            run_id = conn.execute("SELECT MAX(id) FROM runs").fetchone()[0]
        if run_id is None:
            return None
        run = conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
        messages = conn.execute(
            "SELECT id, role, content, tokens_query, tokens_response FROM messages WHERE run_id = ? ORDER BY id",
            (run_id,),
        ).fetchall()
        calls = {}
        for c in conn.execute(
            "SELECT message_id, function_name, arguments, result_text FROM tool_calls WHERE run_id = ? ORDER BY message_id",
            (run_id,),
        ):
            calls.setdefault(c["message_id"], []).append(c)
    except sqlite3.Error as e:
        print(f"Could not read {db_path} for the transcript: {e}")
        return None
    if run is None:
        return None

    body = []
    turns = 0
    prompt = None
    for m in messages:
        if m["role"] == "assistant":
            turns += 1
            body += [THIN, f"TURN {turns}", THIN, ""]
            if prompt is not None:
                if full_prompts or turns == 1:
                    body += [f"[prompt sent to the model, {len(prompt)} characters]", prompt, ""]
                else:
                    history = _HISTORY_RE.search(prompt)
                    body += [
                        f"[prompt sent to the model: {len(prompt)} characters, the same as turn 1 plus the history below]",
                        history.group(1) if history else "(no history section found)",
                        "",
                    ]
            body += [
                f"[model reply, complete and unedited] ({m['tokens_query']} tokens in, {m['tokens_response']} tokens out)",
                m["content"] or "(empty reply)",
                "",
            ]
            reply_calls = calls.get(m["id"], [])
            if not reply_calls:
                body += ["[no command was executed for this reply]", ""]
            for c in reply_calls:
                body += [
                    f"[command executed: {c['function_name'] or '?'}]",
                    c["arguments"] or "",
                    "",
                    "[result]",
                    c["result_text"] or "(no output)",
                    "",
                ]
        elif m["role"] == "status":
            body += [THIN, f"STATUS: {m['content']}", ""]
        else:
            prompt = m["content"]

    header = [
        RULE,
        f"Run transcript: {Path(db_path).stem}",
        f"run id: {run['id']}    tag: {run['tag']!r}    turns: {turns}",
        f"model: {run['model']}",
        f"final state: {run['state']}",
        f"started: {run['started_at']}    stopped: {run['stopped_at']}  (start is local time, stop is UTC)",
        RULE,
        "",
        LEGEND,
        "",
    ]

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    out_path = out_dir / f"{Path(db_path).stem}__run{run_id}__{stamp}.txt"
    out_path.write_text("\n".join(header + body), encoding="utf-8", newline="\n")
    return out_path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("db")
    parser.add_argument("--run", type=int, default=None, help="run id (default: the latest run)")
    parser.add_argument("--full-prompts", action="store_true", help="print the full prompt of every turn")
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    args = parser.parse_args()

    path = write_transcript(args.db, args.out_dir, args.run, args.full_prompts)
    print(f"Transcript written to {path}" if path else "Nothing to write (no such run).")


if __name__ == "__main__":
    main()
