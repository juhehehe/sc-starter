"""The `sc-starter` command: read the arguments and run one subcommand."""

import argparse
import sys
from importlib.metadata import version
from pathlib import Path

from sc_starter import Problem, layout, slurm, ssh, transfer

PROG = "sc-starter"


def files(count: int) -> str:
    """Return "1 file" or "N files"."""
    return f"{count} file" if count == 1 else f"{count} files"


def check(args: argparse.Namespace) -> None:
    """Connect to both cluster hosts once; the setup guide ends with this."""
    for host in (ssh.LOGIN, ssh.EXPORT):
        name = ssh.run(host, "hostname -s").strip()
        print(f"{host}: ok ({name})")
    print("Ready.")


def uploaded(project: Path, count: int, size: int, unchanged: int) -> str:
    """Describe what push sent, in the words of push and submit."""
    target = f"{ssh.EXPORT}:{layout.remote_label(project.name)}"
    if count == 0:
        return f"Nothing to upload: {target} is up to date ({files(unchanged)})."
    report = f"Uploaded {files(count)} ({size / 1_000_000:.1f} MB) to {target}"
    if unchanged:
        report += f"; {files(unchanged)} unchanged"
    return report


def push(args: argparse.Namespace) -> None:
    """Upload what is new or changed in the project in the current folder."""
    project = Path.cwd()
    print(uploaded(project, *transfer.push(project)))


def submit(args: argparse.Namespace) -> None:
    """Upload what changed, then submit a job script of the current folder."""
    project = Path.cwd()
    job, spec, (count, size, unchanged) = slurm.submit(project, args.lines, args.script)
    if count:
        print(uploaded(project, count, size, unchanged))
    runs = f" with runs {spec}" if spec else ""
    print(f"Submitted job {job}{runs}. See how it goes with `{PROG} status`.")


def pull(args: argparse.Namespace) -> None:
    """Bring results/ and the Slurm output files back to the current folder."""
    count, size, still_writing = transfer.pull(Path.cwd())
    print(f"Pulled {files(count)} ({size / 1_000_000:.1f} MB) into this folder.")
    if still_writing:
        print(
            "Some files were still being written and may be incomplete. "
            "Pull again when the runs are done."
        )


def status(args: argparse.Namespace) -> None:
    """Show each run of the last job, or of the job given."""
    print(slurm.status(Path.cwd(), args.job))


def log(args: argparse.Namespace) -> None:
    """Print the Slurm output file of one run."""
    print(slurm.log(Path.cwd(), args.run, args.job), end="")


def build_parser() -> argparse.ArgumentParser:
    """Describe the commands and their options for argparse."""
    parser = argparse.ArgumentParser(
        prog=PROG,
        description=(
            "Run Slurm jobs on the SC cluster of Leipzig University "
            "from your own computer."
        ),
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {version(PROG)}"
    )
    commands = parser.add_subparsers(title="commands", metavar="<command>")

    check_parser = commands.add_parser(
        "check", help="test the connection to the cluster"
    )
    check_parser.set_defaults(func=check)

    push_parser = commands.add_parser(
        "push", help="upload the project in this folder to the cluster"
    )
    push_parser.set_defaults(func=push)

    submit_parser = commands.add_parser(
        "submit",
        help="submit job.slurm; one run per line of runs.txt, if there is one",
    )
    submit_parser.add_argument(
        "script",
        nargs="?",
        default=layout.JOB_SCRIPT,
        help="another job script to run once, such as setup.slurm",
    )
    submit_parser.add_argument(
        "--lines",
        type=Path,
        metavar="FILE",
        help="submit only the run numbers listed in FILE, such as failed.txt",
    )
    submit_parser.set_defaults(func=submit)

    status_parser = commands.add_parser(
        "status", help="show how each run of the last job is going"
    )
    status_parser.add_argument(
        "job", nargs="?", help="a job ID instead of the last job"
    )
    status_parser.set_defaults(func=status)

    log_parser = commands.add_parser(
        "log", help="print the output file of one run of the last job"
    )
    log_parser.add_argument(
        "run", nargs="?", type=int, help="the run number, which is its line in runs.txt"
    )
    log_parser.add_argument("--job", help="a job ID instead of the last job")
    log_parser.set_defaults(func=log)

    pull_parser = commands.add_parser(
        "pull", help="bring results/ and the output files back from the cluster"
    )
    pull_parser.set_defaults(func=pull)

    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the command and return its exit code.

    `argv` defaults to the real command line; tests pass their own list.
    """
    # Windows writes output that goes into a file or pipe in its ANSI code
    # page, which lacks characters that cluster logs have, such as the █ of
    # progress bars. Write a ? for those instead of stopping with a traceback.
    sys.stdout.reconfigure(errors="replace")
    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 0
    try:
        args.func(args)
    except Problem as problem:
        print(f"{PROG}: {problem}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print(f"{PROG}: Stopped.", file=sys.stderr)
        return 130  # what shells report for Ctrl+C
    return 0
