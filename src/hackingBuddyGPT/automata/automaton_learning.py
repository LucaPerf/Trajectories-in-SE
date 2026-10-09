"""Learn automata (Markov chains / MDPs) from abstract traces using AALpy.

Refactored from learn_automata.py. Supports both MC (comma-joined string labels)
and MDP (tuple labels) modes.
"""

import json

from aalpy import run_Alergia
from aalpy.utils import save_automaton_to_file


def traces_to_aalpy(
    abstractions_data: dict,
    automaton_type: str = "mc",
) -> list[list]:
    """Convert abstractions.json-format traces into AALpy-compatible traces.

    Args:
        abstractions_data: Dict with "traces" key containing list of trace dicts.
        automaton_type: "mc" for Markov chain (labels joined with comma) or
                        "mdp" for MDP (labels as tuples).

    Returns:
        List of AALpy traces, each starting with "init".
    """
    traces = abstractions_data["traces"]
    aalpy_traces = []

    for t in traces:
        # Sort by integer key
        aalpy_t = sorted(list(t.items()), key=lambda x: int(x[0]))
        if len(aalpy_t) == 0:
            continue

        _, aalpy_t = zip(*aalpy_t)
        aalpy_t = list(aalpy_t)

        # Convert any tuple elements to lists so we can mutate them below.
        # (abstraction.py stores action/output pairs as tuples.)
        aalpy_t = [list(x) if isinstance(x, tuple) else x for x in aalpy_t]

        # Check terminal state
        is_fail = aalpy_t[-1] == "fail"

        # Remove terminal marker, append to last interaction's output
        aalpy_t = aalpy_t[:-1]

        if len(aalpy_t) == 0:
            # No interactions, only terminal state — skip tagging below
            aalpy_t.append(("", "__fail" if is_fail else "__success"))
            if automaton_type == "mc":
                aalpy_t = [",".join(symb) if isinstance(symb, (tuple, list)) else symb for symb in aalpy_t]
            else:
                aalpy_t = [tuple(symb) if isinstance(symb, list) else symb for symb in aalpy_t]
            aalpy_t.insert(0, "init")
            aalpy_traces.append(aalpy_t)
            continue

        # Tag the last interaction with the outcome
        if automaton_type == "mc":
            last_action, last_output = aalpy_t[-1] if isinstance(aalpy_t[-1], (tuple, list)) else (aalpy_t[-1], "")
            if isinstance(aalpy_t[-1], str):
                aalpy_t[-1] = aalpy_t[-1] + ("__fail" if is_fail else "__success")
            else:
                aalpy_t[-1][1] = aalpy_t[-1][1] + ("__fail" if is_fail else "__success")
        else:
            last_output = aalpy_t[-1][1] if isinstance(aalpy_t[-1], (tuple, list)) else ""
            if isinstance(aalpy_t[-1], (tuple, list)):
                aalpy_t[-1] = (aalpy_t[-1][0], aalpy_t[-1][1] + ("__fail" if is_fail else "__success"))

        # Convert to AALpy format
        if automaton_type == "mc":
            aalpy_t = [",".join(symb) if isinstance(symb, (tuple, list)) else symb for symb in aalpy_t]
        else:
            aalpy_t = [tuple(symb) if isinstance(symb, list) else symb for symb in aalpy_t]

        aalpy_t.insert(0, "init")
        aalpy_traces.append(aalpy_t)

    return aalpy_traces


def learn_automaton(
    aalpy_traces: list[list],
    automaton_type: str = "mc",
    eps: float = 0.05,
):
    """Learn an automaton from AALpy-format traces using the Alergia algorithm.

    Args:
        aalpy_traces: Traces in AALpy format (lists starting with "init").
        automaton_type: "mc" for Markov chain, "mdp" for MDP.
        eps: Alergia compatibility threshold. Lower = larger, more precise model.

    Returns:
        The learned automaton object.
    """
    model_type = "mc" if automaton_type == "mc" else "mdp"
    return run_Alergia(aalpy_traces, automaton_type=model_type, eps=eps)


def save_learned_model(automaton, path: str, round_floats: int = 2) -> None:
    """Save a learned automaton to a Graphviz DOT file.

    Args:
        automaton: The learned automaton from learn_automaton().
        path: Output file path (e.g., "hb_mc.dot").
        round_floats: Number of decimal places for probabilities.
    """
    save_automaton_to_file(automaton, path=path, round_floats=round_floats)


def learn_and_save(
    abstractions_path: str,
    output_path: str,
    automaton_type: str = "mc",
    eps: float = 0.05,
) -> None:
    """Convenience: read abstractions.json, learn automaton, save to DOT file.

    Args:
        abstractions_path: Path to abstractions.json.
        output_path: Path for the output DOT file.
        automaton_type: "mc" or "mdp".
        eps: Alergia compatibility threshold.
    """
    with open(abstractions_path, "r") as f:
        abstractions_data = json.load(f)

    aalpy_traces = traces_to_aalpy(abstractions_data, automaton_type=automaton_type)
    print("====" * 30)
    for t in aalpy_traces:
        print(t)

    learned = learn_automaton(aalpy_traces, automaton_type=automaton_type, eps=eps)
    save_learned_model(learned, path=output_path)
