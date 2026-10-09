"""Abstract concrete agent-environment interactions into categorical representations via LLM.

Refactored from create_abstract_traces.py. All LLM calls use injected OpenAIConnection instances
instead of hardcoded API keys and URLs.
"""

import re

from hackingBuddyGPT.utils.llm_util import LLM

# Default truncation length for command results in prompts
DEFAULT_OUT_LEN_LIMIT = 1000

# Maximum retries when the LLM returns malformed / unparseable output
MAX_ABSTRACTION_RETRIES = 2


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
    input_precise: bool = True,
    output_precise: bool = False,
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

    prompt = f"""We are analyzing interactions of an autonomous software-engineering agent.
The agent works inside a checked-out Python repository and tries to resolve a GitHub issue (fix a bug)
by running shell commands: it searches and reads code, edits files, runs scripts and tests, and finally
submits its patch for verification.
I will provide you with a list of actions performed by the agent
and the corresponding output of the environment (truncated after {out_len_limit} characters).
Match the actions performed by the agent with abstract categories.

Typical action categories include:
- search codebase
- inspect repository structure
- read source file
- edit source file
- run existing tests
- run reproduction script
- submit patch

Prefer reusing existing categories. Only introduce a new category if none fits semantically.
Do not introduce categories that are minor variations of existing ones.

Match outputs with abstract categories based on their usefulness for resolving the issue.

Use two components:

1. VALUE (usefulness of the output):
- EMPTY (no output, nothing found)
- ERROR (the command failed: traceback, syntax error, file not found, ...)
- INFO (informational but not directly useful)
- DISCOVERY (reveals something new and relevant, e.g. where the bug is or how the code works)
- PROGRESS (shows that the fix works or moves toward it: an edit was applied, the issue no longer reproduces, tests pass)
- REPEATED (same or equivalent result as before)

2. TARGET TYPE (what the output relates to):
- NONE (no specific target)
- REPO (repository layout, file lists)
- SOURCE (source code)
- TEST (tests and test results)
- ISSUE (the behaviour described in the issue)
- PATCH (the change made by the agent)
- etc.

Combine them into a single category using the format:
<VALUE>_<TARGET>

Examples:
- DISCOVERY_SOURCE
- INFO_REPO
- PROGRESS_TEST

Only use combinations that make sense and be as specific as you deem necessary to describe the strategy that leads to a fix.
CRITICAL FORMATTING RULES:
- Output categories MUST use <VALUE>_<TARGET> format. Examples of valid output categories:
  DISCOVERY_SOURCE, INFO_REPO, ERROR_NONE, PROGRESS_TEST, PROGRESS_ISSUE, EMPTY_NONE, REPEATED_SOURCE, PROGRESS_PATCH
- Action categories MUST be multi-word descriptive phrases. Examples of valid action categories:
  "search codebase (grep)", "read source file (sed)", "edit source file (sed -i)", "run existing tests (pytest)", "run reproduction script (python -c)", "submit patch"
- NEVER output single generic words. These are INVALID: "search", "read", "edit", "test", "error", "file", "none", "command", "execution", "output", "Command Output"
{"If a specific target is especially relevant, such as the file or function that contains the bug, you may specify it concretely, but enclose it in parentheses(). " if output_precise else ""}{"If there are specific action aspects, like a command with an important argument, you may specify them concretely more concretely, but enclose them in parentheses(). " if input_precise else ""}

Return EXACTLY (comma-separated lists in curly braces):
{{action categories}}
{{output categories}}
Do not include any additional text.

Actions performed by the agent with results:
{actions}
Existing categories:
{{ {','.join(sorted(act_categories))} }}
{{ {','.join(sorted(out_categories))} }}
"""

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

    Raises:
        ValueError: If the LLM output cannot be parsed.
    """
    # If there are very many categories the prompt overflows context and the
    # LLM returns empty.  Cap to a representative sample (the sorted order is
    # stable, so repeated runs with the same categories get the same sample).
    MAX_CATS_FOR_NORMALIZE = 40
    sorted_act = sorted(list(act_categories))
    sorted_out = sorted(list(out_categories))
    total_cats = len(sorted_act) + len(sorted_out)
    if total_cats > MAX_CATS_FOR_NORMALIZE:
        # Sample evenly from both lists
        max_each = MAX_CATS_FOR_NORMALIZE // 2
        if len(sorted_act) > max_each:
            step = len(sorted_act) / max_each
            sorted_act = [sorted_act[int(i * step)] for i in range(max_each)]
        if len(sorted_out) > max_each:
            step = len(sorted_out) / max_each
            sorted_out = [sorted_out[int(i * step)] for i in range(max_each)]
        print(f"Normalize: capped {total_cats} categories to {len(sorted_act) + len(sorted_out)} for LLM call")

    prompt = f"""Normalize the following categories by merging duplicates and semantically equivalent ones.
