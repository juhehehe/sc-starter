"""Copy a project to the cluster and its results back, as tar archives.

No rsync: Windows has none, and macOS ships only openrsync since 15.4.
Each archive goes through one ssh call on the export node and passes
through a temporary file. So a file that push cannot read stops it before
anything is sent, and a broken connection stops pull before anything is
unpacked; a push cut off halfway is made whole by the next one.

push sends only what is new or changed, by the quick check of rsync: the
same size and modification time means the same file. For that it first
asks the export node what it has, in a call of its own; Windows' OpenSSH
opens a new connection for it (under a second), which is cheap against
sending gigabytes of unchanged data again with every small change. A file
whose copy on the cluster changed since it went up stops push, so that
neither a trial run on your computer nor an older copy of the project
overwrites newer work there; for that, push keeps what it sent last.

Links are handled as `rsync --copy-unsafe-links` does: a link that leads
out of the project goes up as what it points to, so that data linked in
from elsewhere on your computer arrives on the cluster; a link within the
project stays a link, since what it points to goes up as well.
"""

import codecs
import io
import json
import os
import re
import shlex
import tarfile
import tempfile
from pathlib import Path
from typing import IO

from sc_starter import Problem, layout, ssh
from sc_starter.layout import (
    NOT_ON_CLUSTER,
    NOTHING_TO_PULL,
    OUTPUT_SUFFIX,
    RESULTS,
    STILL_WRITING,
    enter_remote_dir,
    not_on_cluster,
    remote_dir,
    remote_label,
)

# Never uploaded, wherever they are: git history, SSH keys, Python
# environments and caches. Environments are rebuilt on the cluster from the
# lock files. Keys never leave your computer, not even behind a link to the
# home folder.
SKIP_ANYWHERE = {".git", ".ssh", ".venv", "__pycache__"}

# Never uploaded at the top of the project: results and Slurm output files
# come from the cluster, the tool's own files stay local (failed.txt is
# read by `submit --lines` on your computer), and so do the folders renv
# builds for your computer (those its own .gitignore names, but for the package
# sources in local/ and cellar/).
SKIP_AT_TOP = {
    RESULTS,
    layout.FAILED_FILE,
    layout.NOTES_DIR,
    "renv/library",
    "renv/lock",
    "renv/python",
    "renv/sandbox",
    "renv/staging",
}

# Folder names end up in paths of Slurm output files and shell commands.
SAFE_NAME = re.compile(r"[A-Za-z0-9._-]+")

# What the quick check finds for a file of the project, against its copy
# on the cluster.
SAME = "same"  # push leaves it
HERE_NEWER = "newer here"  # or not on the cluster yet: push sends it
CLUSTER_NEWER = "cluster newer"  # changed there since: push sends nothing

# In NOTES_DIR: the size and time of each file after the last push.
PUSHED = "pushed.json"

# A file's size as it goes up, and its modification time in whole seconds.
Look = tuple[int, int]


def project_name(project: Path) -> str:
    """Return the folder name, which is also the folder name on the cluster."""
    name = project.name
    if not SAFE_NAME.fullmatch(name):
        raise Problem(
            f"The folder name {name!r} cannot be used on the cluster. "
            "Rename the folder, using only letters, digits, '.', '_' and '-'."
        )
    return name


def is_output_file(relative: Path) -> bool:
    """Whether a path in the project is a Slurm output file, at its top."""
    return len(relative.parts) == 1 and relative.suffix == OUTPUT_SUFFIX


def is_skipped(relative: Path) -> bool:
    """Whether a file or folder of the project stays on your computer."""
    if any(part in SKIP_ANYWHERE for part in relative.parts):
        return True
    if relative.as_posix() in SKIP_AT_TOP:
        return True
    return is_output_file(relative)


def is_kept_link(project: Path, relative: Path) -> bool:
    """Whether `relative` is a link that goes up as a link.

    Only a link in the project itself whose target stays within it, judged
    by its text as rsync does: an absolute target never works on the
    cluster, and neither does one that climbs out with "..".
    """
    path = project / relative
    if not path.is_symlink():
        return False
    # A link inside a linked-in folder elsewhere is not part of the project.
    if not path.parent.resolve().is_relative_to(project.resolve()):
        return False
    target = Path(os.readlink(path))
    if target.is_absolute():
        return False
    depth = len(relative.parts) - 1
    for part in target.parts:
        depth += -1 if part == ".." else 1
        if depth < 0:
            return False
    return True


