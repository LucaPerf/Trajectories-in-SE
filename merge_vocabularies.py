"""Merge the traces of all instances under one shared vocabulary, without any LLM.

    python merge_vocabularies.py [--variant template_values]
    python learn.py learn --out artifacts/merged/template_values

Reads artifacts/vm_*/<variant>/abstractions.json (nothing there is changed), rewrites every label with
the fixed rules below and writes artifacts/merged/<variant>/:

  abstractions.json     all traces with the shared labels, in the format read by `learn.py learn`
  vocabulary_map.txt    every shared label with the original labels it replaces, to check the rules by hand
"""

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent

PLACEHOLDER = re.compile(r"\[([A-Z_]+):\s*([^\]]*)\]")
OUTPUT_LABEL = re.compile(r"(EMPTY|ERROR|INFO|DISCOVERY|PROGRESS|REPEATED)_[A-Z]+")
OUTPUT_AS_ACTION = re.compile(r"[A-Z]+_[A-Z_]+")
AFTER_NAME_FLAG = re.compile(r"(-name|-path|--include)[= ]$")

UNKNOWN_ACTION = "UNKNOWN_ACTION"
UNKNOWN_OUTPUT = "UNKNOWN_OUTPUT"


def has(value: str, *words: str) -> bool:
    return any(word in value for word in words)


def path_class(value: str) -> str:
    if has(value, "runner"):
        return "[FILE: test runner]"
    if has(value, "temporary", "patch script"):
        return "[FILE: temporary file]"
    if has(value, "root", "repository"):
        return "[DIR: repository]"
    if has(value, "directory", "package", "tree"):
        return "[DIR: test directory]" if "test" in value else "[DIR: source directory]"
    return "[FILE: test file]" if "test" in value else "[FILE: source file]"


def script_class(value: str) -> str:
    if has(value, "runner"):
        return "[FILE: test runner]"
    if has(value, "inspect", "analysis", "environment", "configure"):
        return "[SCRIPT: inspect]"
    if has(value, "test", "reproduce"):
        return "[SCRIPT: run]"
    return "[SCRIPT: edit]"


def glob_class(value: str, flag: str) -> str:
    if flag == "-path":
        return "[GLOB: path]"
    if "test" in value:
        return "[GLOB: test files]"
    return "[GLOB: python files]" if "python" in value else "[GLOB: file name]"


def shared_placeholder(match: re.Match, unknown: Counter) -> str:
    name, value = match.group(1), match.group(2).lower()
    flag = AFTER_NAME_FLAG.search(match.string[: match.start()])

    # the flag decides first: -name and --include take a file pattern, whatever name the model gave it
    if name == "GLOB" or flag:
        return glob_class(value, flag.group(1) if flag else "")
    if name in ("MESSAGE", "STRING"):
        return "[TEXT]"
    if has(value, "found", "find", "replacement", "placeholder", "current file"):
        return "[FOUND]"
    if name in ("FILE", "PATH", "DIR"):
        return path_class(value)
    if name in ("SCRIPT", "EXPR", "EXPRESSION"):
        return script_class(value)
    if name in ("PATTERN", "TERM"):
        return "[PATTERN]"
    if name in ("TEST", "TESTS", "MODULE", "TARGET") or (name == "ARG" and "test" in value):
        return "[TEST: test module]"
    if name == "COUNT":
        return "[COUNT]"
    if name in ("RANGE", "SETTINGS"):
        return f"[{name}]"
    if name in ("MARKER", "DELIMITER"):
        return ""
    unknown[f"{name}: {value}"] += 1
    return f"[{name}]"


def shared_action(label: str, unknown: Counter) -> str:
    label = label.strip()
    if not label or OUTPUT_AS_ACTION.fullmatch(label):
        return UNKNOWN_ACTION
    label = label.removeprefix("exec_command ")
    if label.startswith("submit_patch"):
        return "submit_patch"

    label = re.sub(r"--include (?=\[)", "--include=", label)
    label = PLACEHOLDER.sub(lambda match: shared_placeholder(match, unknown), label)

    # differences that say nothing about the strategy: where the command runs, how much it prints
    label = label.replace("cd [DIR: repository] && ", "")
    label = re.sub(r" 2>(/dev/null|&1)", "", label)
    label = re.sub(r" (-v2|-v \[COUNT\]|--verbosity=\[COUNT\])(?=$| )", "", label)
    label = re.sub(r"\bpython3\b", "python", label)
    label = re.sub(r"\b(head|tail) (-n )?-?\[COUNT\]", r"\1 [COUNT]", label)
    label = re.sub(r"grep -r -n\b|grep -n -r\b", "grep -rn", label)
    label = re.sub(r"\s+;", ";", label)
    return " ".join(label.split())


