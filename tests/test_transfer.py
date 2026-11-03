"""Tests for uploading a project."""

import codecs
import os
import sys
from pathlib import Path

import pytest

from sc_starter import Problem, cli, transfer


@pytest.fixture
def project(tmp_path, monkeypatch):
    """A small project folder with the usual things that must stay local."""
    folder = tmp_path / "my-project"
    files = {
        "job.slurm": b"#!/bin/bash\r\n#SBATCH --time=00:05:00\r\n",
        "setup.slurm": b"#!/bin/bash\r\n",
        "runs.txt": b"python fit.py 1\r\npython fit.py 2\r\n",
        "fit.py": b"print('fit')\r\n",
        "data/input.csv": b"a,b\n1,2\n",
        "data/__pycache__/x.pyc": b"",
        "renv/activate.R": b"# renv\n",
        "renv/library/pkg/DESCRIPTION": b"",
        "results/old.csv": b"",
        "fit-123_1.out": b"",
        "failed.txt": b"2\n",
        ".venv/pyvenv.cfg": b"",
        ".git/config": b"",
    }
    for name, content in files.items():
        path = folder / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    monkeypatch.chdir(folder)
    return folder


def test_push_sends_the_project_without_local_things(project, fake_ssh, capsys):
    assert cli.main(["push"]) == 0

    assert sorted(fake_ssh.uploaded()) == [
        "data/input.csv",
        "fit.py",
        "job.slurm",
        "renv/activate.R",
        "runs.txt",
        "setup.slurm",
    ]
    assert "Uploaded 6 files" in capsys.readouterr().out


def test_push_uses_the_export_node_and_the_project_folder(project, fake_ssh):
    cli.main(["push"])

    look, send = fake_ssh.calls
    for call in (look, send):
        assert call["host"] == "sc-export"
        assert 'dir="$HOME"/sc-projects/my-project' in call["command"]
    assert fake_ssh.stdin(0) == b""
    assert fake_ssh.stdin(1).startswith(b"\x1f\x8b")  # the gzip archive


def test_push_sends_only_what_is_new_or_changed(project, fake_ssh, capsys):
    """fit.py is on the cluster as it is here; input.csv changed here since."""
    fake_ssh.cluster_has(project, "fit.py", "data/input.csv")
    (project / "data" / "input.csv").write_bytes(b"a,b\n1,2\n3,4\n")

    cli.main(["push"])

    assert sorted(fake_ssh.uploaded()) == [
        "data/input.csv",
        "job.slurm",
        "renv/activate.R",
        "runs.txt",
        "setup.slurm",
    ]
    assert "Uploaded 5 files (0.0 MB)" in capsys.readouterr().out


def test_push_sends_a_file_changed_without_changing_its_size(project, fake_ssh):
    """fit.py is on the cluster with the same size, from a minute earlier."""
    fake_ssh.cluster_has(project, "fit.py", age=60)

    cli.main(["push"])

    assert "fit.py" in fake_ssh.uploaded()


def test_push_keeps_a_newer_copy_on_the_cluster(project, fake_ssh, capsys):
    """fit.py was changed on the cluster a minute after this one."""
    fake_ssh.cluster_has(project, "fit.py", age=-60)

    assert cli.main(["push"]) == 1

    err = capsys.readouterr().err
    assert "The cluster has a newer copy of these files" in err
    assert "\n  fit.py\n" in err
    assert len(fake_ssh.calls) == 1  # only the listing; nothing was sent


def test_push_counts_what_the_cluster_already_has(project, fake_ssh, capsys):
    fake_ssh.cluster_has(project, "fit.py", "renv/activate.R")

    cli.main(["push"])

    assert "Uploaded 4 files (0.0 MB)" in (out := capsys.readouterr().out)
    assert out.rstrip().endswith("; 2 files unchanged")


def test_push_with_nothing_changed_sends_nothing(project, fake_ssh, capsys):
    """Job script and runs.txt have Windows line endings here, not there."""
    names = [
        "data/input.csv",
        "fit.py",
        "job.slurm",
        "renv/activate.R",
        "runs.txt",
        "setup.slurm",
    ]
    fake_ssh.cluster_has(project, *names)

    assert cli.main(["push"]) == 0

    assert len(fake_ssh.calls) == 1
    assert "Nothing to upload" in capsys.readouterr().out


