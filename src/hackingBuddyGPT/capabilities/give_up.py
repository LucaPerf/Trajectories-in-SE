from dataclasses import dataclass

from hackingBuddyGPT.capability import Capability


@dataclass
class GiveUp(Capability):
    """Lets the model declare that it cannot resolve the issue. The run then stops with its own
    final state ("gave up: <reason>"), so a failed run can be told apart from one that simply ran
    out of turns without reading the whole transcript.
    """

    def describe(self) -> str:
        return (
            "Call this only when you are convinced you cannot resolve the issue (for example after "
            "several failed submissions, or when every approach you tried was ruled out). The run "
            "ends immediately. Usage: give_up <short reason why you cannot fix it>"
        )

    def get_name(self):
        return "give_up"

    def __call__(self, reason: str) -> str:
        return "GAVE_UP"
