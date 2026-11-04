"""Phase 1, steps 2 and 3 of the ATLAS pipeline, on the runs collected by main.py.

Step 2, abstraction. Needs the Aqueduct model, so run it on the university network:

    python learn.py abstract --db job_logs\\astropy__astropy-12907.sqlite3 --tag vm_0_iter_0 --out artifacts\\vm_0

  Reads the runs from the database (read-only), asks the model to give every (command, result) pair an
  (action category, output category) label, and writes abstractions.json (input of step 3) plus
  abstractions.txt (the same thing in a form meant for humans).

Step 3, Alergia. Fully offline, can be repeated as often as you like with different --eps:

    python learn.py learn --out artifacts\\vm_0 [--eps 0.05]

  Learns a Markov chain from abstractions.json and writes hb_mc.dot plus model_summary.txt.
"""

import argparse
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "src"))

from main import API_KEY_ENV, API_URL, MAX_TOKENS, MODEL  # noqa: E402  (endpoint and model are set in main.py)


def short(text: str, width: int = 110) -> str:
    text = " ".join((text or "").split())
    return text if len(text) <= width else text[:width] + "..."


def executed_commands(interactions: list[dict], keep_empty: bool) -> tuple[list[dict], int]:
    """Replace the raw model reply by the command that was actually executed.

    The reply can contain extra text or several commands, while only the first command line runs.
    Interactions with an empty command (the model produced no usable reply) are dropped unless keep_empty.
    """
    kept, dropped = [], 0
    for interaction in interactions:
        # A blank "action" (the capability name from the tool call) means the parser did not
        # recognize the reply as exec_command/submit_patch -- nothing ran in the container,
        # even if "arguments" holds leaked reasoning text or stray tokens.
        action = (interaction.get("action") or "").strip()
        arguments = (interaction.get("arguments") or "").strip()
        if not action and not keep_empty:
            dropped += 1
            continue
        command = " ".join(part for part in (action, arguments) if part) or "(empty reply)"
        kept.append({**interaction, "output": command})
    return kept, dropped

def is_submit(interaction: dict) -> bool:
    return (interaction.get("action") or "").strip() == "submit_patch"


def fix_tool_groups(trace: dict, interactions: list[dict], act_exec: set, act_sub: set, run_id) -> int:
    """Make sure a submit_patch step gets a submit category and an exec_command step an exec category."""
    fixed = 0
    for idx, value in trace.items():
        if not isinstance(value, tuple) or idx >= len(interactions):
            continue
        allowed = act_sub if is_submit(interactions[idx]) else act_exec
        if not allowed or value[0] in allowed:
            continue
        if len(allowed) == 1:
            trace[idx] = (next(iter(allowed)), value[1])
            fixed += 1
        else:
            print(f"WARNING run {run_id} step {idx}: '{value[0]}' is outside the expected group")
    return fixed


