"""Slurm on the cluster: submit a project's job and see how its runs go.

The resources are the #SBATCH lines in the project's own job.slurm; the
tool writes no job script of its own and adds only `--array` from runs.txt.
So what the examples teach is exactly what gets submitted, and the same
command works by hand without the tool.
"""

import re
import shlex
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from sc_starter import Problem, notes, runs, ssh, transfer
from sc_starter.layout import (
    FAILED_FILE,
    JOB_SCRIPT,
    NO_OUTPUT,
    NOT_ON_CLUSTER,
    NOTES_DIR,
    OUTPUT_SUFFIX,
    RUNS_FILE,
    SETUP_GOING,
    WHICH_RUN,
    enter_remote_dir,
    not_on_cluster,
    remote_label,
)

# States of runs that are still waiting or going. Every other state except
# COMPLETED means the run ended without finishing (FAILED, TIMEOUT, ...).
ACTIVE_STATES = {
    "PENDING",
    "CONFIGURING",
    "RUNNING",
    "COMPLETING",
    "SUSPENDED",
    "REQUEUED",
    "RESIZING",
}
COMPLETED = "COMPLETED"
UNKNOWN = "UNKNOWN"

# Separates the output of squeue from that of sacct in the status call.
SEPARATOR = "--- sacct ---"

# When submit cannot tell whether sbatch took the job.
MAY_RUN = (
    f"so the job may run anyway. Look with `ssh {ssh.LOGIN} squeue --me` "
    "before you submit again."
)


def submit_script(
    name: str, script: str, spec: str | None, setup: str | None = None
) -> str:
    """Return the shell commands that submit the job on the login node.

    `setup` is the ID of a job that installs what this one needs: while
    squeue still lists it, nothing is submitted.
    """
    sbatch = ["sbatch", "--parsable"]
    if spec is not None:
        sbatch.append(f"--array={spec}")
    sbatch.append(script)
    wait = ""
    if setup is not None:
        wait = (
            f"squeue --noheader --jobs={setup} 2>/dev/null | grep -q . "
            f"&& exit {SETUP_GOING}\n"
        )
    return f"{enter_remote_dir(name)}{wait}{shlex.join(sbatch)}\n"


def job_id(sbatch_output: str) -> str:
    """Read the job ID from `sbatch --parsable`, which prints jobid[;cluster].

    Only its last line: a ~/.bashrc on the cluster may print before it.
    """
    said = sbatch_output.strip()
    job = said.splitlines()[-1].split(";")[0] if said else ""
    if not job.isdigit():
        raise Problem(f"sbatch printed {said!r} instead of a job ID, {MAY_RUN}")
    return job


def submit(
    project: Path, lines_file: Path | None = None, script: str = JOB_SCRIPT
) -> tuple[str, str | None, tuple[int, int, int]]:
    """Upload what changed, then submit a job script of the project.

    job.slurm runs once per line of runs.txt, if there is one. Any other
    script, such as setup.slurm that installs the packages once, runs as a
    single job. Uploading first means the cluster always runs what is in
    this folder. Return the job ID, its run numbers the short way Slurm
    writes them, and what push returned.
    """
    name = transfer.project_name(project)
    # Tab completion in PowerShell writes .\setup.slurm.
    script = script.removeprefix("./").removeprefix(".\\")
    if not transfer.SAFE_NAME.fullmatch(script) or not (project / script).is_file():
        raise Problem(f"There is no {script} in this folder.")
    count = runs.count_runs(project) if script == JOB_SCRIPT else None
    if lines_file is not None and count is None:
        raise Problem(f"--lines needs {JOB_SCRIPT} and a {RUNS_FILE} in this folder.")

    run_numbers = None
    if lines_file is not None:
        run_numbers = runs.read_run_numbers(lines_file, count)
    elif count is not None:
        run_numbers = list(range(1, count + 1))
    spec = runs.array_spec(run_numbers) if run_numbers else None

    setup = notes.setup_job(project) if script == JOB_SCRIPT else None
    problems = {}
    if setup:
        problems[SETUP_GOING] = (
            f"{setup.script} (job {setup.job_id}) has not finished yet. "
            f"Submit {JOB_SCRIPT} once `sc-starter status` shows it COMPLETED."
        )

    pushed = transfer.push(project)
    setup_id = setup.job_id if setup else None
    try:
        printed = ssh.run(
            ssh.LOGIN, submit_script(name, script, spec, setup_id), problems
        )
    except KeyboardInterrupt:
        raise Problem(f"Stopped while the cluster was submitting, {MAY_RUN}") from None
    job = job_id(printed)
    try:
        notes.save(project, job, script, run_numbers)
    except OSError as error:
        raise Problem(
            f"Submitted job {job}, but could not keep a note of it in "
            f"{NOTES_DIR}/: {error.strerror}. The job runs; see it with "
            f"`sc-starter status {job}`, and do not submit it again."
        ) from None
    return job, spec, pushed