def files_to_upload(project: Path) -> list[Path]:
    """Every file that goes to the cluster, relative to the project folder."""
    files: list[Path] = []
    _collect(project, Path(), [project.resolve()], files)
    return files


def _collect(
    project: Path, relative: Path, ancestors: list[Path], files: list[Path]
) -> None:
    """Add the files of the folder `relative` and its subfolders to `files`.

    `ancestors` are the real folders on the way down: a link back to one of
    them would make the walk go round forever.
    """
    try:
        entries = sorted((project / relative).iterdir())
    except OSError as error:
        raise Problem(
            f"Cannot read the folder {relative.as_posix()}: "
            f"{error.strerror or error}. Nothing was uploaded."
        ) from None
    for entry in entries:
        path = relative / entry.name
        if is_skipped(path):
            continue
        if is_kept_link(project, path):
            files.append(path)
        elif entry.is_symlink() and not entry.exists():
            raise Problem(
                f"{path.as_posix()} is a link to {os.readlink(entry)}, which "
                "does not exist. Connect the drive it is on, or remove the link."
            )
        elif entry.is_dir():
            real = entry.resolve()
            if real in ancestors:
                raise Problem(
                    f"{path.as_posix()} is a link to a folder that contains it, "
                    "so push would go round forever. Link to the data folder "
                    "itself instead."
                )
            _collect(project, path, [*ancestors, real], files)
        else:
            files.append(path)


def needs_unix_line_endings(path: str) -> bool:
    r"""Tell whether a file at the top of the project goes up with Unix line endings.

    sbatch refuses job scripts with Windows line endings, and `sed` in the
    job script would keep the \r on every line of runs.txt.
    """
    return "/" not in path and (
        path.endswith(layout.JOB_SCRIPT_SUFFIX) or path == layout.RUNS_FILE
    )


def unix_text(path: Path) -> bytes:
    """Return the content of `path` as it goes to the cluster.

    With Unix line endings, and without the byte order mark that PowerShell
    5.1 and Excel put before UTF-8: bash would take it as part of the first
    command, and sbatch needs `#!` as the very first characters.
    """
    return path.read_bytes().removeprefix(codecs.BOM_UTF8).replace(b"\r\n", b"\n")


def pack(project: Path, files: list[Path], archive: IO[bytes]) -> None:
    """Write `files` of `project` into `archive` as a gzip-compressed tar."""
    with tarfile.open(fileobj=archive, mode="w:gz") as tar:
        for relative in files:
            local = project / relative
            path = relative.as_posix()
            try:
                if is_kept_link(project, relative):
                    info = tar.gettarinfo(local, arcname=path)
                    # Windows writes links with backslashes; the cluster needs /.
                    info.linkname = Path(info.linkname).as_posix()
                    tar.addfile(info)
                    continue
                # resolve(): a link out of the project goes up as its target.
                info = tar.gettarinfo(local.resolve(), arcname=path)
                if info is None:
                    continue  # a socket or the like, which tar cannot hold
                if needs_unix_line_endings(path):
                    data = unix_text(local)
                    info.size = len(data)
                    tar.addfile(info, io.BytesIO(data))
                else:
                    with local.open("rb") as file:
                        tar.addfile(info, file)
            except OSError as error:
                # The archive is still a local file, so nothing has gone up.
                raise Problem(
                    f"Cannot read {path}: {error.strerror or error}. "
                    "Nothing was uploaded."
                ) from None


def listing_script(name: str) -> str:
    """Return the shell commands that list the files in the project folder there.

    One entry per file, `<size> <modification time> <path>`, each ended by
    a NUL byte so that any file name comes through. What push never sends
    is left out, so that a .venv of thousands of files costs nothing.
    """
    prune = " -o ".join(
        [f"-name {shlex.quote(part)}" for part in sorted(SKIP_ANYWHERE)]
        + [f"-path ./{shlex.quote(path)}" for path in sorted(SKIP_AT_TOP)]
    )
    return (
        f"dir={remote_dir(name)}\n"
        '[ -d "$dir" ] || exit 0\n'
        'cd "$dir" || exit\n'
        f"find . \\( {prune} \\) -prune -o -type f -printf '%s %T@ %P\\0'\n"
    )