def cmd_abstract(args) -> None:
    from hackingBuddyGPT.automata.abstraction import abstract_sequence, categorize_interactions, normalize_categories
    from hackingBuddyGPT.automata.trace_extraction import extract_sequences
    from hackingBuddyGPT.utils.db_storage.db_storage import RawDbStorage
    from hackingBuddyGPT.utils.openai.openai_llm import OpenAIConnection

    api_key = os.environ.get(API_KEY_ENV)
    if not api_key:
        sys.exit(f'Environment variable {API_KEY_ENV} is not set. In PowerShell: $env:{API_KEY_ENV} = "..."')

    db = RawDbStorage(connection_string=args.db)
    db.connect()
    parsed = RawDbStorage.parse_tag(args.tag) if args.tag else {}
    runs = extract_sequences(
        db, vm_id=parsed.get("vm_id"), iteration=parsed.get("iteration"), transfer=parsed.get("transfer")
    )

    # A run that ended with an exception is an infrastructure problem (API, network), not agent behaviour.
    states = {run.id: run.state for run in db.get_runs()}
    crashed = [run_id for run_id in runs if states.get(run_id) == "exception occurred"]
    for run_id in crashed:
        del runs[run_id]
    runs = {run_id: data for run_id, data in runs.items() if run_id >= args.min_run}
    if not runs:
        sys.exit("No usable runs found. Check --db and --tag (the tag looks like vm_0_iter_0).")


    prepared = {}
    total_dropped = 0
    for run_id, run_data in runs.items():
        interactions, dropped = executed_commands(run_data["interactions"], args.keep_empty)
        total_dropped += dropped
        prepared[run_id] = {"interactions": interactions, "success": run_data["success"]}
    print(
        f"{len(prepared)} runs ({sum(r['success'] for r in prepared.values())} successful), "
        f"{sum(len(r['interactions']) for r in prepared.values())} interactions; "
        f"skipped {len(crashed)} crashed run(s) and {total_dropped} empty interaction(s)."
    )

    out_dir = Path(args.out)
    if (out_dir / "abstractions.json").exists() and not args.force:
        sys.exit(f"{out_dir} contains already an abstractions.json: use another --out or --force")

    llm = OpenAIConnection(api_key=api_key, model=MODEL, api_url=API_URL, max_tokens=MAX_TOKENS, api_timeout=600)

    act_exec: set[str] = set()
    out_exec: set[str] = set()
    act_sub: set[str] = set()
    out_sub: set[str] = set()
    for run_data in prepared.values():
        exec_part = [i for i in run_data["interactions"] if not is_submit(i)]
        sub_part = [i for i in run_data["interactions"] if is_submit(i)]
        if exec_part:
            categorize_interactions(exec_part, act_exec, out_exec, llm)
        if sub_part:
            categorize_interactions(sub_part, act_sub, out_sub, llm)
    print(f"\nExec actions: {sorted(act_exec)}\nSubmit actions: {sorted(act_sub)}")
    print(f"Output categories: {sorted(out_exec | out_sub)}")

    # each tool is normalized on its own, so a submit step can never be merged with an exec step
    if act_exec or out_exec:
        act_exec, out_exec = normalize_categories(act_exec, out_exec, llm)
    if act_sub or out_sub:
        act_sub, out_sub = normalize_categories(act_sub, out_sub, llm)
    print(f"\nNormalized exec actions: {sorted(act_exec)}\nNormalized submit actions: {sorted(act_sub)}")
    print(f"Normalized output categories: {sorted(out_exec | out_sub)}")

    act_categories = act_exec | act_sub
    out_categories = out_exec | out_sub

    act_categories, out_categories = normalize_categories(act_categories, out_categories, llm)
    print(f"\nNormalized action categories: {sorted(act_categories)}")
    print(f"Normalized output categories: {sorted(out_categories)}")

    traces = []
    total_fixed = 0
    for run_id, run_data in prepared.items():
        print(f"\nAbstracting run {run_id} ({len(run_data['interactions'])} interactions)...")
        trace = abstract_sequence(
            run_data["interactions"], act_categories, out_categories, not run_data["success"], llm
        )
        total_fixed += fix_tool_groups(trace, run_data["interactions"], act_exec, act_sub, run_id)
        traces.append(trace)

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "vocabulary.json").write_text(
        json.dumps({"exec_actions": sorted(act_exec), "submit_actions": sorted(act_sub),
                    "outputs": sorted(out_categories)}, indent=2),
        encoding="utf-8",
    )
    abstractions_data = {
        "act_categories": sorted(act_categories),
        "out_categories": sorted(out_categories),
        "traces": traces,
        "run_ids": list(prepared),
        "source": {"db": args.db, "tag": args.tag},
    }
    (out_dir / "abstractions.json").write_text(json.dumps(abstractions_data, indent=2), encoding="utf-8")

    lines = []
    for (run_id, run_data), trace in zip(prepared.items(), traces):
        lines.append(f"=== run {run_id} ({'success' if run_data['success'] else 'failure'}) ===")
        for index, value in sorted(trace.items()):
            if isinstance(value, (tuple, list)):
                interactions = run_data["interactions"]
                command = interactions[index]["output"] if index < len(interactions) else "?"
                lines += [f"{index}: {short(command)}", f"      action: {value[0]}", f"      output: {value[1]}"]
            else:
                lines.append(f"{index}: <{value}>")
        lines.append("")
    (out_dir / "abstractions.txt").write_text("\n".join(lines), encoding="utf-8")
    print(f"\nWrote {out_dir / 'abstractions.json'} and {out_dir / 'abstractions.txt'}")


