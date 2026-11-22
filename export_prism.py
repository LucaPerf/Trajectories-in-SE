"""Export the learned Markov chains to PRISM, to compute properties such as the probability of success.

    python export_prism.py
    prism prism/vm_7.pm prism/properties.pctl

For every instance in INSTANCES it reads artifacts/<instance>/<variant>/hb_mc.dot and writes into prism/:

  <instance>.pm          the chain as a PRISM DTMC, one comment per state with its label
  <instance>_states.txt  state number -> label, to read PRISM's results
  properties.pctl        the questions asked to every chain (shared)

Two changes are needed for PRISM to accept the chains, both on the numbers only:
- the probabilities in the .dot are rounded to 2 decimals, so the ones leaving a state do not always sum
  to 1: they are rescaled so that they do;
- the final states (__success, __fail) have no outgoing transition: they get a self-loop with probability 1.
"""

from pathlib import Path

HERE = Path(__file__).resolve().parent
VARIANT = "template_values"
INSTANCES = ["vm_7", "vm_11", "vm_27", "vm_70", "vm_113"]

PROPERTIES = """
P=? [ F "success" ]
P=? [ F "fail" ]
P=? [ F<=10 "success" ]
P=? [ F<=20 "success" ]
P=? [ F<=40 "success" ]
R{"steps"}=? [ F "end" ]
"""


def read_chain(dot_path: Path):
    from networkx.drawing.nx_pydot import read_dot

    graph = read_dot(str(dot_path))

    def label(node) -> str:
        return str(graph.nodes[node].get("label", node)).strip('"')

    # "__start0" is only the arrow AALpy draws to mark the initial state
    nodes = [node for node in graph.nodes if not str(node).startswith("__start")]
    index = {node: i for i, node in enumerate(nodes)}
    transitions = {}
    for node in nodes:
        row = {}
        for _, target, data in graph.out_edges(node, data=True):
            try:
                probability = float(str(data.get("label", "")).strip('"'))
            except ValueError:
                continue
            if target in index and probability > 0:
                row[index[target]] = row.get(index[target], 0.0) + probability
        total = sum(row.values())
        transitions[index[node]] = {t: p / total for t, p in row.items()} if row else {index[node]: 1.0}
    labels = [label(node) for node in nodes]
    return labels, transitions


def to_prism(labels: list[str], transitions: dict) -> str:
    start = labels.index("init")
    success = [i for i, text in enumerate(labels) if "__success" in text]
    fail = [i for i, text in enumerate(labels) if "__fail" in text]

    def states(numbers: list[int]) -> str:
        return " | ".join(f"s={i}" for i in numbers) or "false"

    lines = ["dtmc", "", "module chain", f"  s : [0..{len(labels) - 1}] init {start};"]
    for i, text in enumerate(labels):
        # full precision: rounding each probability (e.g. to 12 decimals) makes the sum miss 1 by more
        # than PRISM accepts
        update = " + ".join(f"{p!r}:(s'={t})" for t, p in sorted(transitions[i].items()))
        lines.append(f"  // {text}")
        lines.append(f"  [] s={i} -> {update};")
    lines += [
        "endmodule",
        "",
        f'label "success" = {states(success)};',
        f'label "fail" = {states(fail)};',
        f'label "end" = {states(success + fail)};',
        "",
        'rewards "steps"',
        "  true : 1;",
        "endrewards",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    out_dir = HERE / "prism"
    out_dir.mkdir(exist_ok=True)
    (out_dir / "properties.pctl").write_text(PROPERTIES, encoding="utf-8")
    for instance in INSTANCES:
        labels, transitions = read_chain(HERE / "artifacts" / instance / VARIANT / "hb_mc.dot")
        (out_dir / f"{instance}.pm").write_text(to_prism(labels, transitions), encoding="utf-8")
        (out_dir / f"{instance}_states.txt").write_text(
            "\n".join(f"{i}\t{text}" for i, text in enumerate(labels)) + "\n", encoding="utf-8"
        )
        finals = sum(1 for text in labels if "__success" in text or "__fail" in text)
        print(f"{instance}: {len(labels)} states, {finals} final -> prism/{instance}.pm")
    print("Wrote prism/properties.pctl")


if __name__ == "__main__":
    main()
