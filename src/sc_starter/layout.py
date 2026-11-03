"""The fixed names of a project, on your computer and on the cluster.

Every name the tool relies on is here and nowhere else, so that renaming
one is a change of one line. The guides and examples use the same names.
So are the exit codes by which the scripts on the cluster report back.
"""

import shlex
from pathlib import Path

# In the project folder, on your computer and, after push, on the cluster.
JOB_SCRIPT = "job.slurm"  # runs once per line of runs.txt
JOB_SCRIPT_SUFFIX = ".slurm"  # every job script, such as setup.slurm
RUNS_FILE = "runs.txt"  # one run per line; line N is run N
RESULTS = "results"  # each run writes its own file here; pull brings it back
OUTPUT_SUFFIX = ".out"  # of the output files Slurm writes at the top
FAILED_FILE = "failed.txt"  # written by status: the runs to submit again
NOTES_DIR = ".sc-starter"  # on your computer only: job notes, what went up last

# On the cluster: all projects side by side in this folder of the home,
# each under the name of its folder on your computer.
REMOTE_ROOT = "sc-projects"


GITIGNORE = "# Created by sc-starter: keep this folder out of git.\n*\n"


def notes_dir(project: Path) -> Path:
    """Return `.sc-starter/` in `project`, created on first use.

    It carries its own .gitignore, as pytest and ruff do with their cache
    folders, so it never ends up in the project's git.
    """
    folder = project / NOTES_DIR
    if not folder.exists():
        folder.mkdir()
        (folder / ".gitignore").write_text(GITIGNORE)
    return folder


def remote_dir(name: str) -> str:
    """Return the project folder on the cluster, as a word for the remote shell."""
    return f'"$HOME"/{REMOTE_ROOT}/{shlex.quote(name)}'


def remote_label(name: str) -> str:
    """Return the project folder on the cluster, as messages name it."""
    return f"~/{REMOTE_ROOT}/{name}"


# Exit codes of the scripts on the cluster, for outcomes one can act on.
# Each has one meaning in every script: failing commands themselves exit
# 1 or 2, and ssh exits 255 when it failed itself.
NOT_ON_CLUSTER = 4  # the project folder is not on the cluster
NO_OUTPUT = 5  # the run has no output file (yet)
NOTHING_TO_PULL = 6  # no results and no output files yet
STILL_WRITING = 7  # a file changed while it was packed; not a failure
SETUP_GOING = 8  # the setup job is still in the queue
WHICH_RUN = 9  # the job has runs, so log needs a run number


def enter_remote_dir(name: str) -> str:
    """Return the first lines of a script that works in the project folder there."""
    return (
        f"dir={remote_dir(name)}\n"
        f'[ -d "$dir" ] || exit {NOT_ON_CLUSTER}\n'
        'cd "$dir" || exit\n'
    )


def not_on_cluster(name: str) -> str:
    """Return what to do when a script exits with NOT_ON_CLUSTER."""
    return (
        f"There is no {remote_label(name)} on the cluster. "
        "Submit a job first with `sc-starter submit`."
    )
