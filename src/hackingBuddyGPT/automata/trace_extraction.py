"""Extract interaction sequences from pentesting run databases.

Refactored from create_abstract_traces.py — uses the RawDbStorage API instead of raw SQL,
and supports filtering by VM ID and iteration via structured tags.
"""

from collections import defaultdict

from hackingBuddyGPT.utils.db_storage.db_storage import RawDbStorage

# Default truncation length for command results in prompts
DEFAULT_OUT_LEN_LIMIT = 1000


def extract_sequences(
    db: RawDbStorage,
    vm_id: int | None = None,
    iteration: int | None = None,
    transfer: bool | None = None,
) -> dict[int, dict]:
    """Extract interaction sequences from a pentesting run database.

    Queries runs, messages, and tool_calls tables, groups messages by run_id,
    and pairs each assistant message with its tool call results.

    Args:
        db: The database storage instance.
        vm_id: Optional VM ID to filter runs by (parsed from tag).
        iteration: Optional iteration number to filter runs by (parsed from tag).
        transfer: Optional transfer flag to filter runs by (parsed from tag).

    Returns:
        Dict mapping run_id -> {"interactions": [...], "success": bool}.
        Runs still "in progress" are excluded.
    """
    # 1. Load runs (filtered)
    runs = db.get_runs_filtered(vm_id=vm_id, iteration=iteration, transfer=transfer)

    # Filter out runs still in progress
    run_states = {
        run.id: (run.state == "got root")
        for run in runs
        if run.state != "in progress"
    }

    if not run_states:
        return {}

    run_ids = list(run_states.keys())

    # 2. Load messages for all filtered runs
    messages_raw = db.get_messages_by_run_ids(run_ids)

    # Group messages by run_id
    runs_msgs = defaultdict(list)
    for msg in messages_raw:
        runs_msgs[msg.run_id].append({
            "id": msg.id,
            "role": msg.role,
            "content": msg.content,
        })

    # 3. Load tool calls for all filtered runs
    tool_calls_raw = db.get_tool_calls_by_run_ids(run_ids)

    # Group tool calls by (run_id, message_id)
    tool_map = defaultdict(list)
    for tc in tool_calls_raw:
        tool_map[(tc.run_id, tc.message_id)].append({
            "function": tc.function_name,
            "arguments": tc.arguments,
            "result": tc.result_text,
        })

    # 4. Build interaction pairs
    result = {}
    for run_id, messages in runs_msgs.items():
        if run_id not in run_states:
            continue
        interactions = []
        i = 0

        while i < len(messages) - 1:
            if messages[i]["role"] != "assistant" and messages[i + 1]["role"] == "assistant":
                assistant_msg = messages[i + 1]
                msg_id = assistant_msg["id"]

                tools = tool_map.get((run_id, msg_id), [])

                interactions.append({
                    "input": messages[i]["content"],
                    "output": assistant_msg["content"],
                    "action": tools[0]["function"] if tools else None,
                    "arguments": tools[0]["arguments"] if tools else None,
                    "result": tools[0]["result"] if tools else None,
                })
                i += 2
            else:
                i += 1

        result[run_id] = {
            "interactions": interactions,
            "success": run_states.get(run_id, False),
        }

    return result


def build_concretization(
    db: RawDbStorage,
    abstractions_data: dict,
    vm_id: int | None = None,
    iteration: int | None = None,
) -> dict[str, list[str]]:
    """Map abstract action categories to their most frequent concrete commands.

    For each abstract category in the abstractions data, looks up the actual
    shell commands that were executed in the corresponding trace positions,
    ranks them by frequency, and returns the top 2-3.

    Args:
        db: The database storage instance.
        abstractions_data: Dict with "traces" key from abstractions.json.
        vm_id: Optional VM ID filter.
        iteration: Optional iteration filter.

    Returns:
        Dict mapping abstract action category → list of concrete command strings.
    """
    from collections import defaultdict, Counter

    # Build abstract → concrete mapping: for each trace, walk steps and
    # collect the corresponding tool call arguments from the DB.
    abstract_to_commands: dict[str, list[str]] = defaultdict(list)

    traces = abstractions_data.get("traces", [])
    if not traces:
        return {}

    # Get all runs for this VM/iteration to look up tool calls
    runs = extract_sequences(db, vm_id=vm_id, iteration=iteration)
    if not runs:
        return {}

    # For each trace (which maps to one run), walk the abstract steps
    # and look up the corresponding tool call
    trace_list = list(traces)
    run_list = list(runs.items())

    for trace_idx, trace in enumerate(trace_list):
        if trace_idx >= len(run_list):
            break
        run_id, run_data = run_list[trace_idx]
        interactions = run_data["interactions"]

        sorted_items = sorted(trace.items(), key=lambda x: int(x[0]))
        for step_key, step_value in sorted_items:
            if not isinstance(step_value, (list, tuple)) or len(step_value) < 2:
                continue  # skip terminal state ("success"/"fail")
            action_cat = step_value[0]
            try:
                step_idx = int(step_key)
            except ValueError:
                continue
            if step_idx < len(interactions):
                interaction = interactions[step_idx]
                # Build a concrete command string
                func = interaction.get("action") or ""
                args = interaction.get("arguments") or ""
                if func and args:
                    cmd = f"{func} {args}"
                elif func:
                    cmd = func
                elif args:
                    cmd = args
                else:
                    cmd = "(empty)"
                abstract_to_commands[action_cat].append(cmd)

    # Rank and take top 3 per category
    result = {}
    for abstract_cat, commands in abstract_to_commands.items():
        ranked = Counter(commands).most_common(3)
        result[abstract_cat] = [cmd for cmd, _ in ranked]

    return result
