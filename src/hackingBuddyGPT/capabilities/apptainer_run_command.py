from dataclasses import dataclass

from hackingBuddyGPT.capability import Capability
from hackingBuddyGPT.utils.connectors.apptainer_connection import ApptainerConnection


@dataclass
class ApptainerRunCommand(Capability):
    conn: ApptainerConnection

    def describe(self) -> str:
        return (
            "give a command to be executed and I will respond with the terminal output when "
            "running this command inside the task's Apptainer container. The given command must "
            "not require user interaction. Do not use quotation marks in front and after your command."
        )

    def get_name(self):
        return "exec_command"

    def __call__(self, command: str) -> str:
        stdout, stderr, returncode = self.conn.run(command)
        output = stdout
        if stderr:
            output += f"\n[stderr]\n{stderr}"
        if returncode != 0:
            output += f"\n[exit code: {returncode}]"
        return output or "(no output)"
