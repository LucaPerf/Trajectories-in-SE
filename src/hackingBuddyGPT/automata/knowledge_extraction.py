"""Extract strategic hints and transfer knowledge from learned automata models.

Phase 2 of the pipeline: analyzes a learned Markov chain / MDP to produce
actionable advice for the pentesting agent.
"""

import os
from collections import Counter, defaultdict

from aalpy import load_automaton_from_file
from aalpy.utils import save_automaton_to_file

from hackingBuddyGPT.utils.llm_util import LLM


def model_has_success(model_dot_path: str) -> bool:
    """Check if a learned model contains any successful trajectories.

    Args:
        model_dot_path: Path to the Graphviz DOT file.

    Returns:
        True if at least one state label contains "__success".
    """
    with open(model_dot_path, "r") as f:
        content = f.read()
    return "__success" in content


def extract_hints(model_dot_path: str, llm: LLM) -> str:
    """Extract strategic hints from a learned automaton model.

    Constructs a prompt that asks a reasoning LLM to analyze the Markov chain
    and produce actionable advice. If the model has success traces, the focus is
    on replicating them consistently. Otherwise, the focus is on avoiding failures
    and exploiting promising targets.

    Args:
        model_dot_path: Path to the learned model DOT file.
        llm: The LLM to use for hint extraction (should have thinking/reasoning enabled).

    Returns:
        A string containing strategic hints for the pentesting agent.
    """
    import json, os

    learned_model = load_automaton_from_file(model_dot_path, automaton_type="mc")

    # Try to load abstractions for a compact summary; fall back to full dump
    abstractions_path = model_dot_path.replace("hb_mc.dot", "abstractions.json")
    if os.path.exists(abstractions_path):
        with open(abstractions_path, "r") as f:
            abstractions_data = json.load(f)
        model_text = summarize_model(learned_model, abstractions_data)
    else:
        model_text = str(learned_model)

    prompt = f"""You are pentester and you are supposed to find an exploit.
You have 20 interactions to do so, after that you get a fail verdict.
In each interaction you can either:
`exec_command command`: give a command to be executed and I will respond with the terminal output when running this command over SSH on the linux machine. The given command must not require user interaction.
`test_credential username password`: give credentials to be tested.
`wait seconds`: Wait for a given number of seconds to allow time-dependent events (e.g., cron jobs) to occur. Usage: wait <seconds>
I have observed your previous attempts and created a Markov chain that models your interaction.
Below is a summary of the learned behavioral model.

{model_text}

Look at this model and provide hints for doing better, i.e., avoiding actions that do not
yield valuable results or suggesting actions that seem promising.
Make your hints specific to the given model, but do not reference states, state labels or transitions.
Provide clear, concise, actionable advice based on specifics that you spot in the model.
"""

    response = llm.get_response(prompt)

    if not response.result.strip():
        print("Hints extraction returned empty — retrying with compact prompt")
        prompt = (
            f"Based on this behavioral model summary, provide hints for improving "
            f"penetration testing:\n\n{model_text}\n\n"
            f"Be concise and actionable."
        )
        response = llm.get_response(prompt)

    return response.result