def parse_listing(output: str) -> dict[str, Look]:
    """Read the listing into {path: (size, modification time in whole seconds)}."""
    there = {}
    for entry in output.split("\0"):
        if entry:
            size, mtime, path = entry.split(" ", 2)
            there[path] = (int(size), int(float(mtime)))
    return there


def look(project: Path, relative: Path) -> Look | None:
    """Return the size and time a file has on the cluster; None to send it anyway.

    Job scripts and runs.txt are measured as they go up, with Unix line
    endings. Links that stay links are always sent; they are tiny. So is a
    file push cannot read, and pack then says which.
    """
    if is_kept_link(project, relative):
        return None
    local = project / relative
    try:
        stat = local.stat()
        if needs_unix_line_endings(relative.as_posix()):
            size = len(unix_text(local))
        else:
            size = stat.st_size
    except OSError:
        return None
    return size, int(stat.st_mtime)


def compare(here: Look | None, there: Look | None, last: Look | None) -> str:
    """Compare a file with its copy on the cluster.

    `last` is how it went up the last time. tar on the cluster keeps the
    time from your computer, so the same size and time mean the same file, and
    a copy there that differs from `last` changed on the cluster, as when a
    job wrote it. Without `last`, as for a copy of the project from another
    computer, a later time there means the same.
    """
    if here is None or there is None:
        return HERE_NEWER
    if here == there:
        return SAME
    changed_there = there != last if last else there[1] > here[1]
    return CLUSTER_NEWER if changed_there else HERE_NEWER


def newer_on_cluster(paths: list[str]) -> str:
    """Return the message when push stops for files whose copy there is newer."""
    shown = [f"  {path}" for path in paths[:10]]
    if len(paths) > 10:
        shown.append(f"  and {len(paths) - 10} more")
    return (
        "The cluster has a newer copy of these files than this folder:\n"
        + "\n".join(shown)
        + "\nNothing was uploaded, so that none is overwritten. Read "
        '"The cluster has a newer copy" in docs/reference/troubleshooting.md.'
    )


def last_pushed(project: Path) -> dict[str, Look]:
    """How each file went up the last time; empty when unknown."""
    try:
        listed = json.loads((project / layout.NOTES_DIR / PUSHED).read_text())
        return {path: (size, mtime) for path, (size, mtime) in listed.items()}
    except (OSError, ValueError, AttributeError, TypeError):
        return {}  # never pushed from here, or damaged


def save_pushed(project: Path, looks: dict[str, Look]) -> None:
    """Keep how each file went up, for the next push to compare."""
    try:
        path = layout.notes_dir(project) / PUSHED
        path.write_text(json.dumps(looks, indent=0, sort_keys=True) + "\n")
    except OSError:
        pass  # the next push then compares by time alone


def unpack_script(name: str) -> str:
    """Return the shell commands that unpack the archive into the project folder.

    Nothing on the cluster is ever deleted.
    """
    return f'dir={remote_dir(name)}\nmkdir -p "$dir" && tar -xzf - -C "$dir"\n'


def push(project: Path) -> tuple[int, int, int]:
    """Upload what is new or changed in the project.

    Return the number of files sent, the size of the archive and the
    number of files the cluster already had.
    """
    name = project_name(project)
    # Not a project, but perhaps the home folder with the SSH keys in it.
    if not any(project.glob(f"*{layout.JOB_SCRIPT_SUFFIX}")):
        raise Problem(
            f"This folder has no job script (*{layout.JOB_SCRIPT_SUFFIX}), so it "
            "is not a project. Go to your project folder first, with `cd`."
        )
    files = files_to_upload(project)
    there = parse_listing(ssh.run(ssh.EXPORT, listing_script(name)))
    last = last_pushed(project)
    looks: dict[str, Look] = {}
    kept: list[str] = []
    changed: list[Path] = []
    for file in files:
        path = file.as_posix()
        here = look(project, file)
        if here:
            looks[path] = here
        found = compare(here, there.get(path), last.get(path))
        if found == CLUSTER_NEWER:
            kept.append(path)
        elif found == HERE_NEWER:
            changed.append(file)
    if kept:
        raise Problem(newer_on_cluster(kept))
    size = 0
    if changed:
        with tempfile.TemporaryFile() as archive:
            pack(project, changed, archive)
            size = archive.tell()
            archive.seek(0)
            ssh.send(ssh.EXPORT, unpack_script(name), archive)
    save_pushed(project, looks)
    return len(changed), size, len(files) - len(changed)


