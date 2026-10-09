import subprocess
from dataclasses import dataclass, field
from typing import Tuple

from hackingBuddyGPT.utils.configurable import configurable


@configurable(
    "apptainer",
    "runs commands inside a persistent Apptainer/Singularity instance "
    "(Docker-free container runtime, for use on HPC clusters without root access)",
)
@dataclass
class ApptainerConnection:
    image: str = field(metadata={"help": "path to a .sif image, or a docker://... reference to pull"})
    instance_name: str = field(metadata={"help": "name of the Apptainer instance to start/attach to"})
    binary: str = field(default="singularity", metadata={"help": "container runtime binary (apptainer or singularity)"})
    workdir: str = field(default="", metadata={"help": "working directory inside the container for each command"})
    timeout: int = field(default=120, metadata={"help": "per-command timeout in seconds"})

    _started: bool = field(default=False, init=False)

    def init(self):
        if self._instance_running():
            self._started = True
            return
        subprocess.run(
            [self.binary, "instance", "start", self.image, self.instance_name],
            check=True, capture_output=True, text=True,
        )
        self._started = True

    def _instance_running(self) -> bool:
        result = subprocess.run(
            [self.binary, "instance", "list", self.instance_name],
            capture_output=True, text=True,
        )
        return self.instance_name in result.stdout

    def new_with(self, *, instance_name=None, image=None) -> "ApptainerConnection":
        return ApptainerConnection(
            image=image or self.image,
            instance_name=instance_name or self.instance_name,
            binary=self.binary,
            workdir=self.workdir,
            timeout=self.timeout,
        )

    def run(self, cmd, *args, **kwargs) -> Tuple[str, str, int]:
        if not self._started:
            self.init()

        full_cmd = f"cd {self.workdir} && {cmd}" if self.workdir else cmd
        try:
            result = subprocess.run(
                [self.binary, "exec", f"instance://{self.instance_name}", "bash", "-lc", full_cmd],
                capture_output=True, text=True, timeout=self.timeout,
            )
            return result.stdout, result.stderr, result.returncode
        except subprocess.TimeoutExpired:
            return "", f"command timed out after {self.timeout}s", 1

    def stop(self):
        subprocess.run([self.binary, "instance", "stop", self.instance_name], capture_output=True, text=True)