def summarize_model(learned_model, abstractions_data: dict) -> str:
    """Build a compact textual summary of a learned Markov chain.

    Avoids dumping the full DOT representation (which can be thousands of
    lines) and instead extracts key statistics and patterns.
    """
    import json
    from collections import Counter

    traces = abstractions_data.get("traces", [])

    # Count outcomes
    success_count = 0
    fail_count = 0
    step_counter = Counter()
    success_steps = Counter()
    fail_steps = Counter()

    for t in traces:
        items = sorted(t.items(), key=lambda x: int(x[0]))
        if not items:
            continue
        outcome = items[-1][1]
        if outcome == "success":
            success_count += 1
        else:
            fail_count += 1
        for k, v in items[:-1]:
            if isinstance(v, (list, tuple)) and len(v) >= 2:
                label = f"{v[0]} -> {v[1]}"
                step_counter[label] += 1
                if outcome == "success":
                    success_steps[label] += 1
                else:
                    fail_steps[label] += 1

    # Extract success paths (up to 3)
    success_paths = []
    for t in traces:
        items = sorted(t.items(), key=lambda x: int(x[0]))
        if not items or items[-1][1] != "success":
            continue
        path = []
        for k, v in items[:-1]:
            if isinstance(v, (list, tuple)) and len(v) >= 2:
                path.append(f"{v[0]} -> {v[1]}")
        if path:
            success_paths.append(path)
        if len(success_paths) >= 3:
            break

    # Compact summary
    lines = [
        f"Model summary: {len(traces)} traces, {success_count} success, {fail_count} failure.",
        f"States: {len(learned_model.states)}.",
        "",
        "Most frequent steps in success traces:",
    ]
    for step, count in success_steps.most_common(8):
        lines.append(f"  {step}  (seen {count}x)")

    lines.append("")
    lines.append("Most frequent steps in failure traces:")
    for step, count in fail_steps.most_common(5):
        lines.append(f"  {step}  (seen {count}x)")

    if success_paths:
        lines.append("")
        lines.append("Example success paths (abstract steps):")
        for i, path in enumerate(success_paths):
            lines.append(f"  Path {i + 1}: {' -> '.join(path)}")

    # Add the most frequent success STEP with both action AND output context,
    # and flag steps that lead to error so the LLM can avoid them.
    if success_steps:
        lines.append("")
        lines.append("Key insight — most frequent step leading to root:")
        top_step, top_count = success_steps.most_common(1)[0]
        lines.append(f"  {top_step}  (seen {top_count}x — THIS is the exploit)")
    if fail_steps:
        lines.append("Steps to AVOID (lead to errors/dead ends):")
        for step, count in fail_steps.most_common(3):
            lines.append(f"  AVOID: {step}  (seen {count}x)")

    # Extract raw commands from successful traces so the LLM knows the actual
    # shell commands (not just abstract categories like "credential testing").
    raw_commands = []
    for t in traces:
        items = sorted(t.items(), key=lambda x: int(x[0]))
        if not items or items[-1][1] != "success":
            continue
        # Get the last interaction before the terminal state — the exploit step
        for k, v in reversed(items[:-1]):
            if isinstance(v, (list, tuple)) and len(v) >= 2:
                cat = v[0]
                if "credential" in cat.lower() or "exploit" in cat.lower() or "root" in v[1].upper():
                    raw_commands.append(cat)
                    break
    if raw_commands:
        from collections import Counter as _Counter
        top_raw = _Counter(raw_commands).most_common(3)
        lines.append("")
        lines.append("Actual exploit commands from successful runs:")
        for cmd, cnt in top_raw:
            lines.append(f"  {cmd}  (used {cnt}x)")

    return "\n".join(lines)


def describe_model(abstractions_path: str) -> str:
    """Generate a short natural-language description of a learned behavioral model.

    Args:
        abstractions_path: Path to the abstractions.json file.

    Returns:
        A paragraph describing the model's key characteristics.
    """
    import json

    with open(abstractions_path, "r") as f:
        data = json.load(f)

    traces = data.get("traces", [])
    success_count = sum(1 for t in traces
                        if sorted(t.items(), key=lambda x: int(x[0]))[-1][1] == "success"
                        if t)
    fail_count = len(traces) - success_count

    # Find dominant success and failure steps
    success_steps = Counter()
    fail_steps = Counter()
    for t in traces:
        items = sorted(t.items(), key=lambda x: int(x[0]))
        if not items:
            continue
        outcome = items[-1][1]
        for k, v in items[:-1]:
            if isinstance(v, (list, tuple)) and len(v) >= 2:
                step = f"{v[0]}"
                (success_steps if outcome == "success" else fail_steps)[step] += 1

    top_success = success_steps.most_common(3)
    top_fail = fail_steps.most_common(3)

    desc = (
        f"This behavioral model was learned from {len(traces)} penetration-testing runs. "
        f"{success_count} runs succeeded and {fail_count} failed. "
    )
    if top_success:
        desc += (
            f"Successful runs most frequently involved "
            f"{' ,'.join(f'{act} ({n}x)' for act, n in top_success)}. "
        )
    if top_fail:
        desc += (
            f"Failed runs often involved "
            f"{' ,'.join(f'{act} ({n}x)' for act, n in top_fail)}. "
        )
    if success_count > 0 and fail_count > 0:
        desc += (
            "The model distinguishes success and failure trajectories, "
            "enabling analysis of what strategies work and which lead to dead ends."
        )
    return desc


