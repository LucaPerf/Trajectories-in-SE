from dataclasses import dataclass

from hackingBuddyGPT.capability import Capability
from hackingBuddyGPT.utils.connectors.docker_connection import DockerConnection

MAX_OUTPUT_CHARS = 10000


def _truncate(text: str) -> str:
    if len(text) <= MAX_OUTPUT_CHARS:
        return text
    half = MAX_OUTPUT_CHARS // 2
    return f"{text[:half]}\n...[{len(text) - MAX_OUTPUT_CHARS} characters truncated]...\n{text[-half:]}"


@dataclass
class DockerRunCommand(Capability):
    conn: DockerConnection

    def describe(self) -> str:
        return (
            "give a command to be executed and I will respond with the terminal output when "
            "running this command inside the task's container. The given command must "
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
        return _truncate(output) or "(no output)"
