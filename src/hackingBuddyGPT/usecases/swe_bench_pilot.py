"""Single-instance SWE-bench task runner — smoke test for whether the ATLAS methodology
(explore -> abstract -> learn a Markov chain) transfers from pentesting to software-engineering
tasks. Mirrors usecases/linux_privesc.py's PrivEscLinux (CommandStrategy subclass, same
capability-loop mechanics), but targets a git repo inside a Docker container
instead of a VM over SSH, and requires passing tests instead of a root shell as its success signal.

Runs are logged to the same SQLite log DB as every other UseCase in this repo, so
automata/trace_extraction.py can read them by tag without any changes.
"""

import re

from mako.template import Template

from hackingBuddyGPT.capabilities.docker_run_command import DockerRunCommand
from hackingBuddyGPT.capabilities.submit_patch import SubmitPatch
from hackingBuddyGPT.strategies import CommandStrategy
from hackingBuddyGPT.usecases.usecase import use_case
from hackingBuddyGPT.utils.configurable import parameter
from hackingBuddyGPT.utils.connectors.docker_connection import DockerConnection

swe_template = Template("""You are a software engineer working inside a checked-out git repository
at ${repo_path}. Your goal is to resolve the following issue by editing the code so that the
project's test suite passes.

ISSUE:
${issue_text}

${capabilities}

% if len(history) != 0:
You already tried the following commands:

~~~ bash
${history}
~~~

Do not repeat commands that already told you what you need to know.
%endif

Decide your next single action. Use exec_command to read/search/edit files or run commands, and
submit_patch only once you believe the fix is complete and want it verified against the test
suite.

Your entire reply must be exactly one line, in one of these two forms, and nothing else:
exec_command <shell command on one line>
submit_patch <short note>
Do not explain your reasoning, do not add markup, and do not continue the conversation after that line.
""")

# The hosted model tends to answer with markdown reasoning around (and after) the command, sometimes
# ending with stray tool-call tags. Keep only the first command line and drop those tags.
_COMMAND_LINE_RE = re.compile(r"^[ \t]*((?:exec_command|submit_patch)\b.*)$", re.MULTILINE)
_STRAY_TAGS_RE = re.compile(r"(?:</?(?:parameter|output|command|invoke|function_calls)[^>]*>\s*)+$")


@use_case("SWE-bench Pilot Task (single instance, ATLAS methodology-transfer experiment)")
class SWEBenchPilotUseCase(CommandStrategy):
    conn: DockerConnection = None

    issue_text: str = parameter(desc="Problem statement / issue text for this SWE-bench instance", default="")
    repo_path: str = parameter(desc="Path to the checked-out repo inside the container", default="/testbed")
    test_cmd: str = parameter(desc="Command that runs this instance's FAIL_TO_PASS tests", default="")
    test_patch_file: str = parameter(
        desc="Host path of a file with the instance's test_patch, applied only while submit_patch runs the tests",
        default="",
    )

    def get_name(self) -> str:
        return "SWE-bench Pilot Task"

    def init(self):
        super().init()

        test_patch = ""
        if self.test_patch_file:
            # newline="" keeps any \r\n inside the patch untouched
            with open(self.test_patch_file, encoding="utf-8", newline="") as f:
                test_patch = f.read()

        self._template = swe_template
        self._capabilities.add_capability(DockerRunCommand(conn=self.conn), default=True)
        self._capabilities.add_capability(SubmitPatch(conn=self.conn, test_cmd=self.test_cmd, test_patch=test_patch))

        self._template_params.update({
            "issue_text": self.issue_text,
            "repo_path": self.repo_path,
        })

    def postprocess_commands(self, cmd: str) -> list[str]:
        # Only the extracted command is executed and stored in the history, so a rambling
        # reply does not pollute the next prompts.
        match = _COMMAND_LINE_RE.search(cmd)
        if match is None:
            return [cmd]
        return [_STRAY_TAGS_RE.sub("", match.group(1)).strip()]

    def get_token_overhead(self) -> int:
        # CommandStrategy only budgets history against the raw template source; the
        # rendered issue text and capability block would otherwise push the real
        # prompt past context_size.
        capabilities_block = self._template_params.get("capabilities", "")
        return self.llm.count_tokens(self.issue_text) + self.llm.count_tokens(capabilities_block)

    def check_success(self, cmd: str, result: str) -> bool:
        return cmd.startswith("submit_patch") and "TESTS_PASSED" in result