def prune_model(
    model_dot_path: str,
    target: str = "success",
    output_path: str | None = None,
    min_prob: float = 0.0,
) -> str:
    """Prune a Markov chain to show only paths leading to a target outcome.

    Removes states and transitions that cannot reach a terminal state with
    the given target suffix (``__success`` or ``__fail``).  Optionally filters
    out low-probability transitions.

    Args:
        model_dot_path: Path to the learned Markov chain DOT file.
        target: ``"success"`` or ``"fail"`` — which terminal states to keep.
        output_path: Where to write the pruned DOT file (default: derives from input).
        min_prob: Drop transitions with probability below this threshold.

    Returns:
        Path to the pruned DOT file.
    """
    model = load_automaton_from_file(model_dot_path, automaton_type="mc")

    if output_path is None:
        base = model_dot_path.replace(".dot", "").replace("hb_mc", "hb_mc")
        output_path = f"{base}_{target}.dot"

    target_suffix = f"__{target}"

    # ---- 1. Find terminal states for the target ----
    # The label (with __success/__fail) is in the 'output' attribute, not state_id.
    target_terminal_states = []
    for s in model.states:
        label = getattr(s, "output", "") or ""
        if target_suffix in label:
            target_terminal_states.append(s)

    if not target_terminal_states:
        print(f"No terminal states found for target '{target}' — saving unmodified.")
        save_automaton_to_file(model, path=output_path, round_floats=2)
        return output_path

    # ---- 2. Reverse reachability: states that can reach target terminals ----
    # Build reverse adjacency: target -> set of source states
    # transitions are (target_state, probability) tuples
    reverse = defaultdict(set)
    for s in model.states:
        for trans in s.transitions:
            tgt = trans[0]  # tuple: (target_state, probability)
            reverse[tgt].add(s)

    # BFS backwards from terminal states
    reachable = set(target_terminal_states)
    queue = list(target_terminal_states)
    while queue:
        cur = queue.pop(0)
        for pred in reverse.get(cur, set()):
            if pred not in reachable:
                reachable.add(pred)
                queue.append(pred)

    # Include the initial state even if it has no incoming edges
    if model.initial_state not in reachable:
        # Check if initial state can reach any reachable state
        init_reachable = set()
        queue = [model.initial_state]
        while queue:
            cur = queue.pop(0)
            if cur in init_reachable:
                continue
            init_reachable.add(cur)
            for trans in cur.transitions:
                if trans[0] not in init_reachable:
                    queue.append(trans[0])
        if init_reachable & reachable:
            reachable.add(model.initial_state)

    # ---- 3. Build new state set and transitions ----
    kept_states = [s for s in model.states if s in reachable]
    kept_set = set(kept_states)

    # Only keep transitions where BOTH source and target are reachable,
    # and the probability meets the threshold.  Always keep at least the
    # highest-probability outgoing edge from each state to preserve connectivity.
    pruned_transitions = {}
    for s in kept_states:
        candidates = [t for t in s.transitions if t[0] in kept_set]
        if not candidates:
            continue
        if min_prob == 0.0:
            pruned_transitions[s] = candidates
        else:
            # Keep transitions at or above threshold...
            filtered = [t for t in candidates if t[1] >= min_prob]
            # ...but always keep the single highest-probability edge
            if not filtered:
                best = max(candidates, key=lambda x: x[1])
                filtered = [best]
            pruned_transitions[s] = filtered

    # ---- 3b. Forward reachability after threshold filtering ----
    # Threshold filtering may remove edges that were the only way to reach some
    # states.  Do a forward BFS from the initial state using only the pruned
    # edges to find which states are actually reachable.
    if min_prob > 0.0:
        fwd_reachable = set()
        queue = [model.initial_state]
        while queue:
            cur = queue.pop(0)
            if cur in fwd_reachable:
                continue
            fwd_reachable.add(cur)
            for tgt, _ in pruned_transitions.get(cur, []):
                if tgt not in fwd_reachable:
                    queue.append(tgt)

        # Keep only forward-reachable states
        kept_states = [s for s in kept_states if s in fwd_reachable]
        kept_set = set(kept_states)
        # Re-filter transitions to only use kept states
        pruned_transitions = {
            s: [t for t in trans if t[0] in kept_set]
            for s, trans in pruned_transitions.items()
            if s in kept_set
        }

    if not pruned_transitions:
        print("All states pruned — nothing left.")
        return output_path

    # ---- 4. Write pruned DOT ----
    lines = [f"digraph hb_mc_{target} {{",
             '  rankdir=LR;',
             '  node [shape=box, style=rounded, fontsize=10];',
             '  edge [fontsize=9];',
             '  __start0 [label="", shape=plaintext];']

    state_to_id = {}
    for i, s in enumerate(kept_states):
        sid = f"q{i}"
        state_to_id[s] = sid
        label = (getattr(s, "output", "") or s.state_id or "").replace('"', '\\"')
        # Shorten long labels for readability
        if len(label) > 60:
            label = label[:57] + "..."
        lines.append(f'  {sid} [label="{label}"];')

    lines.append(f'  __start0 -> {state_to_id[model.initial_state]};')

    for s in kept_states:
        if s not in pruned_transitions:
            continue
        src_id = state_to_id[s]
        for trans in pruned_transitions[s]:
            # transitions are (target_state, probability) tuples
            tgt_state, prob = trans[0], trans[1]
            tgt_id = state_to_id[tgt_state]
            lines.append(f'  {src_id} -> {tgt_id} [label={prob:.2f}];')

    lines.append("}")

    with open(output_path, "w") as f:
        f.write("\n".join(lines) + "\n")

    kept = len(kept_states)
    total = len(model.states)
    print(f"Pruned {target}: kept {kept}/{total} states ({kept * 100 // total}%)"
          f"{' (min_prob=' + str(min_prob) + ')' if min_prob else ''}"
          f" -> {output_path}")
    return output_path


