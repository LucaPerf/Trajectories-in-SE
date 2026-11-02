def semantic(out_len_limit, actions, act_categories, out_categories) -> str:
    return f"""We are analyzing interactions of an autonomous software-engineering agent.
The agent works inside a checked-out Python repository and tries to resolve a GitHub issue (fix a bug)
by running shell commands: it can search and read code, edit files, run scripts and tests, and finally
it submits its patch for verification.
I will provide you with a list of actions performed by the agent
and the corresponding output of the environment (truncated after {out_len_limit} characters).
Match each action with an abstract action category and each output with an abstract output category.

An action category describes what kind of step the agent performed, and has the form OPERATION (SLOT).

- OPERATION is a single word, of your own choice, that names what kind of step the agent performed.
- SLOT is 3 to 6 words that make the operation more concrete by combining an action, an object and a scope:
  the action says what is done, the object says what type of thing it is done on, and the scope says how wide
  the step is (for example a single file, a directory, the whole repository).
  Every action category MUST contain both parts.
  An operation without a SLOT is invalid.

The category must stay general enough to be recognized in a DIFFERENT repository and on a DIFFERENT issue.
Test for every SLOT: "in another repository, would this value be different?" If yes, it is a specific value
and must NOT appear. Describe the type of the thing, never the thing itself.

What the SLOT should say, depending on the operation:
- For steps that look for something, the object is the KIND of thing looked for.
  Never use vague words such as string, text, code or content as the object.
- For steps that read, the object is how much is read, for example whole file, line range, directory listing.
- For steps that change files, the SLOT says HOW the change is applied, for example rewrite whole file,
  replace line range, insert lines. Do not name the language construct that is changed (no method, class, function).
- For steps that run something, the object is what is run, for example test suite, single test, reproduction script.

Rules for the SLOT:
- NEVER include file names, paths, function or class names, variable names, or searched strings.
- NEVER include the tool or flags of the command (no grep, sed, pytest, -n, -R, ...).
- NEVER include commas, slashes, arrows (->), quotes, or nested parentheses.
- The action in the SLOT must make the OPERATION more precise, not repeat it.
- Describe only what this single command does; do not say whether something was already seen before.
- Use the same wording for the same kind of step every time, so that equivalent steps get identical categories.

Granularity:
- Keep few distinct operations overall (roughly 5 to 8).
- Prefer reusing existing categories. Only introduce a new one if none fits semantically.
- Do not introduce categories that are minor variations of existing ones.

Illustration of the format on an unrelated domain (a person repairing a bicycle), NOT to be reused as categories:
- Inspect (check brake pads on rear wheel)
- Inspect (look for cracks in whole frame)
- Replace (swap worn part on front wheel)
- Test (ride bicycle on flat road)
- Finish (hand over repaired bicycle)

Match outputs with abstract categories based on their usefulness for resolving the issue.

Use two components:

1. VALUE (usefulness of the output):
- EMPTY (no output, nothing found)
- ERROR (the command failed: traceback, syntax error, file not found, ...)
- INFO (informational but not directly useful)
- DISCOVERY (reveals something new and relevant, e.g. where the bug is or how the code works)
- PROGRESS (shows that the fix works or moves toward it: an edit was applied without errors, the issue no longer reproduces, tests pass)
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

Examples: DISCOVERY_SOURCE, INFO_REPO, PROGRESS_TEST, ERROR_NONE, EMPTY_NONE, REPEATED_SOURCE, PROGRESS_PATCH

Only use combinations that make sense and be as specific as you deem necessary to describe the strategy that leads to a fix.
Output categories MUST use the <VALUE>_<TARGET> format.
A command that modifies files and prints nothing, or prints no error, is PROGRESS_PATCH, never EMPTY.
EMPTY is only for searches or reads that found nothing.

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

PROMPTS = {
    "semantic": semantic,
    #"template": template,
    #"template_values": template_values,
    #"hybrid": hybrid,
}