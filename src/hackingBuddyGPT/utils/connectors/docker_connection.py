import subprocess
from dataclasses import dataclass, field
from typing import Optional, Tuple

from hackingBuddyGPT.utils.configurable import configurable


@configurable("docker", "runs commands inside a persistent Docker container")
@dataclass
class DockerConnection:
    image: str = field(metadata={"help": "Docker image reference, e.g. swebench/sweb.eval.x86_64.<instance>:latest"})
    container_name: str = field(metadata={"help": "name of the container to create or attach to"})
    binary: str = field(default="docker", metadata={"help": "container CLI binary"})
    shell_prefix: str = field(default="", metadata={"help": "shell snippet run before every command (e.g. activating a conda env)"})
    workdir: str = field(default="", metadata={"help": "working directory inside the container for each command"})
    timeout: int = field(default=120, metadata={"help": "per-command timeout in seconds"})

    _started: bool = field(default=False, init=False)

    def init(self):
        state = subprocess.run(
            [self.binary, "container", "inspect", "-f", "{{.State.Running}}", self.container_name],
            capture_output=True, text=True,
        )
        if state.returncode == 0:
            if state.stdout.strip() != "true":
                subprocess.run([self.binary, "start", self.container_name], check=True, capture_output=True)
        else:
            subprocess.run(
                [self.binary, "run", "-d", "--platform", "linux/amd64",
                 "--name", self.container_name, self.image, "sleep", "infinity"],
                check=True, capture_output=True,
            )
        self._started = True

    def run(self, cmd: str, input: Optional[str] = None) -> Tuple[str, str, int]:
        if not self._started:
            self.init()

        parts = [p for p in (self.shell_prefix, f"cd {self.workdir}" if self.workdir else "", cmd) if p]
        full_cmd = " && ".join(parts)

        # Bytes in and out: text mode on Windows would rewrite "\n" as "\r\n" and corrupt any patch sent via stdin.
        docker_cmd = [self.binary, "exec"]
        if input is not None:
            docker_cmd.append("-i")
        docker_cmd += [self.container_name, "bash", "-c", full_cmd]
        try:
            result = subprocess.run(
                docker_cmd,
                input=input.encode("utf-8") if input is not None else None,
                stdin=None if input is not None else subprocess.DEVNULL,
                capture_output=True,
                timeout=self.timeout,
            )
        except subprocess.TimeoutExpired:
            return "", f"command timed out after {self.timeout}s", 1
        return (
            result.stdout.decode("utf-8", errors="replace"),
            result.stderr.decode("utf-8", errors="replace"),
            result.returncode,
        )

    def stop(self):
        subprocess.run([self.binary, "rm", "-f", self.container_name], capture_output=True)
