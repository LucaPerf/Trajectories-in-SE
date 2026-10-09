"""
Dynamic guidance: runtime automaton navigation for penetration testing.

At each turn, classifies the last (command, result) pair against known categories,
matches against the learned Markov chain, evaluates whether the step was expected,
and suggests the most promising next transition toward a __success terminal state.
"""
from __future__ import annotations

import json
import os
import re
from collections import deque
from dataclasses import dataclass, field
from typing import Optional

from .knowledge_models import AbstractionsFile


# =============================================================================
# Automaton loading & indexing
# =============================================================================

def load_automaton(dot_path: str):
    """Load a learned Markov chain from a DOT file via AALpy.

    Returns the automaton object with states that have:
      - state_id: unique string ID (e.g. "q0", "q42")
      - output: label string (e.g. "command execution (id),DISCOVERY_USER")
      - transitions: list of (target_state, probability) tuples
    """
    from aalpy.utils import load_automaton_from_file
    return load_automaton_from_file(dot_path, automaton_type="mc")


def build_state_index(automaton) -> dict[str, object]:
    """Build a lookup from label string -> state object.

    Terminal states have __success or __fail appended to their output category,
    e.g. "credential testing,EXPLOITABLE_ROOT__success".
    """
    index = {}
    for state in automaton.states:
        label = getattr(state, "output", "") or str(state.state_id)
        index[label] = state
    return index


def is_success_state(state) -> bool:
    return "__success" in (getattr(state, "output", "") or "")


def is_fail_state(state) -> bool:
    return "__fail" in (getattr(state, "output", "") or "")


# =============================================================================
# Path finding
# =============================================================================

def find_path_to_success(automaton, start_state, state_index) -> Optional[list]:
    """BFS to find shortest path from start_state to any __success state.

    Returns list of (state, transition_probability) pairs, or None if unreachable.
    """
    visited = {start_state.state_id}
    queue = deque([(start_state, [])])

    while queue:
        current, path = queue.popleft()
        for target, prob in current.transitions:
            if target.state_id in visited:
                continue
            visited.add(target.state_id)
            new_path = path + [(target, round(prob, 3))]
            if is_success_state(target):
                return new_path
            queue.append((target, new_path))
    return None


def _is_useful_state(t_state) -> bool:
    """Skip wait/enumeration-of-system-information — never useful."""
    label = (getattr(t_state, "output", "") or "").lower()
    skip = ("wait", "empty_none", "enumeration of system information")
    return not any(s in label for s in skip)


def find_best_transition(state, state_index) -> Optional[tuple]:
    """From a state, pick the outgoing transition most likely to lead to success.

    Skips wait/empty states which are never useful suggestions.
    """
    if not state.transitions:
        return None

    sorted_tx = sorted(state.transitions, key=lambda t: t[1], reverse=True)

    # Prefer success-terminal, non-useless transitions WITH a real action
    success_tx = [(t, p) for t, p in sorted_tx
                  if is_success_state(t) and _is_useful_state(t)
                  and (getattr(t, "output", "") or "").split(",")[0].strip()]
    if success_tx:
        return success_tx[0]

    # Avoid fail-terminal and useless transitions
    non_fail = [(t, p) for t, p in sorted_tx if not is_fail_state(t) and _is_useful_state(t)]
    if non_fail:
        return non_fail[0]

    # All useful filtered — try any non-fail
    non_fail_any = [(t, p) for t, p in sorted_tx if not is_fail_state(t)]
    if non_fail_any:
        return non_fail_any[0]

    return sorted_tx[0] if sorted_tx else None


# =============================================================================
# Similarity matching (fallback when exact match fails)
# =============================================================================

def _label_similarity(label_a: str, label_b: str) -> float:
    """Simple token-overlap similarity between two category labels."""
    tokens_a = set(label_a.lower().replace("(", " ").replace(")", " ").replace(",", " ").split())
    tokens_b = set(label_b.lower().replace("(", " ").replace(")", " ").replace(",", " ").split())
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = tokens_a & tokens_b
    return len(intersection) / max(len(tokens_a), len(tokens_b))


def find_closest_state(action_cat: str, output_cat: str, state_index: dict) -> Optional[object]:
    """Find the automaton state whose label most closely matches the given categories.

    Tries multiple matching strategies in order:
    1. Exact match: "action_cat,output_cat"
    2. Exact match with terminal suffix
    3. Match action_cat alone (ignore output_cat mismatch)
    4. Substring match — action_cat appears within a state label
    5. Token-overlap similarity fallback
    """
    exact_key = f"{action_cat},{output_cat}"
    if exact_key in state_index:
        return state_index[exact_key]

    # Also try with __success / __fail suffixes
    for suffix in ("__success", "__fail"):
        if f"{exact_key}{suffix}" in state_index:
            return state_index[f"{exact_key}{suffix}"]

    # Match action_cat alone against the action portion of each state label
    # State labels are "action_cat,output_cat" — compare just the action part
    for label, state in state_index.items():
        label_action = label.split(",")[0] if "," in label else ""
        label_action = label_action.replace("__success", "").replace("__fail", "")
        if action_cat.strip().lower() == label_action.strip().lower():
            return state

    # Substring match: action_cat appears anywhere in the state label
    for label, state in state_index.items():
        if action_cat.lower() in label.lower():
            return state

    # Fuzzy fallback
    best_state = None
    best_score = 0.0
    for label, state in state_index.items():
        score = _label_similarity(exact_key, label)
        if score > best_score and score > 0.3:
            best_score = score
            best_state = state

    return best_state


