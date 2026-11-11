"""Abstract concrete agent-environment interactions into categorical representations via LLM.

Refactored from create_abstract_traces.py. All LLM calls use injected OpenAIConnection instances
instead of hardcoded API keys and URLs.
"""

import re
import os
from hackingBuddyGPT.utils.llm_util import LLM
from hackingBuddyGPT.automata.prompts_variants import PROMPTS


# Default truncation length for command results in prompts
DEFAULT_OUT_LEN_LIMIT = 1000

# Maximum retries when the LLM returns malformed / unparseable output
MAX_ABSTRACTION_RETRIES = 2

VARIANT = os.environ.get("PROMPT_VARIANT", "semantic")
if VARIANT not in PROMPTS:
    raise ValueError(f"PROMPT_VARIANT must be one of {list(PROMPTS)}, got '{VARIANT}'")

def _extract_set_from_response(s: str) -> set[str]:
    """Extract a comma-separated set from the first curly-brace group in a string."""
    match = re.search(r"\{([^}]*)\}", s)
    if not match:
        return set()
    content = match.group(1)
    # Strip surrounding quotes and whitespace from each item
    return {item.strip().strip("'\"") for item in content.split(",") if item.strip().strip("'\"")}


# Fallback regex for parsing assignment lines when $START$...$END$ is missing.
# Matches lines like "0: action category -> output category".  Excludes lines
# that contain shell-command artefacts (slashes, quotes, semicolons, pipes) to
# avoid false-positives on echoed action lines from the prompt.
_ASSIGNMENT_LINE = re.compile(
    r"^(\d+)\s*:\s*([^/\n]{2,60})\s*->\s*([^/\n]{2,60})\s*$",
    re.MULTILINE,
)


def categorize_interactions(
    interactions: list[dict],
    act_categories: set[str],
    out_categories: set[str],
    llm: LLM,
    *,
    out_len_limit: int = DEFAULT_OUT_LEN_LIMIT,
) -> tuple[set[str], set[str]]:
    """Use an LLM to discover abstract categories for actions and outputs.

    Sends a batch of interactions to the LLM and asks it to match them to abstract
    categories. Prefers reusing existing categories; only introduces new ones if
    none fits semantically.

    Args:
        interactions: List of interaction dicts with "output" and "result" keys.
        act_categories: Existing set of action category strings (updated in-place).
        out_categories: Existing set of output category strings (updated in-place).
        llm: The LLM connection to use for categorization.
        input_precise: If True, allow parenthetical specifics in action categories.
        output_precise: If True, allow parenthetical specifics in output categories.
        out_len_limit: Truncate results to this many characters.

    Returns:
        Tuple of (updated act_categories, updated out_categories).
    """
    if len(interactions) == 0:
        return act_categories, out_categories

    # Build the serialized list of actions
    action_strings = []
    for i, interaction in enumerate(interactions):
        action = interaction["output"]
        result = (interaction["result"] or "")[:out_len_limit]
        action_strings.append(f"{i}:{action} -> {result}")
    actions = "#!#\n".join(action_strings)

    prompt = PROMPTS[VARIANT](out_len_limit, actions, act_categories, out_categories)

    for attempt in range(MAX_ABSTRACTION_RETRIES + 1):
        categories_raw = llm.get_response(prompt).result.strip()
        print(f"Response to categories (attempt {attempt + 1}):")
        print(categories_raw)

        brace_count = categories_raw.count('}')
        if brace_count >= 2:
            end_of_act = categories_raw.index('}')
            new_act_cats = _extract_set_from_response(categories_raw[:end_of_act + 1])
            act_categories.update(new_act_cats)
            new_out_cats = _extract_set_from_response(categories_raw[end_of_act + 1:])
            out_categories.update(new_out_cats)
            return act_categories, out_categories

        # Salvage truncated responses: if we have at least one complete set,
        # use it for action categories and keep existing output categories.
        if brace_count == 1:
            new_act_cats = _extract_set_from_response(categories_raw)
            act_categories.update(new_act_cats)
            print(f"Salvaged {len(new_act_cats)} action categories from truncated response")
            return act_categories, out_categories

        print(f"Malformed response (attempt {attempt + 1})")
        if attempt < MAX_ABSTRACTION_RETRIES:
            # DO NOT re-send the full actions list on retry — it makes the prompt
            # longer each time and causes empty-response spirals.
            prompt = (
                f"Your last response was malformed — it did not contain two curly-brace "
                f"sets.  Return ONLY two lines in this exact format:\n"
                f"{{action_category_1, action_category_2, ...}}\n"
                f"{{output_category_1, output_category_2, ...}}\n\n"
                f"Use existing categories where possible:\n"
                f"{{ {','.join(sorted(act_categories))} }}\n"
                f"{{ {','.join(sorted(out_categories))} }}"
            )

    # All retries exhausted — return existing categories unchanged
    print("All categorization retries exhausted")
    return act_categories, out_categories


