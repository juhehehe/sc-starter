"""Tests for submitting a job."""

import os
import sys

import pytest

from sc_starter import cli


@pytest.fixture
def project(tmp_path, monkeypatch):
    folder = tmp_path / "my-project"
    folder.mkdir()
    (folder / "job.slurm").write_bytes(b"#!/bin/bash\r\n#SBATCH --time=00:05:00\r\n")
    (folder / "runs.txt").write_text("echo 1\necho 2\necho 3\n")
    monkeypatch.chdir(folder)
    return folder


@pytest.mark.parametrize(
    ("lines", "array"),
    [("4\n", "4"), ("3\n1\n2\n", "1-3"), ("1\n2\n3\n7\n9\n10\n", "1-3,7,9-10")],
)
def test_submit_lines_joins_neighbours_into_ranges(project, fake_ssh, lines, array):
    (project / "runs.txt").write_text("".join(f"echo {n}\n" for n in range(1, 11)))
    (project / "failed.txt").write_text(lines)
    fake_ssh.reply("sc-login", stdout="28390003\n")

    cli.main(["submit", "--lines", "failed.txt"])

    assert f"--array={array} job.slurm" in fake_ssh.calls[-1]["command"]


def test_submit_lines_needs_the_file(project, fake_ssh, capsys):
    assert cli.main(["submit", "--lines", "failed.txt"]) == 1
    assert "failed.txt does not exist" in capsys.readouterr().err
    assert fake_ssh.calls == []


@pytest.mark.parametrize(
    "printed",
    ["28390001;sc\n", "Welcome to SC!\n28390001\n"],
    ids=["with the cluster name", "after a greeting from ~/.bashrc"],
)
def test_submit_reads_the_job_id_from_what_sbatch_printed(
    project, fake_ssh, capsys, printed
):
    fake_ssh.reply("sc-login", stdout=printed)

    assert cli.main(["submit"]) == 0
    assert "Submitted job 28390001 " in capsys.readouterr().out


def test_submit_refuses_anything_but_a_job_id(project, fake_ssh, capsys):
    fake_ssh.reply("sc-login", stdout="sbatch: queue closed; ls\n")

    assert cli.main(["submit"]) == 1

    assert "instead of a job ID" in capsys.readouterr().err
    assert not (project / ".sc-starter" / "last-job").exists()


def test_submit_sends_an_array_with_one_run_per_line(project, fake_ssh, capsys):
    fake_ssh.reply("sc-login", stdout="28390001\n")

    assert cli.main(["submit"]) == 0

    call = fake_ssh.calls[-1]
    assert call["host"] == "sc-login"
    assert "sbatch --parsable --array=1-3 job.slurm" in call["command"]
    assert "Submitted job 28390001 with runs 1-3" in capsys.readouterr().out


def test_submit_uploads_what_changed_before_it_submits(project, fake_ssh, capsys):
    fake_ssh.reply("sc-login", stdout="28390001\n")

    assert cli.main(["submit"]) == 0
    out = capsys.readouterr().out
    assert out.startswith("Uploaded 2 files")
    assert "Submitted job 28390001 with runs 1-3" in out

    look, send, sbatch = fake_ssh.calls
    assert [look["host"], send["host"], sbatch["host"]] == [
        "sc-export",
        "sc-export",
        "sc-login",
    ]
    assert fake_ssh.uploaded(1) == {
        "job.slurm": b"#!/bin/bash\n#SBATCH --time=00:05:00\n",
        "runs.txt": b"echo 1\necho 2\necho 3\n",
    }


def test_submit_without_changes_submits_without_uploading(project, fake_ssh, capsys):
    fake_ssh.cluster_has(project, "job.slurm", "runs.txt")
    fake_ssh.reply("sc-login", stdout="28390001\n")

    assert cli.main(["submit"]) == 0

    assert [call["host"] for call in fake_ssh.calls] == ["sc-export", "sc-login"]
    assert capsys.readouterr().out.startswith("Submitted job 28390001")


def test_submit_without_runs_sends_a_single_job(project, fake_ssh):
    (project / "runs.txt").unlink()
    fake_ssh.reply("sc-login", stdout="28390002\n")

    cli.main(["submit"])

    assert "sbatch --parsable job.slurm" in fake_ssh.calls[-1]["command"]


def test_submit_lines_sends_only_the_listed_runs(project, fake_ssh):
    (project / "failed.txt").write_text("1\n3\n")
    fake_ssh.reply("sc-login", stdout="28390003\n")

    cli.main(["submit", "--lines", "failed.txt"])

    assert "--array=1,3 job.slurm" in fake_ssh.calls[-1]["command"]


def test_submit_keeps_its_notes_out_of_git(project, fake_ssh):
    fake_ssh.reply("sc-login", stdout="28390004\n")

    cli.main(["submit"])

    assert (project / ".sc-starter" / ".gitignore").read_text().endswith("\n*\n")