# =============================================================================
# Cheap LLM classification
# =============================================================================

CLASSIFY_PROMPT = """You are a classifier. Given a command and its output, assign the SINGLE best matching action category and output category from the lists below.

Action categories (what the command does):
{act_cats}

Output categories (what the result contains):
{out_cats}

Command: {cmd}
Output (truncated): {result}

Return EXACTLY one line in the format: action_category -> output_category
Do not add explanation."""


def classify_interaction(cmd: str, result: str, act_categories: list[str],
                         out_categories: list[str], llm) -> tuple[str, str]:
    """Classify a (command, output) pair using a cheap LLM.

    Returns (action_category, output_category) or ("unknown", "unknown") on failure.
    """
    # Truncate result to keep tokens low
    result_short = result[:500] if len(result) > 500 else result

    prompt = CLASSIFY_PROMPT.format(
        act_cats=", ".join(sorted(act_categories)),
        out_cats=", ".join(sorted(out_categories)),
        cmd=cmd[:200],
        result=result_short,
    )

    try:
        response = llm.get_response(prompt)
        text = response.result.strip()
        # Parse "action_cat -> output_cat"
        match = re.match(r"(.+?)\s*->\s*(.+)", text)
        if match:
            return match.group(1).strip(), match.group(2).strip()
        # Fallback: try to match known categories directly
        for act in act_categories:
            if act.lower() in text.lower():
                for out in out_categories:
                    if out.lower() in text.lower():
                        return act, out
        # Last resort: try comma-separated
        if "," in text:
            parts = text.split(",", 1)
            return parts[0].strip(), parts[1].strip()
    except Exception:
        pass

    return "unknown", "unknown"


# =============================================================================
# Main DynamicGuidance class
# =============================================================================

