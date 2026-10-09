"""Experiment isolation and resume support.

Each experiment gets a dedicated directory with its own database, artifacts,
and state tracking. This enables parallel execution and resume-after-abort.
"""

import datetime
import json
import os

from hackingBuddyGPT.utils.db_storage.db_storage import RawDbStorage


class ExperimentManager:
    """Manages an isolated experiment directory with state tracking and resume."""

    def __init__(self, experiment_id: str | None = None, base_dir: str = "experiments"):
        """Create or open an experiment directory.

        Args:
            experiment_id: Unique ID for this experiment. If None, generates a
                           timestamp-based ID.
            base_dir: Root directory for all experiments.
        """
        if experiment_id is None:
            experiment_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

        self.experiment_id = experiment_id
        self.base_dir = base_dir
        self.exp_dir = os.path.join(base_dir, experiment_id)
        self.artifact_dir = os.path.join(self.exp_dir, "artifacts")
        self.db_path = os.path.join(self.exp_dir, "log.db")
        self.state_path = os.path.join(self.exp_dir, "state.json")

        os.makedirs(self.artifact_dir, exist_ok=True)

        # Initialize DB
        self.db = RawDbStorage(connection_string=self.db_path)
        self.db.init()
        self.db.setup_db()

    # ---- State management ----

    def load_state(self) -> dict:
        """Load experiment state from state.json, or return empty state."""
        if os.path.exists(self.state_path):
            with open(self.state_path) as f:
                return json.load(f)
        return {
            "experiment_id": self.experiment_id,
            "created": datetime.datetime.now().isoformat(),
            "phases": {},
        }

    def save_state(self, state: dict) -> None:
        """Save experiment state to state.json."""
        state["updated"] = datetime.datetime.now().isoformat()
        with open(self.state_path, "w") as f:
            json.dump(state, f, indent=2)

    # ---- Tags ----

    @staticmethod
    def build_tag(vm_id: int, iteration: int | None = None, transfer: bool = False) -> str:
        """Build a structured tag string for this experiment."""
        return RawDbStorage.build_tag(vm_id, iteration=iteration, transfer=transfer)

    # ---- Resume / cleanup ----

    def resume_phase(self, phase: str, vm_id: int, k_tests: int,
                     transfer: bool = False) -> int:
        """Prepare to resume a phase for a VM.

        Cleans up any "in progress" runs and returns the number of
        additional runs needed to reach k_tests.

        Args:
            phase: Phase name ("phase1", "transfer", "baseline_b").
            vm_id: VM identifier.
            k_tests: Target number of runs.
            transfer: If True, use the transfer tag format.

        Returns:
            Number of runs still needed (0 if phase is already complete).
        """
        if transfer:
            tag = self.build_tag(vm_id, transfer=True)
        elif phase == "phase1":
            tag = self.build_tag(vm_id, iteration=0)
        elif phase == "transfer":
            tag = self.build_tag(vm_id, transfer=True)
        else:
            tag = self.build_tag(vm_id, iteration=0)  # fallback

        # Clean up stalled "in progress" runs
        cleaned = self.db.cleanup_in_progress_runs(tag)
        if cleaned > 0:
            print(f"Cleaned up {cleaned} in-progress run(s) for tag '{tag}'")

        # Count completed (non-in-progress) runs
        completed = self.db.count_runs_by_tag(tag)
        needed = max(0, k_tests - completed)

        if needed == 0:
            print(f"Phase '{phase}' VM {vm_id}: already complete ({completed} runs)")
        else:
            print(f"Phase '{phase}' VM {vm_id}: {completed}/{k_tests} done, {needed} remaining")

        return needed

    def count_runs_by_tag(self, tag: str) -> int:
        """Count runs with the given tag (excluding 'in progress')."""
        return self.db.count_runs_by_tag(tag)