@dataclass
class Run:
    """One run of a job, as Slurm reports it."""

    state: str = UNKNOWN
    exit_code: str = ""
    node: str = ""
    elapsed: str = ""
    reason: str = ""

    def failed(self) -> bool:
        """Tell whether the run ended without completing."""
        return self.state not in ACTIVE_STATES | {COMPLETED, UNKNOWN}


def status_script(job: str) -> str:
    """Ask both parts of Slurm in one call.

    squeue knows waiting and running runs, with the reason for waiting, but
    forgets a job a few minutes after it ends; sacct keeps finished runs.
    """
    return (
        f"squeue --jobs={job} --array --noheader --format='%i|%T|%r|%N|%M' "
        "2>/dev/null\n"
        f"echo '{SEPARATOR}'\n"
        f"sacct --jobs={job} --allocations --parsable2 --noheader "
        "--format=JobID,State,ExitCode,NodeList,Elapsed\n"
    )


def _rows(text: str, job: str):
    """Yield the run number and the other fields of each line about `job`.

    The run number is None for a job without runs. sacct writes the runs
    that have not started in one line such as 123_[4-10]; that line is
    yielded once per run, so that runs cancelled before they started are
    not lost.
    """
    task = re.compile(rf"{job}(?:_(\d+)|_\[([\d,%-]+)\])?")
    for line in text.splitlines():
        job_id, *fields = line.split("|")
        if not (match := task.fullmatch(job_id)):
            continue
        single, grouped = match.groups()
        if grouped:
            # A limit of runs at a time, as in [4-10%2], names no runs.
            for number in runs.expand_spec(grouped.partition("%")[0]):
                yield number, fields
        else:
            yield (int(single) if single else None), fields


def parse_status(output: str, job: str) -> dict[int | None, Run]:
    """Read the output of the status call into one Run per run number."""
    queue, _, accounting = output.partition(SEPARATOR + "\n")
    runs: dict[int | None, Run] = {}
    for number, (state, exit_code, node, elapsed) in _rows(accounting, job):
        # sacct writes "CANCELLED by <user id>"; the first word is the state.
        runs[number] = Run(state.split()[0], exit_code, node, elapsed)
    # squeue is more up to date for runs it still knows.
    for number, (state, reason, node, elapsed) in _rows(queue, job):
        runs[number] = Run(state, "", node, elapsed, reason)
    return runs


def _table(rows: list[list[str]]) -> str:
    widths = [max(len(row[i]) for row in rows) for i in range(len(rows[0]))]
    return "\n".join(
        "  ".join(
            cell.ljust(width) for cell, width in zip(row, widths, strict=True)
        ).rstrip()
        for row in rows
    )