def test_submit_runs_another_script_once(project, fake_ssh, capsys):
    (project / "setup.slurm").write_text("#!/bin/bash\n")
    fake_ssh.reply("sc-login", stdout="28390005\n")

    assert cli.main(["submit", "setup.slurm"]) == 0

    command = fake_ssh.calls[-1]["command"]
    assert "sbatch --parsable setup.slurm" in command
    assert "runs.txt" not in command
    assert "Submitted job 28390005." in capsys.readouterr().out


@pytest.mark.parametrize("typed", [".\\setup.slurm", "./setup.slurm"])
def test_submit_takes_a_script_written_with_its_folder(project, fake_ssh, typed):
    """Tab completion in PowerShell writes .\\setup.slurm."""
    (project / "setup.slurm").write_text("#!/bin/bash\n")
    fake_ssh.reply("sc-login", stdout="28390005\n")

    assert cli.main(["submit", typed]) == 0
    assert "sbatch --parsable setup.slurm" in fake_ssh.calls[-1]["command"]


def test_submit_lines_belongs_to_the_job_script(project, fake_ssh, capsys):
    (project / "setup.slurm").write_text("#!/bin/bash\n")
    (project / "failed.txt").write_text("1\n")

    assert cli.main(["submit", "setup.slurm", "--lines", "failed.txt"]) == 1
    assert "--lines needs job.slurm" in capsys.readouterr().err
    assert fake_ssh.calls == []


def test_submit_needs_a_job_script(project, fake_ssh, capsys):
    (project / "job.slurm").unlink()

    assert cli.main(["submit"]) == 1
    assert "no job.slurm" in capsys.readouterr().err
    assert fake_ssh.calls == []


@pytest.mark.skipif(sys.platform == "win32", reason="Ctrl+C is a signal on Unix")
def test_submit_stopped_with_ctrl_c_says_the_job_may_run(project, fake_ssh, capsys):
    fake_ssh.reply("sc-login", stdout="28390001\n", interrupt=True)

    assert cli.main(["submit"]) == 1

    assert "may run anyway" in capsys.readouterr().err


def test_submit_says_the_job_runs_when_its_note_cannot_be_kept(
    project, fake_ssh, capsys
):
    (project / ".sc-starter").write_text("a file where the folder belongs")
    fake_ssh.reply("sc-login", stdout="28390001\n")

    assert cli.main(["submit"]) == 1

    err = capsys.readouterr().err
    assert "Submitted job 28390001, but" in err
    assert "do not submit it again" in err


def test_submit_goes_on_after_a_damaged_last_job(project, fake_ssh, capsys):
    """As after the computer went off while submit wrote it."""
    (project / ".sc-starter").mkdir()
    (project / ".sc-starter" / "last-job").write_text("")
    fake_ssh.reply("sc-login", stdout="28390001\n")

    assert cli.main(["submit"]) == 0


def test_submit_keeps_a_note_when_slurm_gives_an_id_again(project, fake_ssh):
    fake_ssh.reply("sc-login", stdout="28390001\n")
    cli.main(["submit"])

    assert cli.main(["submit"]) == 0


def test_submit_hands_the_pushed_job_script_to_sbatch(project, cluster, capsys):
    assert cli.main(["submit"]) == 0

    assert cluster.jobs == {"28390001": "--parsable --array=1-3 job.slurm"}
    assert (cluster.folder() / "runs.txt").read_text() == "echo 1\necho 2\necho 3\n"
    assert "Submitted job 28390001 with runs 1-3" in capsys.readouterr().out


def test_submit_submits_nothing_when_the_upload_fails(project, cluster, capsys):
    cluster.stand_in("tar", "echo 'tar: job.slurm: Disk quota exceeded' >&2\nexit 2")

    assert cli.main(["submit"]) == 1

    assert "Disk quota exceeded" in capsys.readouterr().err
    assert cluster.jobs == {}
    assert not (project / ".sc-starter" / "last-job").exists()


def test_submit_waits_for_the_setup_job(project, cluster, capsys):
    """job.slurm needs the packages that setup.slurm installs."""
    (project / "setup.slurm").write_text("#!/bin/bash\n")
    cli.main(["submit", "setup.slurm"])
    cluster.queue("28390001|RUNNING|None|t001|0:10\n")

    assert cli.main(["submit"]) == 1
    assert "setup.slurm (job 28390001) has not finished" in capsys.readouterr().err
    assert list(cluster.jobs) == ["28390001"]

    cluster.queue("")
    assert cli.main(["submit"]) == 0
    assert list(cluster.jobs) == ["28390001", "28390002"]


def test_submit_keeps_a_checkpoint_the_job_wrote_on_the_cluster(
    project, cluster, capsys
):
    """A checkpoint from a trial run here must not replace the job's newer one."""
    (project / "checkpoint.pickle").write_bytes(b"round 2")
    cli.main(["submit"])
    there = cluster.folder() / "checkpoint.pickle"
    there.write_bytes(b"round 9")
    os.utime(there, (there.stat().st_mtime + 60,) * 2)
    capsys.readouterr()

    assert cli.main(["submit"]) == 1

    assert "checkpoint.pickle" in capsys.readouterr().err
    assert there.read_bytes() == b"round 9"
    assert list(cluster.jobs) == ["28390001"]