def test_push_gives_job_script_and_runs_unix_line_endings(project, fake_ssh):
    cli.main(["push"])

    files = fake_ssh.uploaded()
    assert files["job.slurm"] == b"#!/bin/bash\n#SBATCH --time=00:05:00\n"
    assert files["runs.txt"] == b"python fit.py 1\npython fit.py 2\n"
    assert files["setup.slurm"] == b"#!/bin/bash\n"
    assert files["fit.py"] == b"print('fit')\r\n"


def test_push_drops_the_mark_windows_puts_before_utf8(project, fake_ssh):
    """PowerShell 5.1 and Excel start UTF-8 files with a byte order mark."""
    (project / "job.slurm").write_bytes(codecs.BOM_UTF8 + b"#!/bin/bash\r\n")
    (project / "runs.txt").write_bytes(codecs.BOM_UTF8 + b"python fit.py 1\r\n")

    cli.main(["push"])

    files = fake_ssh.uploaded()
    assert files["job.slurm"] == b"#!/bin/bash\n"
    assert files["runs.txt"] == b"python fit.py 1\n"


@pytest.mark.skipif(
    sys.platform == "win32", reason="chmod cannot take away read access on Windows"
)
def test_push_names_a_file_it_cannot_read(project, fake_ssh, capsys):
    unreadable = project / "data" / "input.csv"
    unreadable.chmod(0)
    try:
        assert cli.main(["push"]) == 1
    finally:
        unreadable.chmod(0o644)

    assert "Cannot read data/input.csv" in capsys.readouterr().err
    assert len(fake_ssh.calls) == 1  # only the listing; nothing was sent


def test_push_names_a_job_script_it_cannot_read_on_a_second_push(
    project, fake_ssh, capsys
):
    """job.slurm is on the cluster, and has changed since."""
    fake_ssh.cluster_has(project, "job.slurm", age=60)
    (project / "job.slurm").chmod(0)
    try:
        assert cli.main(["push"]) == 1
    finally:
        (project / "job.slurm").chmod(0o644)

    assert "Cannot read job.slurm" in capsys.readouterr().err
    assert len(fake_ssh.calls) == 1


@pytest.mark.skipif(sys.platform == "win32", reason="chmod does not lock folders")
def test_push_names_a_folder_it_cannot_read(project, fake_ssh, capsys):
    (project / "data").chmod(0)
    try:
        assert cli.main(["push"]) == 1
    finally:
        (project / "data").chmod(0o755)

    assert "Cannot read the folder data" in capsys.readouterr().err


needs_links = pytest.mark.skipif(
    sys.platform == "win32", reason="making links needs extra rights on Windows"
)


@needs_links
def test_push_sends_what_a_link_out_of_the_project_points_to(
    project, tmp_path, fake_ssh
):
    """Data on another drive, linked into the project, arrives on the cluster."""
    drive = tmp_path / "drive"
    (drive / "survey").mkdir(parents=True)
    (drive / "survey" / "wave1.csv").write_bytes(b"id\n1\n")
    (drive / "codebook.pdf").write_bytes(b"%PDF")
    (project / "survey").symlink_to(drive / "survey")
    (project / "data" / "codebook.pdf").symlink_to(
        Path("../..") / "drive" / "codebook.pdf"
    )

    cli.main(["push"])

    files = fake_ssh.uploaded()
    assert files["survey/wave1.csv"] == b"id\n1\n"
    assert files["data/codebook.pdf"] == b"%PDF"


@needs_links
def test_push_never_sends_ssh_keys_behind_a_link(project, tmp_path, fake_ssh):
    """A link to the home folder brings its files, but not the SSH keys."""
    home = tmp_path / "home"
    (home / ".ssh").mkdir(parents=True)
    (home / ".ssh" / "id_ed25519").write_bytes(b"private key")
    (home / "notes.txt").write_bytes(b"notes")
    (project / "home").symlink_to(home)

    cli.main(["push"])

    files = fake_ssh.uploaded()
    assert files["home/notes.txt"] == b"notes"
    assert not [path for path in files if ".ssh" in Path(path).parts]


