"""Shared dataclasses for the automata learning pipeline."""

from dataclasses import dataclass, field


@dataclass
class Interaction:
    """A single interaction step: the agent's output, the action taken, and the result."""
    input: str       # the system/user prompt content
    output: str      # the assistant's response
    action: str | None   # the tool function name (e.g., "exec_command")
    arguments: str | None  # arguments to the tool
    result: str | None     # the result of the tool call


@dataclass
class RunData:
    """All interactions for a single pentesting run, plus success flag."""
    interactions: list[Interaction]
    success: bool


@dataclass
class AbstractionsFile:
    """The full abstractions.json schema."""
    act_categories: list[str]
    out_categories: list[str]
    traces: list[dict]  # list of {str(int): [action_cat, out_cat]} dicts with terminal "success"/"fail"