def normalize_categories(
    act_categories: set[str],
    out_categories: set[str],
    llm: LLM,
) -> tuple[set[str], set[str]]:
    """Use an LLM to merge semantically duplicate or equivalent categories.

    Args:
        act_categories: Current set of action categories.
        out_categories: Current set of output categories.
        llm: The LLM connection to use for normalization.

    Returns:
        Tuple of (normalized act_categories, normalized out_categories).
        If no valid answer is obtained after all retries, the input categories are returned unchanged.
    """
    # All categories are sent: the result replaces the whole set, so sampling
    # only some of them (as done before) silently dropped the others.
    sorted_act = sorted(list(act_categories))
    sorted_out = sorted(list(out_categories))
    print(f"Normalize: sending {len(sorted_act)} action and {len(sorted_out)} output categories to the LLM")

    def _listing(categories: list[str]) -> str:
        # one per line, without the quotes and escaping of a Python list
        return "\n".join(f"- {c}" for c in categories)

    base_prompt = f"""Normalize the following categories by merging duplicates and semantically equivalent ones.
The categories were produced independently on different runs of the same kind of agent,
so many of them describe the same step in different words.
Do NOT over-merge. The categories are used to abstractly reason about the strategy of a software-engineering
agent that resolves a GitHub issue, so keep the categories that distinguish different steps of a fix
(searching, reading, editing, running tests, submitting).

Action categories have the form OPERATION (SLOT).
Output categories have the form <VALUE>_<TARGET>.

Rules:
- Keep the format. Never remove the SLOT and never reduce an action category to its OPERATION alone.
  Never remove the VALUE or the TARGET from an output category.
- Merge two categories if the agent does the same kind of step, on the same kind of thing, with the same extent,
  and they differ only in wording, in a synonym, or in a level of detail that would not change what the agent does next.
- Do not merge categories that describe genuinely different steps (a different kind of action,
  a different kind of thing acted on, or a different extent).
- Choose each merged category among the input categories. Do not invent new categories. Do not use quotes.

Return EXACTLY this format, i.e., one set of action categories and one set of output categories:

$START$
{{action1, action2, ...}}
{{output1, output2, ...}}
$END$

Action categories:
{_listing(sorted_act)}

Output categories:
{_listing(sorted_out)}
"""

    def _clean(item: str) -> str:
        return item.strip().strip("'\"")

    prompt = base_prompt
    for attempt in range(MAX_ABSTRACTION_RETRIES + 1):
        response = llm.get_response(prompt).result or ""

        print(f"Normalization response (attempt {attempt + 1}): {response}")

        problem = None
        match = re.search(r"\$START\$(.*?)\$END\$", response, re.DOTALL)
        if not match:
            problem = "it was empty or did not contain the required $START$ and $END$ delimiters"
        else:
            sets = re.findall(r"\{([^}]*)\}", match.group(1))
            if len(sets) < 2:
                problem = "it did not contain both category sets"
            else:
                new_act_categories = {c for c in map(_clean, sets[0].split(",")) if c}
                new_out_categories = {c for c in map(_clean, sets[1].split(",")) if c}
                # the prompt asks to choose among the input categories: anything else was invented
                invented = (new_act_categories - act_categories) | (new_out_categories - out_categories)
                if invented:
                    problem = f"it contained categories that are not among the given ones: {sorted(invented)}"
                elif (act_categories and not new_act_categories) or (out_categories and not new_out_categories):
                    problem = "one of the two sets was empty"
                else:
                    return new_act_categories, new_out_categories

        print(f"Normalization response rejected (attempt {attempt + 1}): {problem}")
        # the retry repeats the full prompt, so it is never less strict than the first attempt
        prompt = (
            f"Your previous answer was rejected because {problem}.\n"
            f"Answer again, following all the instructions below.\n\n{base_prompt}"
        )

    print("WARNING: normalization failed after all retries, keeping the categories unchanged")
    return set(act_categories), set(out_categories)