def status(project: Path, job: str | None = None) -> str:
    """Report each run of the job; write the failed runs to failed.txt."""
    job, note = notes.job_meant(project, job)
    found = parse_status(ssh.run(ssh.LOGIN, status_script(job)), job)
    if not found:
        return (
            f"Slurm does not list job {job}. Right after submitting, "
            "wait a few seconds and try again."
        )

    if note is None:
        numbers = sorted(found, key=lambda number: number or 0)
    elif note.run_numbers is None:
        numbers = [None]
    else:
        numbers = note.run_numbers
    commands = note.commands if note else []

    shown = {number: found.get(number, Run()) for number in numbers}
    header = ["run", "state", "exit", "node", "elapsed"]
    rows = [header + ["command"] if commands else header]
    for number, run in shown.items():
        # Right after submitting, Slurm gives the reason "None" for a while.
        waiting = run.state == "PENDING" and run.reason not in ("", "None")
        state = f"{run.state} ({run.reason})" if waiting else run.state
        label = str(number) if number else "-"
        row = [label, state, run.exit_code, run.node, run.elapsed]
        if commands:
            row.append(
                commands[number - 1] if number and number <= len(commands) else ""
            )
        rows.append(row)

    counts = Counter(run.state for run in shown.values())
    summary = ", ".join(f"{count} {state}" for state, count in sorted(counts.items()))
    report = [f"Job {job}: {summary}", "", _table(rows)]
    if numbers == [None]:
        # failed.txt is for `submit --lines`, which needs runs.txt.
        return "\n".join(report)

    # failed.txt always holds the failed runs of the job shown last, so that
    # one from an earlier job never sends runs again that have since passed.
    failed = [number for number, run in shown.items() if run.failed()]
    failed_file = project / FAILED_FILE
    if failed:
        failed_file.write_text("".join(f"{n}\n" for n in failed))
        command = f"`sc-starter submit --lines {FAILED_FILE}`"
        # Submitted now, status would follow only the new job from then on.
        if any(state in ACTIVE_STATES for state in counts):
            again = (
                "Once the runs still waiting or running have ended, "
                f"submit them again with {command}."
            )
        else:
            again = f"Submit them again with {command}."
        report += ["", f"Wrote the failed runs to {FAILED_FILE}. {again}"]
    elif failed_file.exists():
        failed_file.unlink()
        report += ["", f"No run of job {job} failed; removed the old {FAILED_FILE}."]
    return "\n".join(report)


def log(project: Path, run: int | None, job: str | None = None) -> str:
    """Return the output file of one run, read on the cluster.

    The file name follows the job scripts of this repository:
    `--output=%x-%A_%a.out` for runs, `--output=%x-%j.out` without.
    """
    name = transfer.project_name(project)
    job_id, note = notes.job_meant(project, job)
    which_run = (
        "Which run? For example: "
        f"`sc-starter log {f'--job {job_id} ' if job else ''}3`."
    )
    if run is not None:
        if note and note.run_numbers and run not in note.run_numbers:
            ran = runs.array_spec(note.run_numbers)
            raise Problem(f"Job {job_id} has no run {run}; it ran {ran}.")
        pattern = f"*-{job_id}_{run}{OUTPUT_SUFFIX}"
        naming = f"%x-%A_%a{OUTPUT_SUFFIX}"
    elif note and note.run_numbers is not None:
        raise Problem(which_run)
    else:
        pattern = f"*-{job_id}{OUTPUT_SUFFIX}"
        naming = f"%x-%j{OUTPUT_SUFFIX}"

    missing = f"exit {NO_OUTPUT}"
    if run is None:
        # A job from elsewhere, or a job script with its own --array, may
        # have runs; then their output files say so.
        runs_pattern = f"*-{job_id}_*{OUTPUT_SUFFIX}"
        missing = f"ls -- {runs_pattern} >/dev/null 2>&1 && exit {WHICH_RUN}; {missing}"
    script = (
        f"{enter_remote_dir(name)}set -- {pattern}\n"
        f'[ -e "$1" ] || {{ {missing}; }}\n'
        'cat -- "$1"\n'
    )
    printed = ssh.run(
        ssh.EXPORT,
        script,
        problems={
            NOT_ON_CLUSTER: not_on_cluster(name),
            NO_OUTPUT: f"There is no output file {pattern} in "
            f"{remote_label(name)} yet. Slurm writes it when the run starts, "
            f"if {JOB_SCRIPT} names it with `#SBATCH --output={naming}`.",
            WHICH_RUN: f"Job {job_id} has runs. {which_run}",
        },
    )
    return printed or (
        f"The output file {pattern} is empty. If the run failed, your home "
        f"directory may be full: `ssh {ssh.EXPORT} sc_quotas` shows it.\n"
    )
