# Trajectories-in-SE

## Current results

Instance: `astropy__astropy-12907` (SWE-bench Lite), 20 independent runs, 19 successful. The one failure (run 10) reached the maximum turn limit without submitting a fix.
Each run gives the model a bug report and a Docker container with the buggy repo, and lets it
read/edit/test code (`exec_command`) until it believes the issue is fixed and asks for the
hidden test suite to be run (`submit_patch`). A run succeeds when that test suite passes.

## Folder contents

### `artifacts/vm_0/`

Output of the abstraction and automata-learning steps, run on the 20 collected traces.

- `abstractions.json` / `abstractions.txt`: every (action, observation) pair from every run, labeled by the model with an abstract (action category, observation category) pair
- `hb_mc.dot`: the Markov chain learned from the abstracted traces (Alergia algorithm), one state per (action category, output category), with transition probabilities
- `model_summary.txt`: a readable listing of every state in `hb_mc.dot` with its outgoing transitions and probabilities
- `hb_mc_0.pdf`: a rendered chart of `hb_mc.dot`

### `job_logs/`

- `astropy__astropy-12907.sqlite3`: the database with the full history of all 20 runs
- `astropy__astropy-12907.test.patch`: hidden test patch for this instance, written to disk once before any run starts, and used (applied and reverted) each time the model calls `submit_patch` to check its fix against the real tests.

### `output/`

20 text files (`run1` through `run20`), one per run, each a readable transcript of that run: every prompt, every model reply, every command executed and its result, turn by turn, ending with the run's final status.
