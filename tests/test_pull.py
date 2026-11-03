"""Tests for bringing results back from the cluster."""

import io
import shutil
import tarfile

import pytest

from sc_starter import cli, layout


def archive_of(files: dict[str, bytes], links: dict[str, str] | None = None) -> bytes:
    """A gzip tar as the pack script on the cluster would print it.

    `links` adds symbolic links, by name and target.
    """
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as tar:
        for name, content in files.items():
            info = tarfile.TarInfo(name)
            info.size = len(content)
            tar.addfile(info, io.BytesIO(content))
        for name, target in (links or {}).items():
            info = tarfile.TarInfo(name)
            info.type, info.linkname = tarfile.SYMTYPE, target
            tar.addfile(info)
    return buffer.getvalue()


@pytest.fixture
def project(tmp_path, monkeypatch):
    folder = tmp_path / "my-project"
    (folder / "results").mkdir(parents=True)
    (folder / "results" / "run-1.csv").write_text("old\n")
    monkeypatch.chdir(folder)
    return folder


def test_pull_unpacks_results_and_output_files(project, fake_ssh, capsys):
    fake_ssh.reply(
        "sc-export",
        stdout=archive_of(
            {"results/run-1.csv": b"new\n", "fit-28390001_1.out": b"done\n"}
        ),
    )

    assert cli.main(["pull"]) == 0

    assert (project / "results" / "run-1.csv").read_text() == "new\n"
    assert (project / "fit-28390001_1.out").read_text() == "done\n"
    assert "Pulled 2 files" in capsys.readouterr().out
    assert fake_ssh.calls[0]["host"] == "sc-export"


def test_pull_refuses_files_outside_the_project(project, fake_ssh, capsys):
    fake_ssh.reply("sc-export", stdout=archive_of({"../outside.txt": b"x"}))

    assert cli.main(["pull"]) == 1

    assert "Refused to unpack" in capsys.readouterr().err
    assert not (project.parent / "outside.txt").exists()


@pytest.mark.parametrize(
    "archive",
    [
        archive_of({"results/run-1.csv": b"new\n", ".git/hooks/pre-commit": b"x"}),
        archive_of({"results/run-1.csv": b"new\n", "run.py": b"x"}),
        archive_of({"results/run-1.csv": b"new\n"}, links={"results/a": "../run.py"}),
    ],
    ids=["into .git", "over the code", "a link"],
)
def test_pull_unpacks_only_results_and_output_files(project, fake_ssh, capsys, archive):
    fake_ssh.reply("sc-export", stdout=archive)

    assert cli.main(["pull"]) == 1

    assert "Nothing was changed" in capsys.readouterr().err
    assert (project / "results" / "run-1.csv").read_text() == "old\n"
    assert sorted(path.name for path in project.iterdir()) == ["results"]


def test_pull_says_which_file_it_cannot_write(project, fake_ssh, capsys):
    """As when Excel has it open on Windows; here a folder is in its way."""
    (project / "results" / "run-2.csv").mkdir()
    fake_ssh.reply("sc-export", stdout=archive_of({"results/run-2.csv": b"new\n"}))

    assert cli.main(["pull"]) == 1
    assert "Could not write" in capsys.readouterr().err


@pytest.mark.parametrize(
    ("code", "stderr"),
    [
        (2, "tar: results/run-1.csv: Cannot open: Permission denied\n"),
        (255, "Connection to export01 closed by remote host.\n"),
    ],
    ids=["tar failed", "connection lost"],
)
def test_pull_changes_nothing_when_the_cluster_side_fails(
    project, fake_ssh, capsys, code, stderr
):
    fake_ssh.reply(
        "sc-export",
        stdout=archive_of({"results/run-1.csv": b"new\n"})[:30],
        stderr=stderr,
        code=code,
    )

    assert cli.main(["pull"]) == 1

    assert stderr.strip() in capsys.readouterr().err
    assert (project / "results" / "run-1.csv").read_text() == "old\n"


def test_pull_brings_back_results_and_output_files_only(project, cluster, capsys):
    folder = cluster.folder()
    (folder / "results").mkdir(parents=True)
    (folder / "results" / "run-1.csv").write_text("1\n")
    (folder / "fit-28390001_1.out").write_text("done\n")
    (folder / "fit.py").write_text("print('fit')\n")

    assert cli.main(["pull"]) == 0

    assert (project / "results" / "run-1.csv").read_text() == "1\n"
    assert (project / "fit-28390001_1.out").read_text() == "done\n"
    assert not (project / "fit.py").exists()
    assert "Pulled 2 files" in capsys.readouterr().out


def test_pull_explains_why_there_is_nothing(project, cluster, capsys):
    assert cli.main(["pull"]) == 1
    assert "Submit a job first with `sc-starter submit`" in capsys.readouterr().err

    cluster.folder().mkdir(parents=True)
    assert cli.main(["pull"]) == 1
    assert "Nothing to pull yet" in capsys.readouterr().err


def test_pull_follows_results_linked_to_a_workspace(project, tmp_path, cluster):
    """Large results can live in a workspace, with a link to it as results/."""
    workspace = tmp_path / "workspace" / "results"
    workspace.mkdir(parents=True)
    (workspace / "k-10.csv").write_text("10\n")
    cluster.folder().mkdir(parents=True)
    (cluster.folder() / "results").symlink_to(workspace)

    assert cli.main(["pull"]) == 0

    assert (project / "results" / "k-10.csv").read_text() == "10\n"
    assert not (project / "results").is_symlink()


def test_pull_brings_a_file_with_two_names_as_two_files(project, cluster):
    """GNU tar writes a second name of a file as a link, which pull refuses."""
    results = cluster.folder() / "results"
    results.mkdir(parents=True)
    (results / "run-1.csv").write_text("1\n")
    (results / "latest.csv").hardlink_to(results / "run-1.csv")

    assert cli.main(["pull"]) == 0

    assert (project / "results" / "latest.csv").read_text() == "1\n"


def test_pull_unpacks_what_came_while_runs_were_writing(project, fake_ssh, capsys):
    fake_ssh.reply(
        "sc-export",
        stdout=archive_of({"results/run-1.csv": b"half"}),
        code=layout.STILL_WRITING,
    )

    assert cli.main(["pull"]) == 0

    assert (project / "results" / "run-1.csv").read_text() == "half"
    assert "still being written" in capsys.readouterr().out


def test_pull_unpacks_while_runs_are_still_writing(project, cluster, capsys):
    """GNU tar exits 1 when a file changed while it read it; a stand-in does so."""
    (cluster.folder() / "results").mkdir(parents=True)
    (cluster.folder() / "results" / "run-1.csv").write_text("half")
    cluster.stand_in("tar", f'{shutil.which("tar")} "$@"\nexit 1')

    assert cli.main(["pull"]) == 0

    assert (project / "results" / "run-1.csv").read_text() == "half"
    out = capsys.readouterr().out
    assert "Pulled 1 file" in out
    assert "still being written" in out


def test_pull_changes_nothing_when_tar_fails_on_the_cluster(project, cluster, capsys):
    """Other than exit code 1, a failing tar leaves the archive incomplete."""
    (cluster.folder() / "results").mkdir(parents=True)
    (cluster.folder() / "results" / "run-1.csv").write_text("new\n")
    cluster.stand_in("tar", f'{shutil.which("tar")} "$@"\nexit 2')

    assert cli.main(["pull"]) == 1

    assert "exit code 2" in capsys.readouterr().err
    assert (project / "results" / "run-1.csv").read_text() == "old\n"