def prune_model_multi(
    model_dot_path: str,
    target: str = "success",
    output_dir: str | None = None,
    thresholds: list[float] | None = None,
) -> dict[float, dict]:
    """Generate pruned model views at multiple probability thresholds.

    Each threshold level reveals progressively more dominant behaviors.
    Threshold 0.0 keeps all reachable paths; higher values keep only
    high-probability transitions, exposing the core strategies.

    Args:
        model_dot_path: Path to the learned Markov chain DOT file.
        target: ``"success"`` or ``"fail"`` — which outcome to focus on.
        output_dir: Directory for pruned DOT files (default: derived from input).
        thresholds: Probability thresholds to apply (default: [0.0, 0.05, 0.1, 0.2, 0.5]).

    Returns:
        Dict mapping threshold → {path, states_kept, states_total, pct}.
    """
    import os as _os

    if thresholds is None:
        thresholds = [0.0, 0.3, 0.5, 0.7, 0.9]

    if output_dir is None:
        output_dir = _os.path.dirname(model_dot_path)

    results = {}
    print(f"Multi-threshold pruning for '{target}' ({len(thresholds)} levels):")
    for t in thresholds:
        base = _os.path.basename(model_dot_path).replace(".dot", "")
        out = _os.path.join(output_dir, f"{base}_{target}_p{int(t * 100):02d}.dot")
        _ = prune_model(model_dot_path, target, out, min_prob=t)

        # Count states in the output (node defs: "  qN [label=\"...\"]")
        import re as _re
        with open(out) as f:
            dot = f.read()
        state_count = len(_re.findall(r'^\s*q\d+\s*\[label="', dot, _re.MULTILINE))
        results[t] = {"path": out, "states": state_count}
        print(f"  threshold={t:.2f}: {state_count} states -> {out}")

    return results