def _clean_cat(s: str) -> str:
    """Remove the #!# separator the model copies from the prompt, plus stray quotes and spaces."""
    return s.replace("#!#", "").strip().strip("'\"").strip()


def _parse_assignments(text: str) -> dict[int, tuple[str, str]]:
    """Parse assignment lines from an LLM response.

    First tries the primary $START$...$END$ block format.  If that yields nothing,
    falls back to a regex that finds `<id>:<action> -> <output>` patterns anywhere
    in the text (handles missing / malformed delimiters).
    """
    # Primary parser: $START$...$END$ block
    start, end = "$START$", "$END$"
    block = ""
    if start in text and end in text:
        block = text.split(start, 1)[1].split(end, 1)[0].strip()

    result: dict[int, tuple[str, str]] = {}
    for line in block.splitlines():
        line = line.strip()
        # the model sometimes copies the (...)* of the syntax in the prompt and wraps each line in parentheses
        if line.startswith("("):
            line = line[1:].strip()
            if line.endswith(")"):
                line = line[:-1].strip()
        if not line or ":" not in line:
            continue
        id_str, category = line.split(":", 1)
        try:
            idx = int(id_str.strip())
        except ValueError:
            continue
        split_cat = category.strip().split("->")
        if len(split_cat) >= 2:
            # output categories never contain parentheses: a trailing one closes a group opened on an earlier line
            result[idx] = (_clean_cat(split_cat[0]), _clean_cat(split_cat[1]).rstrip(") "))
        elif len(split_cat) == 1:
            result[idx] = (_clean_cat(split_cat[0]), "")

    # Fallback parser: if primary produced nothing, scan for assignment patterns
    # anywhere in the raw text (handles missing / malformed delimiters).
    if not result:
        for m in _ASSIGNMENT_LINE.finditer(text):
            idx = int(m.group(1))
            result[idx] = (_clean_cat(m.group(2)), _clean_cat(m.group(3)))

    return result


