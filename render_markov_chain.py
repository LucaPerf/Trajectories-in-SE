#!/usr/bin/env python3
"""Render a learned Markov chain DOT file (e.g. hb_mc.dot) to a PDF.

Pure-Python renderer (networkx + matplotlib) — does not require the
Graphviz `dot` binary to be installed. Layout quality is lower than
Graphviz's own, but this works anywhere the project's venv is set up.

Usage:
    python scripts/render_markov_chain.py <input.dot> [output.pdf]

If output.pdf is omitted, the PDF is written next to the input file
with the same basename (e.g. hb_mc.dot -> hb_mc.pdf).

Examples:
    python scripts/render_markov_chain.py experiments/vm1/artifacts/vm_1/iteration_0/hb_mc.dot
    python scripts/render_markov_chain.py SE-task/artifacts/vm_0/hb_mc.dot SE-task/artifacts/vm_0/hb_mc.pdf
"""

import argparse
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import networkx as nx
import pydot


def render(dot_path: str, pdf_path: str, figsize=(22, 16), dpi=200) -> None:
    (graph,) = pydot.graph_from_dot_file(dot_path)
    G = nx.drawing.nx_pydot.from_pydot(graph)

    # The AALpy/automata exporter adds a synthetic __start0 marker node
    # pointing at the real initial state; drop it but remember the target
    # so the real initial state can be highlighted instead.
    start_node = None
    for u, v in list(G.edges()):
        if u == "__start0":
            start_node = v
    if "__start0" in G.nodes():
        G.remove_node("__start0")

    labels = {n: (d.get("label", n) or n).strip('"') for n, d in G.nodes(data=True)}

    pos = nx.kamada_kawai_layout(G)

    fig, ax = plt.subplots(figsize=figsize)

    nx.draw_networkx_nodes(
        G, pos, ax=ax, node_size=2600, node_color="#cfe3ff",
        edgecolors="#2b5fa5", linewidths=1.3,
    )
    if start_node:
        nx.draw_networkx_nodes(
            G, pos, ax=ax, nodelist=[start_node], node_size=2800,
            node_color="#b8f2c9", edgecolors="#1f7a3d", linewidths=2.0,
        )

    nx.draw_networkx_labels(G, pos, labels=labels, ax=ax, font_size=6.5)

    self_loops = [(u, v) for u, v in G.edges() if u == v]
    normal_edges = [(u, v) for u, v in G.edges() if u != v]

    nx.draw_networkx_edges(
        G, pos, ax=ax, edgelist=normal_edges, connectionstyle="arc3,rad=0.12",
        arrowsize=14, width=1.1, edge_color="#555555", node_size=2600,
    )
    nx.draw_networkx_edges(
        G, pos, ax=ax, edgelist=self_loops, connectionstyle="arc3,rad=0.6",
        arrowsize=14, width=1.1, edge_color="#a55", node_size=2600,
    )

    edge_labels = {}
    for u, v, d in G.edges(data=True):
        lbl = d.get("label", "")
        if isinstance(lbl, str):
            lbl = lbl.strip('"')
        edge_labels[(u, v)] = lbl

    nx.draw_networkx_edge_labels(
        G, pos, edge_labels=edge_labels, ax=ax, font_size=6, font_color="#333333",
        bbox=dict(boxstyle="round,pad=0.1", fc="white", ec="none", alpha=0.7),
    )

    ax.set_title(f"Learned Markov Chain: {dot_path}", fontsize=14)
    ax.axis("off")
    fig.tight_layout()

    with PdfPages(pdf_path) as pp:
        pp.savefig(fig, dpi=dpi)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dot_path", help="Path to the input .dot file")
    parser.add_argument("pdf_path", nargs="?", default=None,
                         help="Path to the output .pdf file (default: same name as input, .pdf extension)")
    args = parser.parse_args()

    pdf_path = args.pdf_path or os.path.splitext(args.dot_path)[0] + ".pdf"
    render(args.dot_path, pdf_path)
    print(f"wrote {pdf_path}")


if __name__ == "__main__":
    sys.exit(main())