def describe_dot(dot_path: Path) -> str:
    """List every state of the learned Markov chain with its outgoing transitions and probabilities."""
    from networkx.drawing.nx_pydot import read_dot

    graph = read_dot(str(dot_path))

    def label(node) -> str:
        return str(graph.nodes[node].get("label", node)).strip('"')

    def probability(value) -> float:
        try:
            return float(str(value).strip('"'))
        except ValueError:
            return 0.0

    lines = [f"{graph.number_of_nodes()} states, {graph.number_of_edges()} transitions", ""]
    for node in graph.nodes:
        lines.append(f"[{node}] {label(node)}")
        edges = [(target, probability(data.get("label", ""))) for _, target, data in graph.out_edges(node, data=True)]
        for target, prob in sorted(edges, key=lambda e: -e[1]):
            lines.append(f"      {prob:.2f} -> [{target}] {label(target)}")
    return "\n".join(lines)


def pair_frequencies(abstractions: dict) -> str:
    """Count how often every (action, output) pair occurs in the traces, and in how many runs."""
    from collections import Counter

    occurrences, runs = Counter(), Counter()
    for trace in abstractions["traces"]:
        pairs = [tuple(value) for value in trace.values() if isinstance(value, list)]
        occurrences.update(pairs)
        runs.update(set(pairs))

    distinct = max(len(occurrences), 1)
    lines = [
        f"{sum(occurrences.values())} interactions in {len(abstractions['traces'])} runs, "
        f"{len({action for action, _ in occurrences})} distinct actions, "
        f"{len(occurrences)} distinct (action, output) pairs"
    ]
    for limit in (1, 2, 5):
        n = sum(1 for count in occurrences.values() if count <= limit)
        lines.append(f"pairs seen at most {limit} time(s): {n} ({100 * n / distinct:.0f}%)")
    lines += ["", f"{'count':>5} {'runs':>4}  action -> output"]
    for (action, output), count in occurrences.most_common():
        lines.append(f"{count:>5} {runs[(action, output)]:>4}  {action} -> {output}")
    return "\n".join(lines)


def cmd_learn(args) -> None:
    from hackingBuddyGPT.automata.automaton_learning import learn_and_save

    out_dir = Path(args.out)
    abstractions_path = out_dir / "abstractions.json"
    if not abstractions_path.exists():
        sys.exit(f"{abstractions_path} not found: run the 'abstract' step first.")
    dot_path = out_dir / "hb_mc.dot"
    learn_and_save(str(abstractions_path), str(dot_path), "mc", args.eps)

    summary = describe_dot(dot_path)
    (out_dir / "model_summary.txt").write_text(summary, encoding="utf-8")
    print(f"\n{summary}\n\nWrote {dot_path} and {out_dir / 'model_summary.txt'}")

    frequencies = pair_frequencies(json.loads(abstractions_path.read_text(encoding="utf-8")))
    (out_dir / "pair_frequencies.txt").write_text(frequencies, encoding="utf-8")
    print("\n" + "\n".join(frequencies.splitlines()[:4]) + f"\n\nWrote {out_dir / 'pair_frequencies.txt'}")


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    abstract = sub.add_parser("abstract", help="step 2: label every interaction (needs the model)")
    abstract.add_argument("--db", required=True, help="run database written by main.py")
    abstract.add_argument("--tag", default="", help="only runs with this tag, e.g. vm_0_iter_0")
    abstract.add_argument("--min-run", type=int, default=0, help="ignore runs with an id below this (e.g. earlier runs with other settings)")
    abstract.add_argument("--out", required=True, help="output folder, e.g. artifacts\\vm_0")
    abstract.add_argument("--keep-empty", action="store_true", help="keep interactions where the model sent no command")
    abstract.add_argument("--force", action="store_true", help="overwrite an existing abstractions.json in --out")
    abstract.set_defaults(func=cmd_abstract)

    learn = sub.add_parser("learn", help="step 3: learn the automaton with Alergia (offline)")
    learn.add_argument("--out", required=True, help="folder that contains abstractions.json")
    learn.add_argument("--eps", type=float, default=0.05, help="Alergia threshold: lower gives a larger, more precise model")
    learn.set_defaults(func=cmd_learn)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