def shared_output(label: str) -> str:
    label = label.strip().rstrip(")")
    return label if OUTPUT_LABEL.fullmatch(label) else UNKNOWN_OUTPUT


def vocabulary_report(summary: list[str], action_sources: dict, action_instances: dict, unknown: Counter) -> str:
    lines = summary[:]
    if unknown:
        lines += ["", "Placeholders without a rule (kept by name only):"]
        lines += [f"{count:>5}  {name}" for name, count in unknown.most_common()]
    for action, sources in sorted(action_sources.items(), key=lambda item: -sum(item[1].values())):
        lines += ["", f"[{sum(sources.values())} steps, {len(action_instances[action])} instances] {action}"]
        lines += [f"{count:>7}  {label}" for label, count in sources.most_common()]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--variant", default="template_values", help="abstraction folder to merge")
    args = parser.parse_args()

    paths = sorted((HERE / "artifacts").glob(f"vm_*/{args.variant}/abstractions.json"))
    if not paths:
        raise SystemExit(f"No artifacts/vm_*/{args.variant}/abstractions.json found.")

    traces, run_ids, skipped = [], [], []
    action_sources = defaultdict(Counter)
    action_instances = defaultdict(set)
    original_actions, original_outputs, output_labels, unknown = set(), set(), Counter(), Counter()

    for path in paths:
        instance = path.parent.parent.name
        data = json.loads(path.read_text(encoding="utf-8"))
        for run_id, trace in zip(data["run_ids"], data["traces"]):
            # a run whose steps were all lost would only add an empty path to the terminal state
            if not any(isinstance(value, list) for value in trace.values()):
                skipped.append(f"{instance}:{run_id}")
                continue
            rewritten = {}
            for index, value in trace.items():
                if not isinstance(value, list):
                    rewritten[index] = value
                    continue
                action, output = shared_action(value[0], unknown), shared_output(value[1])
                action_sources[action][value[0]] += 1
                action_instances[action].add(instance)
                original_actions.add(value[0])
                original_outputs.add(value[1])
                output_labels[output] += 1
                rewritten[index] = [action, output]
            traces.append(rewritten)
            run_ids.append(f"{instance}:{run_id}")

    instances = {path.parent.parent.name for path in paths}
    shared_by_all = sum(1 for seen in action_instances.values() if seen == instances)
    steps = sum(sum(sources.values()) for sources in action_sources.values())
    summary = [
        f"Instances: {', '.join(sorted(instances))}",
        f"{len(traces)} runs, {steps} steps; skipped {len(skipped)} run(s) without steps: {', '.join(skipped) or '-'}",
        f"Actions: {len(original_actions)} -> {len(action_sources)}, of which {shared_by_all} in all instances",
        f"Outputs: {len(original_outputs)} -> {len(output_labels)}",
        f"Steps with an action label that is not a command: {sum(action_sources.get(UNKNOWN_ACTION, Counter()).values())}",
        f"Steps with an invalid output label: {output_labels[UNKNOWN_OUTPUT]}",
    ]

    out_dir = HERE / "artifacts" / "merged" / args.variant
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "abstractions.json").write_text(
        json.dumps({"act_categories": sorted(action_sources), "out_categories": sorted(output_labels),
                    "traces": traces, "run_ids": run_ids,
                    "source": {"variant": args.variant, "instances": sorted(instances)}}, indent=2),
        encoding="utf-8",
    )
    report = vocabulary_report(summary, action_sources, action_instances, unknown)
    (out_dir / "vocabulary_map.txt").write_text(report, encoding="utf-8")
    print("\n".join(summary) + f"\n\nWrote {out_dir / 'abstractions.json'} and {out_dir / 'vocabulary_map.txt'}")


if __name__ == "__main__":
    main()