# Fixed post-recon footer used by common_path mode.
# Deliberately does NOT encourage find-looping — pushes toward credential hunting
# and investigation of what was found.
_EXPLORE_FOOTER = """NEXT: After the steps above, look for credentials and escalation paths:
- Check bash history: `cat /home/*/.bash_history | grep -i passw`
- Check for writable files/dirs: `find / -writable -type f 2>/dev/null`
- Check services and cron: `ps aux`, `cat /etc/crontab 2>/dev/null`
- If you found a password, test it: `test_credential root <password>` or `su root`
- If you found a SUID binary, research it or try running it
Do NOT keep running the same find command with different flags — move on."""


def extract_common_path(
    abstractions_path: str,
    threshold: float = 0.5,
) -> str:
    """Extract the most common success path across all traces (LLM-free).

    Finds steps that appear in the majority of success traces at each position,
    then concretizes them using the concretization mapping.

    Args:
        abstractions_path: Path to abstractions.json.
        threshold: Fraction of traces that must share a step for it to be included
                   in the common path (default 0.5 = majority).

    Returns:
        Formatted strategy string with common steps and explore-around footer.
    """
    import json, os
    from collections import Counter

    with open(abstractions_path) as f:
        data = json.load(f)

    # Load concretization
    concretization_path = abstractions_path.replace("abstractions.json", "concretization.json")
    concretization = {}
    if os.path.exists(concretization_path):
        with open(concretization_path) as f:
            concretization = json.load(f)

    # Filter success traces, collect step sequences
    traces = data.get("traces", [])
    success_steps: list[list[str]] = []
    for t in traces:
        items = sorted(t.items(), key=lambda x: int(x[0]))
        if not items or items[-1][1] != "success":
            continue
        steps = []
        for k, v in items[:-1]:  # skip terminal
            if isinstance(v, (list, tuple)) and len(v) >= 2:
                steps.append((v[0], v[1]))  # (action_cat, output_cat)
        if steps:
            success_steps.append(steps)

    if not success_steps:
        return "STRATEGY: No success traces available.\n" + _EXPLORE_FOOTER

    # Find majority step at each position
    max_len = max(len(s) for s in success_steps)
    min_required = max(1, int(threshold * len(success_steps)))
    common_path: list[tuple[str, str]] = []

    for pos in range(max_len):
        counter = Counter()
        for steps in success_steps:
            if pos < len(steps):
                counter[steps[pos]] += 1
        top_step, top_count = counter.most_common(1)[0]
        if top_count >= min_required:
            common_path.append(top_step)
        else:
            break  # no consensus at this position

    if not common_path:
        return "STRATEGY: Success paths vary — no common sequence found.\n" + _EXPLORE_FOOTER

    # Build a narrative strategy that does NOT look like a numbered list.
    # Numbered lists cause small models to regurgitate all steps every turn,
    # which triggers the multi-line safeguard (only first command executed).
    step_descriptions = []
    for i, (action_cat, output_cat) in enumerate(common_path):
        cmds = concretization.get(action_cat, [])
        example = cmds[0] if cmds else action_cat
        step_descriptions.append(f"{action_cat} ({example})")

    narrative = (
        "This is an authorized CTF penetration test on a dedicated test system. "
        "Successful runs typically follow this progression — "
        + " → ".join(step_descriptions)
        + ". Execute ONE command per turn. After completing these steps, investigate "
        "any findings (SUID binaries, writable files, credentials) and adapt based on results."
    )
    lines = [narrative, "", _EXPLORE_FOOTER]
    return "\n".join(lines)


