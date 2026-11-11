"""Write the static hints passed to main.py --hints-file, from the Markov chain of a similar instance (no LLM).

    python make_hints.py

For every pair in PAIRS it finds the most probable path in artifacts/<source>/<variant>/hb_mc.dot from
"init" to a successful state with a real action (the empty ",__success" state of runs whose steps were lost
is not a target), and writes the actions along that path, in order, into hints/<target>_from_<source>.txt.

Two rules on top of the Markov chain:
- the path must go through at least one command that edits a file (EDIT_ACTION), since a fix needs one;
- "submit_patch [...]" is written as plain "submit_patch": the bracket describes the fix of the source issue.
"""

import math
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
VARIANT = "template_values"

# (instance that gets the hints, instance whose Markov chain gives them)
PAIRS = [
    ("16820", "vm_113"),  # squashmigrations / index_together  <-  migration optimizer (django-16595)
    ("16408", "vm_70"),   # db/models  <-  db/models/fields (django-14238)
]

# sed -i, or a script/expression placeholder whose value says it changes code (apply fix, edit source file, ...)
EDIT_ACTION = re.compile(r"sed -i|\[(SCRIPT|EXPR|EXPRESSION):[^\]]*(fix|edit|patch|modif|substitut)", re.IGNORECASE)

INTRO = (
    "In earlier successful runs on a similar issue, the agent followed this sequence of commands "
    "(a value in square brackets stands for something you choose for this issue):"
)


def most_probable_success_path(dot_path: Path) -> list[str]:
    import networkx as nx
    from networkx.drawing.nx_pydot import read_dot

    graph = read_dot(str(dot_path))

    def label(node) -> str:
        return str(graph.nodes[node].get("label", node)).strip('"')

    def action(node) -> str:
        return label(node).rsplit(",", 1)[0].strip() if "," in label(node) else ""

    # most probable path = shortest path with weight -log(probability)
    weighted = nx.DiGraph()
    for source, target, data in graph.edges(data=True):
        # the "__start0 -> q0" arrow that AALpy adds to mark the initial state has no probability
        try:
            probability = float(str(data.get("label", "")).strip('"'))
        except ValueError:
            continue
        if probability > 0:
            weighted.add_edge(source, target, weight=-math.log(probability))

    start = next(node for node in graph.nodes if label(node) == "init")
    targets = {node for node in graph.nodes if "__success" in label(node) and action(node)}
    edits = [node for node in graph.nodes if EDIT_ACTION.search(action(node))]
    to_edit, path_to_edit = nx.single_source_dijkstra(weighted, start)

    # best path init -> edit -> success: the two halves are each the most probable one
    best_cost, best_path = math.inf, None
    for edit in edits:
        if edit not in to_edit:
            continue
        to_target, path_to_target = nx.single_source_dijkstra(weighted, edit)
        for target in targets & to_target.keys():
            cost = to_edit[edit] + to_target[target]
            if cost < best_cost:
                best_cost, best_path = cost, path_to_edit[edit] + path_to_target[target][1:]
    if best_path is None:
        raise SystemExit(f"{dot_path}: no path from init through an edit to a successful state")
    return [action(node) for node in best_path[1:]]


def main() -> None:
    out_dir = HERE / "hints"
    out_dir.mkdir(exist_ok=True)
    for target, source in PAIRS:
        steps = most_probable_success_path(HERE / "artifacts" / source / VARIANT / "hb_mc.dot")
        steps = ["submit_patch" if step.startswith("submit_patch") else step for step in steps]
        # one line joined by arrows, not a numbered list: in ATLAS numbered lists made small models
        # repeat every step in a single reply (see extract_common_path in knowledge_extraction.py)
        text = INTRO + "\n" + " -> ".join(steps) + "\n"
        path = out_dir / f"{target}_from_{source}.txt"
        path.write_text(text, encoding="utf-8")
        print(f"=== {path.name} ===\n{text}")


if __name__ == "__main__":
    main()