def pack_script(name: str) -> str:
    """Return the shell commands that pack results/ and the Slurm output files.

    The names go to tar through a pipe, as a job of tens of thousands
    of runs would make too long a command line. --dereference: results/
    may be a link, for example into a workspace.
    --hard-dereference: a file with two names goes as two files, since pull
    unpacks no links.

    GNU tar exits 1 when a file changed while it read it, as happens while
    runs are still writing. The archive is complete all the same, so that
    case gets its own exit code instead of counting as a failure.
    """
    return (
        f"{enter_remote_dir(name)}set -- *{OUTPUT_SUFFIX}\n"
        '[ -e "$1" ] || [ -L "$1" ] || set --\n'
        f'[ -d {RESULTS} ] && set -- {RESULTS} "$@"\n'
        f'[ "$#" -gt 0 ] || exit {NOTHING_TO_PULL}\n'
        "printf '%s\\0' \"$@\" | "
        "tar -czf - --dereference --hard-dereference --null -T -\n"
        "code=$?\n"
        f'[ "$code" -eq 1 ] && exit {STILL_WRITING}\n'
        'exit "$code"\n'
    )


def refusal(member: tarfile.TarInfo, project: Path) -> str | None:
    """Why pull does not unpack this member of the archive; None if it does.

    Python's "data" filter refuses anything that would land outside the
    project folder. Beyond that, pull takes only what the pack script packs:
    results/ and the output files at the top, as plain files and folders. A
    link could make a later pull write anywhere.
    """
    try:
        tarfile.data_filter(member, str(project))
    except tarfile.FilterError as error:
        return str(error)
    path = member.name
    wanted = (
        path == RESULTS or path.startswith(f"{RESULTS}/") or is_output_file(Path(path))
    )
    if not wanted or not (member.isfile() or member.isdir()):
        return f"{path!r} is neither a file in {RESULTS}/ nor an output file"
    return None


def pull(project: Path) -> tuple[int, int, bool]:
    """Bring back results/ and the output files.

    Return the count, the size and whether some files were still being
    written, so that they may be cut off. Files with the same name on your
    computer are overwritten. Every file is checked before the first is
    written, so that a refusal changes nothing.
    """
    name = project_name(project)
    problems = {
        NOT_ON_CLUSTER: not_on_cluster(name),
        NOTHING_TO_PULL: f"Nothing to pull yet: {remote_label(name)} has no "
        f"{RESULTS}/ folder and no output files.",
    }
    with tempfile.TemporaryFile() as archive:
        # Still writing is no failure: the archive is complete, only perhaps
        # not every file in it, which pull then says.
        code = ssh.fetch(
            ssh.EXPORT, pack_script(name), archive, problems, fine={STILL_WRITING}
        )
        size = archive.tell()
        archive.seek(0)
        with tarfile.open(fileobj=archive, mode="r:gz") as tar:
            members = tar.getmembers()
            for member in members:
                if reason := refusal(member, project):
                    raise Problem(
                        f"Refused to unpack the results: {reason}. Nothing was changed."
                    )
            try:
                tar.extractall(project, filter="data")
            except OSError as error:
                if error.filename is None:  # such as a full disk
                    raise Problem(f"Could not unpack the results: {error}") from None
                raise Problem(
                    f"Could not write {error.filename}: {error.strerror}. Is it "
                    "open in another program, such as Excel? Close it and pull "
                    "again."
                ) from None
            files = [member for member in members if member.isfile()]
    return len(files), size, code == STILL_WRITING
