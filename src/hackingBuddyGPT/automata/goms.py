import re
import argparse
from collections import defaultdict

import networkx as nx
from networkx.drawing.nx_pydot import read_dot, write_dot


class GOMS:

    def __init__(self, graph):
        self.G = graph

    # ---------------------------------------------------------
    # Utilities
    # ---------------------------------------------------------

    def node_label(self, node):
        return str(self.G.nodes[node].get("label", node)).strip('"')

    def find_nodes_by_regex(self, regex):
        r = re.compile(regex, re.IGNORECASE)
        return [n for n in self.G.nodes if r.search(self.node_label(n))]

    # ---------------------------------------------------------
    # Reachability
    # ---------------------------------------------------------

    def forward_reachable(self, start):

        visited = set()
        stack = [start]

        while stack:
            n = stack.pop()

            if n in visited:
                continue

            visited.add(n)

            for succ in self.G.successors(n):
                stack.append(succ)

        return visited

    def reverse_reachable(self, targets):

        RG = self.G.reverse(copy=False)

        visited = set()
        stack = list(targets)

        while stack:
            n = stack.pop()

            if n in visited:
                continue

            visited.add(n)

            for pred in RG.neighbors(n):
                stack.append(pred)

        return visited

    def find_initial_states(self):
        """
        DOT files often encode starts as:

            __start0 -> q0

        If not found, fall back to nodes with indegree 0.
        """

        initials = []

        for n in self.G.nodes:

            if str(n).startswith("__start"):
                initials.extend(list(self.G.successors(n)))

        if initials:
            return initials

        for n in self.G.nodes:
            if self.G.in_degree(n) == 0:
                initials.append(n)

        return initials

    def reachable_from_any_initial(self):

        reachable = set()

        for init in self.find_initial_states():
            reachable |= self.forward_reachable(init)

        return reachable

    # ---------------------------------------------------------
    # Goal-Oriented Slice
    # ---------------------------------------------------------

    def goal_slice(self, targets):

        forward = self.reachable_from_any_initial()
        backward = self.reverse_reachable(targets)

        keep = forward & backward

        return self.G.subgraph(keep).copy()

    def prune_away_from_targets(self, targets):

        forward = self.reachable_from_any_initial()
        backward = self.reverse_reachable(targets)

        keep = forward & backward

        H = nx.DiGraph()

        for n, data in self.G.nodes(data=True):
            if n in keep:
                H.add_node(n, **data)

        for u, v, data in self.G.edges(data=True):
            if u in keep and v in keep:
                H.add_edge(u, v, **data)

        return H

    # ---------------------------------------------------------
    # Shortest Path DAG
    # ---------------------------------------------------------

    @staticmethod
    def _is_useful_target(node_label: str) -> bool:
        """Filter out empty-label Alergia aggregation artifacts.

        Alergia merging can produce terminal states like ``,__success``
        (empty action and output) or ``EMPTY_NONE,EMPTY_NONE__fail``.
        These are not real exploit paths — they are statistical aggregates
        that create spurious direct edges to terminal states.
        """
        core = node_label.replace("__success", "").replace("__fail", "")
        if "," in core:
            action, output = core.split(",", 1)
            action = action.strip()
            output = output.strip()
            if not action or output.lower() in ("", "empty_none"):
                return False
        else:
            if not core.strip() or core.strip().lower() in ("empty_none", "wait"):
                return False
        return True

    def shortest_path_dag(self, targets):

        # Filter out empty-label aggregation artifacts before computing
        # shortest paths — otherwise the DAG collapses to a single
        # spurious direct edge from init to ``,,__success``.
        targets = [t for t in targets if self._is_useful_target(self.node_label(t))]
        if not targets:
            return nx.DiGraph()

        H = self.prune_away_from_targets(targets)

        initials = [
            n for n in self.find_initial_states()
            if n in H.nodes
        ]

        if not initials:
            return H

        # Distance from start
        d_start = {}

        for init in initials:
            lengths = nx.single_source_shortest_path_length(H, init)

            for node, dist in lengths.items():
                if node not in d_start:
                    d_start[node] = dist
                else:
                    d_start[node] = min(d_start[node], dist)

        # Distance to goal
        RH = H.reverse(copy=False)

        d_goal = {}

        for t in targets:

            if t not in H:
                continue

            lengths = nx.single_source_shortest_path_length(RH, t)

            for node, dist in lengths.items():
                if node not in d_goal:
                    d_goal[node] = dist
                else:
                    d_goal[node] = min(d_goal[node], dist)

        valid_targets = [t for t in targets if t in d_start]

        if not valid_targets:
            return H

        shortest_goal_distance = min(
            d_start[t] for t in valid_targets
        )

        D = nx.DiGraph()

        for n, data in H.nodes(data=True):

            if n in d_start and n in d_goal:
                if d_start[n] + d_goal[n] <= shortest_goal_distance:
                    D.add_node(n, **data)

        for u, v, data in H.edges(data=True):

            if u not in D:
                continue

            if v not in D:
                continue

            if (
                d_start[u] + 1 + d_goal[v]
                == shortest_goal_distance
            ):
                D.add_edge(u, v, **data)

        return D

    # ---------------------------------------------------------
    # Probability Handling
    # ---------------------------------------------------------

    def _edge_probability(self, u, v, data):

        for key in ["probability", "weight", "label"]:

            if key not in data:
                continue

            try:
                txt = str(data[key]).strip('"')
                m = re.search(r"([0-9]*\.?[0-9]+)", txt)

                if m:
                    return float(m.group(1))

            except Exception:
                pass

        return 1.0

    def success_probability(self, targets):

        H = self.prune_away_from_targets(targets)

        probs = {n: 0.0 for n in H.nodes}

        for t in targets:
            if t in probs:
                probs[t] = 1.0

        for _ in range(100):

            old = probs.copy()

            for n in H.nodes:

                if n in targets:
                    continue

                p = 0.0

                for _, succ, data in H.out_edges(n, data=True):
                    edge_p = self._edge_probability(n, succ, data)
                    p += edge_p * old[succ]

                probs[n] = min(1.0, p)

        return probs

    def topk_explanation(self, targets, k=1):

        H = self.prune_away_from_targets(targets)

        probs = self.success_probability(targets)

        E = nx.DiGraph()

        for n, data in H.nodes(data=True):
            E.add_node(n, **data)

        for n in H.nodes:

            # Terminal nodes (targets) have no outgoing edges
            if n in targets:
                continue

            candidates = []

            for _, succ, data in H.out_edges(n, data=True):

                score = (
                    self._edge_probability(n, succ, data)
                    * probs.get(succ, 0.0)
                )

                candidates.append((score, succ, data))

            candidates.sort(reverse=True)

            kept = candidates[:k]

            # Guarantee at least one outgoing edge so the node stays
            # connected to the targets (prevents orphan states).
            if not kept and candidates:
                kept = [candidates[0]]

            for _, succ, data in kept:
                E.add_edge(n, succ, **data)

        return E

    # ---------------------------------------------------------
    # SCC Collapse
    # ---------------------------------------------------------

    def collapse_sccs(self, graph):

        sccs = list(nx.strongly_connected_components(graph))

        mapping = {}
        CG = nx.DiGraph()

        for idx, comp in enumerate(sccs):

            if len(comp) == 1:

                node = next(iter(comp))
                mapping[node] = node

                CG.add_node(node, **graph.nodes[node])

            else:

                name = f"SCC_{idx}"

                CG.add_node(
                    name,
                    label=f"{name}\\n({len(comp)} states)"
                )

                for n in comp:
                    mapping[n] = name

        for u, v, data in graph.edges(data=True):

            cu = mapping[u]
            cv = mapping[v]

            if cu != cv:
                CG.add_edge(cu, cv, **data)

        return CG

    # ---------------------------------------------------------
    # Failure Grouping
    # ---------------------------------------------------------

    def group_failures(self, failure_nodes):

        groups = defaultdict(list)

        for n in failure_nodes:

            label = self.node_label(n)

            if "__" in label:
                key = label.split("__")[0]
            else:
                key = label

            groups[key].append(n)

        return dict(groups)


def export_graph(graph, filename):
    write_dot(graph, filename)
    print("wrote", filename)


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument("dot")
    parser.add_argument("--success", default="success")
    parser.add_argument("--failure", default="fail")
    parser.add_argument("--topk", type=int, default=1)

    args = parser.parse_args()

    G = read_dot(args.dot)

    goms = GOMS(G)

    success_nodes = goms.find_nodes_by_regex(args.success)
    failure_nodes = goms.find_nodes_by_regex(args.failure)

    print("Initial states:", goms.find_initial_states())
    print("Success nodes:", success_nodes)
    print("Failure nodes:", failure_nodes)

    for s in success_nodes:

        slice_graph = goms.goal_slice([s])
        export_graph(slice_graph, f"success_slice_{s}.dot")

        dag = goms.shortest_path_dag([s])
        export_graph(dag, f"success_dag_{s}.dot")

        topk = goms.topk_explanation([s], args.topk)
        export_graph(topk, f"success_topk_{s}.dot")

    for f in failure_nodes:

        slice_graph = goms.goal_slice([f])
        export_graph(slice_graph, f"failure_slice_{f}.dot")

    print()
    print("Failure groups:")
    print(goms.group_failures(failure_nodes))


if __name__ == "__main__":
    main()
