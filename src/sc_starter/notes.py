"""The job notes in `.sc-starter/` of a project: what your computer knows of jobs.

The folder holds one folder per submitted job with its ID, the time, the
job script and the run numbers, and copies of the job script and runs.txt,
so that one can later tell what ran when; and the ID of the last job.
status, log and submit ask only this module which job is meant and what
it ran.
"""

import json
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from sc_starter import Problem, runs
from sc_starter.layout import JOB_SCRIPT, NOTES_DIR, RUNS_FILE, notes_dir


@dataclass(frozen=True)
class JobNote:
    """What your computer knows of a job submitted from this project folder."""

    job_id: str
    script: str  # the job script it ran
    run_numbers: list[int] | None  # None for a job without runs
    commands: list[str]  # the lines of runs.txt when it was submitted


def save(
    project: Path, job_id: str, script: str, run_numbers: list[int] | None
) -> None:
    """Keep a note of a submitted job and make it the last job of the project."""
    files = [script] + ([RUNS_FILE] if run_numbers else [])
    folder = notes_dir(project) / "jobs" / job_id
    folder.mkdir(parents=True, exist_ok=True)  # Slurm may give an ID again
    for file in files:
        shutil.copy2(project / file, folder / file)
    note = {
        "job_id": job_id,
        "submitted": datetime.now().astimezone().isoformat(timespec="seconds"),
        "script": script,
        "array": runs.array_spec(run_numbers) if run_numbers else None,
    }
    (folder / "job.json").write_text(json.dumps(note, indent=2) + "\n")
    (notes_dir(project) / "last-job").write_text(job_id + "\n")


def job_meant(project: Path, job_id: str | None) -> tuple[str, JobNote | None]:
    """Return the job that status and log mean, and its note.

    That is the job ID given, or else the last job. The note is None for a
    job submitted from elsewhere, or when it was cut off, as when the computer
    went off while submit wrote it.
    """
    if job_id is None:
        job_id = _last_job(project)
    # The ID goes into shell commands on the cluster.
    elif not job_id.isdigit():
        raise Problem(f"{job_id!r} is not a job ID; job IDs are numbers.")
    return job_id, _read(project, job_id)


def setup_job(project: Path) -> JobNote | None:
    """Return the note of the last job, if it ran another script than job.slurm.

    Usually setup.slurm, which installs the packages job.slurm needs.
    """
    try:
        job_id = _last_job(project)
    except Problem:
        return None  # no job yet, or a damaged note: nothing to wait for
    note = _read(project, job_id)
    return note if note and note.script != JOB_SCRIPT else None


def _last_job(project: Path) -> str:
    path = project / NOTES_DIR / "last-job"
    if not path.exists():
        raise Problem("No job was submitted from this folder yet.")
    job_id = path.read_text().strip()
    if not job_id.isdigit():
        raise Problem(
            f"{NOTES_DIR}/last-job does not hold a job ID. "
            "Name the job instead: `sc-starter status <job ID>`."
        )
    return job_id


def _read(project: Path, job_id: str) -> JobNote | None:
    folder = project / NOTES_DIR / "jobs" / job_id
    try:
        note = json.loads((folder / "job.json").read_text())
        spec = note.get("array")
        run_numbers = runs.expand_spec(spec) if spec else None
        # job.slurm for notes kept before they named the script.
        script = note.get("script", JOB_SCRIPT)
    except (OSError, ValueError, AttributeError):
        return None  # none, or damaged
    return JobNote(job_id, script, run_numbers, _commands(folder / RUNS_FILE))


def _commands(copy: Path) -> list[str]:
    """Return the copy of runs.txt, read as runs.txt itself: line N is run N."""
    try:
        return runs.read_lines(copy)
    except (OSError, Problem):
        return []  # a job without runs, or a damaged copy