def abstract_sequence(
    interactions: list[dict],
    act_categories: set[str],
    out_categories: set[str],
    run_fail: bool,
    llm: LLM,
    *,
    out_len_limit: int = DEFAULT_OUT_LEN_LIMIT,
) -> dict[int, tuple[str, str] | str]:
    """Use an LLM to assign each interaction to an (action_category, output_category) pair.

    Retries with a correction prompt if the LLM response is malformed (missing
    assignments or wrong number of entries).

    Args:
        interactions: List of interaction dicts.
        act_categories: Set of abstract action categories.
        out_categories: Set of abstract output categories.
        run_fail: True if this run did not solve the task (the tests did not pass).
        llm: The LLM connection to use for abstraction.
        out_len_limit: Truncate results to this many characters.

    Returns:
        Dict mapping interaction index to either:
        - A tuple (action_category, output_category) for real interactions
        - The string "success" or "fail" for the terminal state
    """
    if len(interactions) == 0:
        # No interactions — terminal state only
        abstracted: dict[int, tuple[str, str] | str] = {}
        max_id = 0
        abstracted[max_id + 1] = "fail" if run_fail else "success"
        return abstracted

    # Build serialized action list (reused across retries)
    action_strings = []
    for i, interaction in enumerate(interactions):
        action = interaction["output"]
        result = (interaction["result"] or "")[:out_len_limit]
        action_strings.append(f"{i}:{action} -> {result}")
    actions = "#!#\n".join(action_strings)

    cat_block = (
        f"{{ {','.join(sorted(act_categories))} }}\n"
        f"{{ {','.join(sorted(out_categories))} }}"
    )

    prompt = f"""We are analyzing interactions of an autonomous software-engineering agent that tries to resolve a GitHub issue in a Python repository.
The agent has two tools: exec_command (runs a shell command in the repository) and submit_patch (hands the patch over to be verified by the project's test suite).
I will provide you with a list of actions performed by the agent and the corresponding output of the environment (truncated after {out_len_limit} characters).
Each action starts with the name of the tool that was used.
Additionally, I provide a set of action categories and a set of output categories. The input format is
ACTIONS:
(<id>:<action>-><output>#!#\\n)*
CATEGORIES:
{{(<action category>,)*}}
{{(<output category>,)*}}

ACTIONS:
{actions}
CATEGORIES:
{cat_block}

Your task is to assign every action to exactly one action category and its output to exactly one output category.

Rules for the action category:
- Choose only among the given action categories and write them exactly as given, word for word.
- Choose the category that describes what this single command does, judging only from the command itself.
- If several categories fit, choose the most specific one.
- Never assign to an action a category that describes a step of the other tool.

Rules for the output category:
- Choose only among the given output categories and write them exactly as given.
- An output category has the form <VALUE>_<TARGET>. Judge it from the output of the environment, using these definitions.
  VALUE (usefulness of the output):
  - EMPTY: no output, nothing found
  - ERROR: the command failed or the tests failed (traceback, syntax error, file not found, failing tests, ...)
  - INFO: informational but not directly useful
  - DISCOVERY: reveals something new and relevant, e.g. where the bug is or how the code works
  - PROGRESS: shows that the fix works or moves toward it: an edit was applied without errors, the issue no longer reproduces, tests pass
  - REPEATED: same or equivalent result as an earlier step in this sequence
  TARGET (what the output relates to): the part of the category after the underscore, e.g. source code, tests, the patch, the repository layout, no specific target.
- A command that modifies files and prints nothing, or prints no error, has VALUE PROGRESS, never EMPTY.
  EMPTY is only for searches or reads that found nothing.
- If no given output category fits exactly, choose the closest one. Do not invent new categories.

Use the following syntax, one line per action, in the same order, and nothing else
$START$
(<id>:<action category> -> <output category>\\n)*
$END$
Your task is just to abstract away information so that we can analyze the strategies of the agent.
"""

    expected_count = len(interactions)

    for attempt in range(MAX_ABSTRACTION_RETRIES + 1):
        response = llm.get_response(prompt).result

        if attempt == 0:
            print(f"Abstraction prompt: {prompt}")
        print(f"Raw abstraction response (attempt {attempt + 1}): {response}")

        abstracted = _parse_assignments(response)

        # Count non-terminal entries (tuples, not strings)
        parsed_count = sum(1 for v in abstracted.values() if isinstance(v, tuple))

        if parsed_count >= expected_count:
            # Success — got at least as many assignments as interactions
            break

        print(f"Parsed only {parsed_count}/{expected_count} assignments (attempt {attempt + 1})")

        if attempt < MAX_ABSTRACTION_RETRIES:
            prompt = (
                f"Your last response was malformed — it did not contain assignments for "
                f"all {expected_count} interactions.  You MUST output EXACTLY one line per "
                f"interaction using this format:\n"
                f"$START$\n"
                f"0:action_category -> output_category\n"
                f"1:action_category -> output_category\n"
                f"...\n"
                f"$END$\n\n"
                f"Here are the interactions again:\n{actions}\n\n"
                f"Available categories:\n{cat_block}"
            )

    # Add terminal state
    max_id = max(abstracted.keys()) if abstracted else len(interactions)
    if run_fail:
        abstracted[max_id + 1] = "fail"
    else:
        abstracted[max_id + 1] = "success"

    return abstracted