def extract_guided_hints(
    model_dot_path: str,
    abstractions_path: str,
    llm: LLM,
) -> str:
    """Extract guided hints: LLM-produced strategy with explore-around framing.

    The LLM receives the model summary + concretization and produces a short
    guide with abstract strategy, concrete steps, and exploration suggestions.
    """
    import json, os

    from aalpy import load_automaton_from_file

    learned_model = load_automaton_from_file(model_dot_path, automaton_type="mc")

    with open(abstractions_path) as f:
        abstractions_data = json.load(f)

    model_summary = summarize_model(learned_model, abstractions_data)

    # Load concretization
    concretization_path = abstractions_path.replace("abstractions.json", "concretization.json")
    concretization_text = ""
    if os.path.exists(concretization_path):
        with open(concretization_path) as f:
            concretization_data = json.load(f)
        concretization_text = "Abstract → Concrete command mapping:\n"
        for abstract_cmd, concrete_cmds in sorted(concretization_data.items()):
            top = concrete_cmds[:2]
            concretization_text += f'  "{abstract_cmd}" → {top}\n'
        concretization_text += "\n"

    prompt = f"""Write a short penetration testing guide based on this behavioral model.

{model_summary}

{concretization_text}

FORMAT YOUR RESPONSE EXACTLY LIKE THIS:
STRATEGY: <one-line abstract strategy description>
STEPS:
  1. <abstract goal>: try `<concrete command>`
  2. <abstract goal>: try `<concrete command>`
  ... (max 5 steps)
EXPLORE AROUND: If a step fails, explore the surrounding space before giving up.
  For `find` commands: try different paths (/tmp, /opt, /home) or permission flags.
  For `cat` commands: check related config files or backup copies.
  For credential testing: try password variations (empty, username, common passwords).
  If you find something promising (SUID binary, writable file, credential),
  investigate it further.

Keep the entire response under 600 characters.
"""

    response = llm.get_response(prompt)

    # Retry on empty
    if not response.result.strip():
        print("Guided hints returned empty — retrying with compact prompt")
        prompt = f"Based on this model, write a short penetration testing guide:\n\n{model_summary}\n\n{concretization_text}\n\nFORMAT: STRATEGY: ... STEPS: 1. ... 2. ... EXPLORE AROUND: ... Keep under 500 chars."
        response = llm.get_response(prompt)

    result = response.result
    if len(result) > 800:
        result = result[:800] + "\n..."
    return result


def extract_transfer_knowledge(
    model_dot_path: str,
    abstractions_path: str,
    llm: LLM,
) -> str:
    """Extract transfer knowledge: instructions for replicating successful behavior.

    Args:
        model_dot_path: Path to the learned model DOT file.
        abstractions_path: Path to the abstractions.json file.
        llm: The LLM to use for knowledge extraction.

    Returns:
        A string with step-by-step instructions for replicating success.
    """
    import json

    learned_model = load_automaton_from_file(model_dot_path, automaton_type="mc")

    with open(abstractions_path, "r") as f:
        abstractions_data = json.load(f)

    model_summary = summarize_model(learned_model, abstractions_data)

    # Load concretization mapping if available
    concretization_path = abstractions_path.replace("abstractions.json", "concretization.json")
    concretization_text = ""
    if os.path.exists(concretization_path):
        with open(concretization_path) as f:
            concretization_data = json.load(f)
        concretization_text = "Abstract → Concrete command mapping:\n"
        for abstract_cmd, concrete_cmds in sorted(concretization_data.items()):
            top = concrete_cmds[:2]
            concretization_text += f"  \"{abstract_cmd}\" → {top}\n"
        concretization_text += "\n"

    prompt = f"""You are analyzing a penetration testing agent's behavior to help a less capable agent
replicate successful strategies.

{model_summary}

{concretization_text}

Based on this data, complete TWO tasks:

TASK 1 — Find a strategy: Identify a sequence of abstract steps in the model
summary that reaches __success, avoiding steps whose output is ERROR, EMPTY,
or REPEATED (those are dead ends).

TASK 2 — Concretize: Translate each abstract step into a real shell command
using the Abstract→Concrete mapping above. The last step must be the command
that directly achieves root (EXPLOITABLE_ROOT).

CRITICAL: Output ACTUAL shell commands (exec_command X, test_credential Y, etc.),
NOT abstract categories like "credential_testing" or "privilege_escalation".
Use the exact commands from the mapping.

Focus on the 2-3 most important commands. Use this format:
  STRATEGY:
  1. <command>
  2. <command>
  3. <command>
"""

    response = llm.get_response(prompt)

    # If the model returned empty (transient 401s or model refusal), retry once
    # with a compact prompt that sends only the summary.
    if not response.result.strip():
        print("Transfer knowledge extraction returned empty — retrying with compact prompt")
        prompt = (
            f"Based on this behavioral model, list the 2-3 most important commands "
            f"for privilege escalation on this system (under 100 words):\n\n"
            f"{model_summary}\n\n"
            f"Format: STRATEGY: 1. <cmd> 2. <cmd> 3. <cmd>"
        )
        response = llm.get_response(prompt)

    # Truncate overly long instructions — the target model has a small context
    # window and long instructions drown out the syntax/formatting rules.
    result = response.result
    if len(result) > 800:
        result = result[:800] + "\n..."
        print(f"Transfer instructions truncated from {len(response.result)} to 800 chars")

    return result