@dataclass
class DynamicGuidance:
    """Runtime automaton navigator for dynamic penetration testing guidance.

    Tracks automaton state across turns, classifies interactions, evaluates
    whether the agent followed the suggested path, and generates feedback
    with the next suggested step.
    """

    dot_path: str
    abstractions_path: str
    concretization_path: str
    classification_llm: object  # OpenAIConnection for cheap classification

    # Loaded state
    _automaton: object = field(default=None, repr=False)
    _state_index: dict = field(default_factory=dict, repr=False)
    _act_categories: list[str] = field(default_factory=list)
    _out_categories: list[str] = field(default_factory=list)
    _concretization: dict = field(default_factory=dict)

    # Runtime state tracking
    current_state_id: str = ""
    suggested_state_id: str = ""  # state we told the agent to go to
    suggested_action: str = ""    # action we suggested last turn
    _tried_transitions: set = field(default_factory=set)  # (from_state, to_state) pairs already suggested
    _tried_actions: set = field(default_factory=set)      # action strings already tried this run

    def load(self):
        """Load automaton, categories, and concretization from disk."""
        # Load automaton
        self._automaton = load_automaton(self.dot_path)
        self._state_index = build_state_index(self._automaton)

        # Load categories from abstractions
        with open(self.abstractions_path) as f:
            abstractions = json.load(f)
        self._act_categories = abstractions.get("act_categories", [])
        self._out_categories = abstractions.get("out_categories", [])

        # Load concretization
        if os.path.exists(self.concretization_path):
            with open(self.concretization_path) as f:
                self._concretization = json.load(f)

        # Start at init state
        init = self._state_index.get("init")
        if init:
            self.current_state_id = init.state_id

    def classify(self, cmd: str, result: str) -> tuple[str, str]:
        """Classify a command/result pair against known categories."""
        return classify_interaction(
            cmd, result,
            self._act_categories,
            self._out_categories,
            self.classification_llm,
        )

    def _concretize_action(self, action_cat: str) -> str:
        """Map an abstract action category to a concrete example command.

        The concretization file maps action categories to lists of example commands.
        Returns the first useful example — skipping bare 'wait' which is useless advice.
        """
        def _first_useful(examples):
            if isinstance(examples, list):
                for ex in examples:
                    ex_str = str(ex).strip()
                    # Skip bare 'wait' — useless as a suggestion
                    if ex_str in ("wait", "wait 5", "wait 10", "wait 30"):
                        continue
                    return ex_str
                return examples[0] if examples else ""
            return str(examples) if examples else ""

        if action_cat in self._concretization:
            result = _first_useful(self._concretization[action_cat])
            if result:
                return result
        # Try fuzzy match
        for cat, cmds in self._concretization.items():
            if _label_similarity(action_cat, cat) > 0.7:
                result = _first_useful(cmds)
                if result:
                    return result
        return ""

    def _get_state_label(self, state) -> str:
        """Get the action portion of a state label, with fallbacks."""
        label = getattr(state, "output", "") or ""
        if label == "init":
            return "basic enumeration"
        label = label.replace("__success", "").replace("__fail", "")
        if "," in label:
            action = label.split(",", 1)[0].strip()
            if action:
                return action
        # Empty action — e.g., ",__success" means instant root with no command
        return "basic enumeration"

    def evaluate_step(self, actual_state) -> str:
        """Evaluate whether the agent followed the suggested path.

        Returns one of: "MATCH", "ALTERNATIVE", "MISMATCH", "FAIL", "SUCCESS"
        """
        if is_success_state(actual_state):
            return "SUCCESS"
        if is_fail_state(actual_state):
            return "FAIL"

        if self.suggested_state_id and actual_state.state_id == self.suggested_state_id:
            return "MATCH"

        # Check if the actual state is reachable from current via some transition
        current = self._get_current_state()
        if current:
            reachable_ids = {t.state_id for t, _ in current.transitions}
            if actual_state.state_id in reachable_ids:
                return "ALTERNATIVE"

        return "MISMATCH"

    def _get_current_state(self):
        """Get the current automaton state object."""
        for state in self._automaton.states:
            if state.state_id == self.current_state_id:
                return state
        return None

    def suggest(self, cmd: str, result: str) -> str:
        """Full pipeline: classify → find → evaluate → suggest next step.

        Returns feedback text to inject into the agent's prompt.
        """
        # 1. Classify
        action_cat, output_cat = self.classify(cmd, result)

        # Track tried actions to avoid cycles
        self._tried_actions.add(action_cat)

        # 2. Find matching state
        actual_state = find_closest_state(action_cat, output_cat, self._state_index)

        if actual_state is None:
            return "Continue enumeration and look for privilege escalation paths."

        # Update current position
        self.current_state_id = actual_state.state_id

        # 3. Evaluate
        verdict = self.evaluate_step(actual_state)

        # 4. Find best UNTRIED transition — avoid repeating suggestions
        best = self._pick_untried_transition(actual_state)
        if best is None:
            # All transitions lead to fail or already tried — reset to init state
            init = self._state_index.get("init")
            if init and init.state_id != actual_state.state_id:
                self._tried_transitions.clear()
                self.current_state_id = init.state_id
                best = find_best_transition(init, self._state_index)
            if best is None:
                return "The automaton has no known success path from here. Start fresh: try exec_command id to reset enumeration."
            target_state, prob = best
            target_action = self._get_state_label(target_state)
            concrete = self._concretize_action(target_action)
            self.suggested_state_id = target_state.state_id
            self.suggested_action = target_action
            return f"Dead end — resetting. Next: {target_action}" + (f" (try: {concrete})" if concrete else "")

        target_state, prob = best
        target_action = self._get_state_label(target_state)
        concrete = self._concretize_action(target_action)
        self._tried_transitions.add((actual_state.state_id, target_state.state_id))
        self.suggested_state_id = target_state.state_id
        self.suggested_action = target_action

        # 5. Build feedback
        verdict_msgs = {
            "MATCH": "Good, proceeding as expected.",
            "ALTERNATIVE": "That's a valid alternative path.",
            "MISMATCH": "That step doesn't match known success patterns. Redirecting.",
            "FAIL": "That path leads to failure. Try this instead.",
            "SUCCESS": "Root obtained!",
        }

        prefix = verdict_msgs.get(verdict, "")
        hint = f"Next: {target_action}"
        if concrete:
            hint += f" (try: {concrete})"
        # Compact exploration reminder — helps with credential/SUID discovery
        hint += " | Also: check bash_history, test found creds, look for SUID binaries"

        return f"{prefix} {hint}"

    def _pick_untried_transition(self, state) -> Optional[tuple]:
        """Pick the best untried transition FROM state, using the shared useful filter."""
        if not state.transitions:
            return None

        candidates = [(t, p) for t, p in sorted(state.transitions, key=lambda x: x[1], reverse=True)
                      if not is_fail_state(t) and _is_useful_state(t)]

        untried = [(t, p) for t, p in candidates
                    if (state.state_id, t.state_id) not in self._tried_transitions
                    and self._get_state_label(t) not in self._tried_actions]

        if untried:
            return untried[0]

        # All tried — clear and restart from top
        self._tried_transitions.clear()
        return candidates[0] if candidates else None

    def suggest_initial(self) -> str:
        """Generate the first-turn suggestion from the init state."""
        init = self._state_index.get("init")
        if init is None:
            return "Start with basic enumeration: exec_command id"

        best = find_best_transition(init, self._state_index)
        if best is None:
            return "Start with basic enumeration: exec_command id"

        target_state, prob = best
        target_action = self._get_state_label(target_state)
        concrete = self._concretize_action(target_action)
        self.suggested_state_id = target_state.state_id
        self.suggested_action = target_action

        hint = f"Start with: {target_action}"
        if concrete:
            hint += f" (try: {concrete})"
        return hint
