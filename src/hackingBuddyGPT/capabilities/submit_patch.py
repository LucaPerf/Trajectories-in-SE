from dataclasses import dataclass

from hackingBuddyGPT.capability import Capability
from hackingBuddyGPT.utils.connectors.docker_connection import DockerConnection


@dataclass
class SubmitPatch(Capability):
    """The SWE-bench equivalent of capabilities/submit_flag.py: a single, unambiguous
    success signal for a run, kept separate from ordinary shell output so that
    check_success() doesn't have to guess at test-runner output.

    SWE-bench's FAIL_TO_PASS tests come from a separate test_patch, not from the repo at the
    buggy commit. So the patch is applied only for the duration of this check (sent through
    stdin, never left in the container) and reverted right after, keeping the tests hidden
    from the agent.
    """

    conn: DockerConnection
    test_cmd: str
    test_patch: str = ""

    def describe(self) -> str:
        return (
            "Call this when you believe the issue is fixed. I will run the project's test suite "
            "inside the container and tell you whether it passes. "
            "Usage: submit_patch <short note about what you changed>"
        )

    def get_name(self):
        return "submit_patch"

    def __call__(self, note: str) -> str:
        if self.test_patch:
            script = (
                "cat > /tmp/swe_test.patch && "
                "git apply /tmp/swe_test.patch && "
                f"({self.test_cmd}); rc=$?; "
                "git apply -R /tmp/swe_test.patch; rm -f /tmp/swe_test.patch; exit $rc"
            )
            stdout, stderr, returncode = self.conn.run(script, input=self.test_patch)
        else:
            stdout, stderr, returncode = self.conn.run(self.test_cmd)

        if returncode == 0:
            return "TESTS_PASSED"
        tail = (stdout + "\n" + stderr).strip()[-2000:]
        return f"TESTS_FAILED\n{tail}"