# =============================================================================
# GOMS-based graph slicing (networkx)
# =============================================================================

def _goms_load_and_find_targets(model_dot_path: str, target: str):
    """Load a DOT file via networkx and find terminal nodes matching target."""
    from networkx.drawing.nx_pydot import read_dot
    from .goms import GOMS

    graph = read_dot(model_dot_path)
    goms = GOMS(graph)
    target_nodes = goms.find_nodes_by_regex(f"__{target}")
    return goms, target_nodes


def goms_slice(model_dot_path: str, target: str, output_path: str) -> str:
    """Goal-oriented slice: only states on paths from init to target terminals."""
    from .goms import export_graph

    goms, target_nodes = _goms_load_and_find_targets(model_dot_path, target)
    if not target_nodes:
        print(f"No '{target}' nodes found in {model_dot_path}")
        return output_path
    sliced = goms.goal_slice(target_nodes)
    export_graph(sliced, output_path)
    print(f"GOMS slice ({target}): {len(sliced.nodes)} nodes -> {output_path}")
    return output_path


def goms_dag(model_dot_path: str, target: str, output_path: str) -> str:
    """Shortest-path DAG: only nodes on shortest paths to target terminals."""
    from .goms import export_graph

    goms, target_nodes = _goms_load_and_find_targets(model_dot_path, target)
    if not target_nodes:
        print(f"No '{target}' nodes found in {model_dot_path}")
        return output_path
    dag = goms.shortest_path_dag(target_nodes)
    export_graph(dag, output_path)
    print(f"GOMS DAG ({target}): {len(dag.nodes)} nodes -> {output_path}")
    return output_path


def goms_topk(model_dot_path: str, target: str, output_path: str, k: int = 1) -> str:
    """Top-k explanation: keep k best outgoing edges per node.

    Edges ranked by probability × successor success probability.
    Always keeps at least one edge per non-terminal node for connectivity.
    After edge pruning, removes nodes unreachable from the init state.
    """
    from .goms import export_graph

    goms, target_nodes = _goms_load_and_find_targets(model_dot_path, target)
    if not target_nodes:
        print(f"No '{target}' nodes found in {model_dot_path}")
        return output_path
    topk = goms.topk_explanation(target_nodes, k)

    # Prune nodes not forward-reachable from init after edge filtering
    init_nodes = [n for n in topk.nodes
                  if topk.nodes[n].get("label", "").strip('"') == "init"]
    if init_nodes:
        init_id = init_nodes[0]
        reachable = set()
        stack = [init_id]
        while stack:
            node = stack.pop()
            if node in reachable:
                continue
            reachable.add(node)
            for _, dst in topk.out_edges(node):
                if dst not in reachable:
                    stack.append(dst)
        to_remove = [n for n in topk.nodes if n not in reachable]
        topk.remove_nodes_from(to_remove)

    export_graph(topk, output_path)
    print(f"GOMS top-{k} ({target}): {len(topk.nodes)} nodes -> {output_path}")
    return output_path