Do NOT over-merge. The categories are used to abstractly reason about the strategy of a software-engineering
agent that resolves a GitHub issue, so keep the categories that distinguish different steps of a fix
(searching, reading, editing, running tests, submitting).

Return EXACTLY this format, i.e., one set of action categories and one set of output categories:

$START$
{{action1, action2, ...}}
{{output1, output2, ...}}
$END$

Action categories:
{sorted_act}

Output categories:
{sorted_out}
"""

    for attempt in range(MAX_ABSTRACTION_RETRIES + 1):
        response = llm.get_response(prompt).result

        print(f"Normalization response (attempt {attempt + 1}): {response}")

        # Extract the $START$...$END$ block
        match = re.search(r"\$START\$(.*?)\$END\$", response, re.DOTALL)
        if not match:
            if attempt < MAX_ABSTRACTION_RETRIES:
                prompt = (
                    f"Your last response was malformed — it did not contain the required "
                    f"$START$ and $END$ delimiters.  You MUST return EXACTLY:\n"
                    f"$START$\n"
                    f"{{action1, action2, ...}}\n"
                    f"{{output1, output2, ...}}\n"
                    f"$END$\n\n"
                    f"Now re-examine and normalize these categories:\n"
                    f"Action categories:\n{sorted(list(act_categories))}\n\n"
                    f"Output categories:\n{sorted(list(out_categories))}"
                )
                continue
            raise ValueError("Invalid LLM output format: missing $START$...$END$ delimiters")

        block = match.group(1)
        sets = re.findall(r"\{([^}]*)\}", block)

        if len(sets) < 2:
            if attempt < MAX_ABSTRACTION_RETRIES:
                prompt = (
                    f"Your last response was malformed — could not find both category sets. "
                    f"You MUST return EXACTLY two curly-brace sets after $START$:\n"
                    f"$START$\n"
                    f"{{action1, action2, ...}}\n"
                    f"{{output1, output2, ...}}\n"
                    f"$END$\n\n"
                    f"Now re-examine these categories:\n"
                    f"Action categories:\n{sorted(list(act_categories))}\n\n"
                    f"Output categories:\n{sorted(list(out_categories))}"
                )
                continue
            raise ValueError("Could not extract both category sets from LLM output")

        new_act_categories = {x.strip() for x in sets[0].split(",") if x.strip()}
        new_out_categories = {x.strip() for x in sets[1].split(",") if x.strip()}
        return new_act_categories, new_out_categories

    raise ValueError("All normalization retries exhausted")


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
        if not line or ":" not in line:
            continue
        id_str, category = line.split(":", 1)
        try:
            idx = int(id_str.strip())
        except ValueError:
            continue
        split_cat = category.strip().split("->")
        if len(split_cat) >= 2:
            result[idx] = (split_cat[0].strip(), split_cat[1].strip())
        elif len(split_cat) == 1:
            result[idx] = (split_cat[0].strip(), "")

    # Fallback parser: if primary produced nothing, scan for assignment patterns
    # anywhere in the raw text (handles missing / malformed delimiters).
    if not result:
        for m in _ASSIGNMENT_LINE.finditer(text):
            idx = int(m.group(1))
            result[idx] = (m.group(2).strip(), m.group(3).strip())

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

    prompt = f"""We are analyzing interactions of an autonomous software-engineering agent that tries to resolve a GitHub issue in a Python repository, and you should help us in doing so.
I will provide you with a list of actions performed by the agent and the corresponding output of the environment (truncated after {out_len_limit} characters).
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

Your task is to assign the actions performed by the agent to an action category and the output to an output category.
Use the following syntax
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
