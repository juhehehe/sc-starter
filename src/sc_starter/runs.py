"""The run list `runs.txt`: one complete command per line, line N is run N.

No comments and no empty lines, so that the line number in any editor is
exactly the run number Slurm gives the job (`$SLURM_ARRAY_TASK_ID`), and
`sed -n "${SLURM_ARRAY_TASK_ID}p" runs.txt` in the job script picks it.
"""

import re
from pathlib import Path

from sc_starter import Problem
from sc_starter.layout import RUNS_FILE
from sc_starter.transfer import unix_text

# Characters that Python's splitlines() takes as the end of a line, but sed
# in the job script does not: there only \n ends a line. Text copied from
# another program can bring them along without showing them.
HIDDEN_LINE_BREAK = re.compile("[\r\v\f\x1c\x1d\x1e\x85\u2028\u2029]")


def read_text(path: Path) -> str:
    """Return the text of a file the way it goes to the cluster.

    Without the mark Windows puts before UTF-8 and with Unix line endings,
    see `unix_text`: runs.txt then reads here as it does in the job script,
    and a file for --lines written in PowerShell reads like any other.
    """
    try:
        return unix_text(path).decode("utf-8")
    except UnicodeDecodeError:
        raise Problem(
            f"{path.name} is not saved as UTF-8. Save it again as UTF-8 (in "
            "VS Code: the encoding at the bottom right). In PowerShell, write "
            "it with `Set-Content -Encoding utf8` instead of `>`."
        ) from None


def read_lines(path: Path) -> list[str]:
    """Return the lines of a run list, split as sed in the job script splits them."""
    text = read_text(path)
    return text.removesuffix("\n").split("\n") if text else []


def count_runs(project: Path) -> int | None:
    """Check runs.txt and return its number of runs; None if there is none."""
    path = project / RUNS_FILE
    if not path.exists():
        return None
    # So that the count is the number of runs sed sees.
    lines = read_lines(path)
    if not lines:
        raise Problem(f"{RUNS_FILE} is empty. Write one run per line.")
    for number, line in enumerate(lines, start=1):
        if not line.strip():
            raise Problem(
                f"{RUNS_FILE}, line {number} is empty. Every line is one run, "
                "so remove empty lines."
            )
        if line.lstrip().startswith("#"):
            raise Problem(
                f"{RUNS_FILE}, line {number} is a comment. Every line is one "
                "run, so keep notes elsewhere, for example in the README."
            )
        if line.rstrip().endswith("\\"):
            raise Problem(
                f"{RUNS_FILE}, line {number} ends with \\. Every line is one "
                "complete run, so write the whole command on one line."
            )
        if hidden := HIDDEN_LINE_BREAK.search(line):
            raise Problem(
                f"{RUNS_FILE}, line {number} has a hidden line break "
                f"(U+{ord(hidden.group()):04X}), as text copied from another "
                "program can have. The job script would run it with the next "
                "part as one command. Delete it, and write each run on its own "
                "line."
            )
    return len(lines)


def read_run_numbers(path: Path, count: int) -> list[int]:
    """Read run numbers, one per line, as `status` writes them to failed.txt."""
    if not path.exists():
        raise Problem(f"{path.name} does not exist.")
    numbers = set()
    for word in read_text(path).split():
        if not word.isdigit() or not 1 <= int(word) <= count:
            raise Problem(
                f"{path.name} lists {word!r}, but {RUNS_FILE} has runs 1 to {count}."
            )
        numbers.add(int(word))
    if not numbers:
        raise Problem(f"{path.name} lists no runs.")
    return sorted(numbers)


def array_spec(numbers: list[int]) -> str:
    """Write sorted run numbers the short way Slurm reads them: 1-3,7,9-10."""
    ranges: list[list[int]] = []
    for number in numbers:
        if ranges and number == ranges[-1][1] + 1:
            ranges[-1][1] = number
        else:
            ranges.append([number, number])
    return ",".join(str(a) if a == b else f"{a}-{b}" for a, b in ranges)


def expand_spec(spec: str) -> list[int]:
    """Return the run numbers of an array spec: 1-3,7 gives [1, 2, 3, 7]."""
    numbers = []
    for part in spec.split(","):
        first, _, last = part.partition("-")
        numbers += range(int(first), int(last or first) + 1)
    return numbers
