"""The examples follow the conventions the tool relies on.

`sc-starter log` finds the output file of a run by its name, and `submit`
counts the runs in runs.txt. An example that broke either would break the
tool for everyone who copies it. And the README of an example builds its
files block by block; together, the blocks must be the files in its folder.
"""

import re
from pathlib import Path

import pytest

from sc_starter import runs
from sc_starter.layout import NOTES_DIR

REPO = Path(__file__).resolve().parents[1]
# Folders with files the repository does not write itself, among them the
# copies that site/build.py makes of the pages.
SKIP = {".git", ".venv", NOTES_DIR, "_src", "_site"}


def repository_files(pattern: str) -> list[Path]:
    return sorted(
        path
        for path in REPO.glob(f"**/{pattern}")
        if not SKIP.intersection(path.relative_to(REPO).parts)
    )


def name(path: Path) -> str:
    return path.relative_to(REPO).as_posix()


@pytest.mark.parametrize("script", repository_files("*.slurm"), ids=name)
def test_job_scripts_name_their_output_files_as_log_expects(script):
    """Array jobs: name, job ID, run number; any other job: name, job ID."""
    array = script.name == "job.slurm" and (script.parent / "runs.txt").exists()
    naming = "%x-%A_%a.out" if array else "%x-%j.out"

    assert f"#SBATCH --output={naming}" in script.read_text(encoding="utf-8")


@pytest.mark.parametrize("runs_file", repository_files("runs.txt"), ids=name)
def test_runs_files_hold_one_run_per_line(runs_file):
    assert runs.count_runs(runs_file.parent) > 0


# A code block whose title names a file: ```python title="run.py"```.
FILE_BLOCK = re.compile(r'^```\w* title="([^"]+)"\n(.*?)^```', re.MULTILINE | re.DOTALL)
# Titles that are no file of the example: where a command runs (R is the
# console of R), what it prints, a folder, a result that only the runs
# write, or a few lines shown on their own.
NOT_A_FILE = re.compile(r"Your computer|Cluster|R|Output|.*/|results/.*|Part of .*")


def written_files(readme: Path) -> dict[str, str]:
    """The files a README builds, each from all its blocks in order."""
    files: dict[str, list[str]] = {}
    for title, block in FILE_BLOCK.findall(readme.read_text(encoding="utf-8")):
        if not NOT_A_FILE.fullmatch(title):
            files.setdefault(title, []).append(block)
    return {title: "\n".join(blocks) for title, blocks in files.items()}


def lines(text: str) -> list[str]:
    """The lines of a file, without the blank lines that join the blocks."""
    return [line.rstrip() for line in text.splitlines() if line.strip()]


@pytest.mark.parametrize(
    "readme",
    [path for path in repository_files("README.md") if "examples" in path.parts],
    ids=name,
)
def test_readmes_build_the_files_of_their_example(readme):
    for title, text in written_files(readme).items():
        assert lines(text) == lines((readme.parent / title).read_text()), title


@pytest.mark.parametrize(
    ("page", "folder"),
    [
        ("slurm/first-job.md", "first-jobs"),
        ("slurm/r-and-python.md", "first-jobs"),
        ("slurm/job-arrays.md", "first-jobs/hello-array"),
        ("slurm/time-and-memory.md", "first-jobs"),
        ("slurm/gpu-jobs.md", "first-jobs"),
    ],
)
def test_the_slurm_pages_build_the_first_jobs(page, folder):
    """Each page of the Slurm section writes the files of its first jobs."""
    files = written_files(REPO / "docs" / page)
    assert files
    for title, text in files.items():
        assert lines(text) == lines((REPO / folder / title).read_text()), title