@needs_links
def test_push_keeps_a_link_within_the_project_as_a_link(project, fake_ssh):
    (project / "latest.csv").symlink_to(Path("data") / "input.csv")

    cli.main(["push"])

    with fake_ssh.archive() as tar:
        link = tar.getmember("latest.csv")
    assert link.issym()
    assert link.linkname == "data/input.csv"


@needs_links
def test_push_stops_at_a_link_to_nothing(project, tmp_path, fake_ssh, capsys):
    """The drive with the data is not connected."""
    (project / "survey").symlink_to(tmp_path / "unplugged" / "survey")

    assert cli.main(["push"]) == 1

    assert "survey is a link to" in capsys.readouterr().err
    assert fake_ssh.calls == []


@needs_links
def test_push_stops_at_a_link_that_goes_round(project, tmp_path, fake_ssh, capsys):
    (project / "data" / "everything").symlink_to(tmp_path)

    assert cli.main(["push"]) == 1

    assert "would go round forever" in capsys.readouterr().err
    assert fake_ssh.calls == []


def test_push_refuses_a_folder_without_job_script(tmp_path, monkeypatch, capsys):
    """Such as the home folder, with the private SSH keys in it."""
    home = tmp_path / "home"
    (home / ".ssh").mkdir(parents=True)
    (home / ".ssh" / "id_ed25519").write_text("PRIVATE KEY\n")
    monkeypatch.chdir(home)

    assert cli.main(["push"]) == 1
    assert "no job script" in capsys.readouterr().err


def test_push_refuses_folder_names_unsafe_for_the_cluster(tmp_path, monkeypatch):
    folder = tmp_path / "my project"
    folder.mkdir()
    monkeypatch.chdir(folder)

    with pytest.raises(Problem, match="Rename the folder"):
        transfer.push(folder)


def test_push_unpacks_into_the_cluster_folder(project, cluster):
    assert cli.main(["push"]) == 0

    folder = cluster.folder()
    assert (folder / "data" / "input.csv").read_bytes() == b"a,b\n1,2\n"
    assert (folder / "job.slurm").read_bytes() == (
        b"#!/bin/bash\n#SBATCH --time=00:05:00\n"
    )
    assert not (folder / "results").exists()
    assert [call["host"] for call in cluster.calls] == ["sc-export", "sc-export"]


def test_what_went_up_counts_as_unchanged_on_the_next_push(project, cluster, capsys):
    (project / "my data.csv").write_bytes(b"x\n")
    cli.main(["push"])
    # What jobs leave there and push never sends stays out of the listing.
    for made_there in [".venv/pyvenv.cfg", "results/k-10.csv", "src/__pycache__/a.pyc"]:
        (cluster.folder() / made_there).parent.mkdir(parents=True, exist_ok=True)
        (cluster.folder() / made_there).write_bytes(b"")
    capsys.readouterr()

    assert cli.main(["push"]) == 0

    assert "Nothing to upload" in capsys.readouterr().out
    assert len(cluster.calls) == 3


def set_time(path: Path, seconds: float) -> None:
    os.utime(path, (seconds, seconds))


def test_push_keeps_a_copy_changed_on_the_cluster_since_it_went_up(
    project, cluster, capsys
):
    """Though the copy here was changed later still."""
    cli.main(["push"])
    went_up = (project / "fit.py").stat().st_mtime
    there = cluster.folder() / "fit.py"
    there.write_text("print('changed there')\n")
    set_time(there, went_up + 60)
    (project / "fit.py").write_text("print('changed here')\n")
    set_time(project / "fit.py", went_up + 120)

    assert cli.main(["push"]) == 1

    assert "\n  fit.py\n" in capsys.readouterr().err
    assert there.read_text() == "print('changed there')\n"


def test_push_sends_a_file_brought_back_with_an_older_time(project, cluster):
    """As from a backup: the copy on the cluster has not changed since push."""
    cli.main(["push"])
    restored = project / "fit.py"
    went_up = restored.stat().st_mtime
    restored.write_text("print('from the backup')\n")
    set_time(restored, went_up - 3600)

    assert cli.main(["push"]) == 0

    assert (cluster.folder() / "fit.py").read_text() == "print('from the backup')\n"
