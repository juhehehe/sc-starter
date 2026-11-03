"""Tests for showing how the runs of a job go, and their output files."""

import codecs
import io
import sys

import pytest

from sc_starter import cli, layout, notes, slurm

QUEUE = "28390001_3|RUNNING|None|t004|0:42\n28390001_4|PENDING|Priority||0:00\n"
ACCOUNTING = (
    "28390001_1|COMPLETED|0:0|t004|00:00:05\n"
    "28390001_2|FAILED|1:0|t005|00:00:03\n"
    "28390001_3|RUNNING|0:0|t004|00:00:42\n"
    "28390001_[4]|PENDING|0:0|None assigned|00:00:00\n"
)


def slurm_lists(accounting: str = "", queue: str = "") -> str:
    """What the status call prints when squeue and sacct list these lines."""
    return f"{queue}{slurm.SEPARATOR}\n{accounting}"


OUTPUT = slurm_lists(ACCOUNTING, QUEUE)


@pytest.fixture
def project(tmp_path, monkeypatch):
    """A project that submitted job 28390001 with four runs."""
    folder = tmp_path / "my-project"
    folder.mkdir()
    (folder / "job.slurm").write_text("#!/bin/bash\n")
    (folder / "runs.txt").write_text("echo 1\nexit 1\nsleep 60\necho 4\n")
    notes.save(folder, "28390001", "job.slurm", [1, 2, 3, 4])
    monkeypatch.chdir(folder)
    return folder


def test_the_first_job_of_the_guide(tmp_path, monkeypatch, fake_ssh, capsys):
    """first-jobs/hello.slurm from Your first job: one job, without runs.txt."""
    folder = tmp_path / "first-jobs"
    folder.mkdir()
    (folder / "hello.slurm").write_text("#!/bin/bash\n#SBATCH --output=%x-%j.out\n")
    monkeypatch.chdir(folder)

    fake_ssh.reply("sc-login", stdout="28412452\n")
    assert cli.main(["submit", "hello.slurm"]) == 0
    capsys.readouterr()

    accounting = "28412452|COMPLETED|0:0|t002|00:00:00\n"
    fake_ssh.reply("sc-login", stdout=slurm_lists(accounting))
    assert cli.main(["status"]) == 0
    assert capsys.readouterr().out == (
        "Job 28412452: 1 COMPLETED\n"
        "\n"
        "run  state      exit  node  elapsed\n"
        "-    COMPLETED  0:0   t002  00:00:00\n"
    )

    fake_ssh.reply("sc-export", stdout="Job:   28412452\n")
    assert cli.main(["log"]) == 0
    assert capsys.readouterr().out == "Job:   28412452\n"
    assert "*-28412452.out" in fake_ssh.calls[-1]["command"]


def test_status_lists_runs_that_never_started_one_by_one(project, fake_ssh, capsys):
    """sacct writes them in one line, with a limit of runs at a time: %2."""
    accounting = (
        "28390001_1|COMPLETED|0:0|t004|00:00:05\n"
        "28390001_[2-4%2]|CANCELLED by 12345|0:0|None assigned|00:00:00\n"
    )
    fake_ssh.reply("sc-login", stdout=slurm_lists(accounting))

    cli.main(["status"])

    assert "Job 28390001: 3 CANCELLED, 1 COMPLETED" in capsys.readouterr().out


def test_status_lists_runs_cancelled_before_they_started(project, fake_ssh, capsys):
    # The line sacct wrote on the cluster for an array cancelled while waiting.
    cancelled = "28390001_[1-4]|CANCELLED by 12345|0:0|None assigned|00:00:00\n"
    fake_ssh.reply("sc-login", stdout=slurm_lists(cancelled))

    cli.main(["status"])

    assert "Job 28390001: 4 CANCELLED" in capsys.readouterr().out
    assert (project / "failed.txt").read_text() == "1\n2\n3\n4\n"


def test_status_lists_every_run_of_an_array_cancelled_halfway(
    project, fake_ssh, capsys
):
    accounting = (
        "28390001_1|COMPLETED|0:0|t004|00:00:05\n"
        "28390001_2|CANCELLED by 12345|0:15|t004|00:00:10\n"
        "28390001_[3-4]|CANCELLED by 12345|0:0|None assigned|00:00:00\n"
    )
    fake_ssh.reply("sc-login", stdout=slurm_lists(accounting))

    cli.main(["status"])

    assert "Job 28390001: 3 CANCELLED, 1 COMPLETED" in capsys.readouterr().out
    assert (project / "failed.txt").read_text() == "2\n3\n4\n"


def test_status_shows_commands_without_what_windows_adds(project, fake_ssh, capsys):
    """The mark PowerShell puts before UTF-8, and Windows line endings."""
    (project / "runs.txt").write_bytes(codecs.BOM_UTF8 + b"echo 1\r\n")
    fake_ssh.reply("sc-login", stdout="28390002\n")
    cli.main(["submit"])
    accounting = "28390002_1|COMPLETED|0:0|t004|00:00:05\n"
    fake_ssh.reply("sc-login", stdout=slurm_lists(accounting))
    capsys.readouterr()

    cli.main(["status"])

    assert capsys.readouterr().out.splitlines()[-1].endswith("00:00:05  echo 1")


def test_status_of_a_job_named_by_its_id(project, fake_ssh, capsys):
    notes.save(project, "28390009", "job.slurm", None)
    fake_ssh.reply("sc-login", stdout=OUTPUT)

    cli.main(["status", "28390001"])

    out = capsys.readouterr().out
    assert out.startswith("Job 28390001: 1 COMPLETED, 1 FAILED")
    assert "exit 1" in out


def test_status_of_a_job_from_elsewhere_lists_the_runs_in_order(
    project, fake_ssh, capsys
):
    accounting = (
        "28390077_3|COMPLETED|0:0|t004|00:00:05\n"
        "28390077_1|COMPLETED|0:0|t004|00:00:05\n"
        "28390077_2|FAILED|1:0|t004|00:00:05\n"
    )
    fake_ssh.reply("sc-login", stdout=slurm_lists(accounting))

    cli.main(["status", "28390077"])

    rows = capsys.readouterr().out.splitlines()[3:6]
    assert [row.split()[0] for row in rows] == ["1", "2", "3"]


def test_log_of_a_job_named_by_its_id(project, fake_ssh, capsys):
    notes.save(project, "28390009", "job.slurm", None)

    cli.main(["log", "--job", "28390001", "3"])

    assert "*-28390001_3.out" in fake_ssh.calls[-1]["command"]


def test_status_shows_every_run_with_its_command(project, fake_ssh, capsys):
    fake_ssh.reply("sc-login", stdout=OUTPUT)

    assert cli.main(["status"]) == 0

    out = capsys.readouterr().out
    assert "Job 28390001: 1 COMPLETED, 1 FAILED, 1 PENDING, 1 RUNNING" in out
    assert "PENDING (Priority)" in out
    [row_of_run_2] = [line for line in out.splitlines() if line.startswith("2 ")]
    assert row_of_run_2.endswith("exit 1")
    assert "squeue --jobs=28390001" in fake_ssh.calls[0]["command"]


def test_status_shows_the_commands_as_submitted(project, fake_ssh, capsys):
    fake_ssh.reply("sc-login", stdout="28390002\n")
    cli.main(["submit"])
    (project / "runs.txt").write_text("echo changed\n")
    accounting = "28390002_1|COMPLETED|0:0|t004|00:00:05\n"
    fake_ssh.reply("sc-login", stdout=slurm_lists(accounting))
    capsys.readouterr()

    cli.main(["status"])

    out = capsys.readouterr().out
    assert "echo 1" in out
    assert "echo changed" not in out


@pytest.mark.parametrize("state", ["TIMEOUT", "OUT_OF_MEMORY", "NODE_FAIL"])
def test_status_counts_every_end_but_completed_as_failed(project, fake_ssh, state):
    accounting = (
        "28390001_1|COMPLETED|0:0|t004|00:00:05\n"
        f"28390001_2|{state}|0:0|t003|00:02:15\n"
        "28390001_3|COMPLETED|0:0|t004|00:00:05\n"
        "28390001_4|COMPLETED|0:0|t004|00:00:05\n"
    )
    fake_ssh.reply("sc-login", stdout=slurm_lists(accounting))

    cli.main(["status"])

    assert (project / "failed.txt").read_text() == "2\n"


def test_status_writes_failed_runs_for_a_second_submit(project, fake_ssh, capsys):
    fake_ssh.reply("sc-login", stdout=OUTPUT)

    cli.main(["status"])

    assert (project / "failed.txt").read_text() == "2\n"
    assert "submit --lines failed.txt" in capsys.readouterr().out


def test_status_says_to_wait_for_runs_still_going(project, fake_ssh, capsys):
    """Submitting at once would make status follow only the new job."""
    fake_ssh.reply("sc-login", stdout=OUTPUT)

    cli.main(["status"])

    out = capsys.readouterr().out
    assert "Once the runs still waiting or running have ended, submit" in out


def test_status_removes_failed_runs_of_an_earlier_job(project, fake_ssh, capsys):
    """The runs in failed.txt were submitted again and have passed since."""
    (project / "failed.txt").write_text("2\n")
    passed = ACCOUNTING.replace("FAILED|1:0", "COMPLETED|0:0")
    fake_ssh.reply("sc-login", stdout=slurm_lists(passed))

    cli.main(["status"])

    assert not (project / "failed.txt").exists()
    assert "removed the old failed.txt" in capsys.readouterr().out


def test_status_of_a_failed_single_job_keeps_failed_txt(project, fake_ssh, capsys):
    """failed.txt is for `submit --lines`, which a job without runs cannot use."""
    (project / "failed.txt").write_text("2\n")
    notes.save(project, "28390009", "job.slurm", None)
    fake_ssh.reply("sc-login", stdout=slurm_lists("28390009|FAILED|1:0|t004|0:01\n"))

    assert cli.main(["status"]) == 0

    assert "1 FAILED" in capsys.readouterr().out.splitlines()[0]
    assert (project / "failed.txt").read_text() == "2\n"


def test_status_marks_runs_slurm_does_not_list(project, fake_ssh, capsys):
    first_line = ACCOUNTING.splitlines()[0]
    fake_ssh.reply("sc-login", stdout=slurm_lists(f"{first_line}\n"))

    cli.main(["status"])

    assert "1 COMPLETED, 3 UNKNOWN" in capsys.readouterr().out
    assert not (project / "failed.txt").exists()


def test_status_says_so_when_slurm_does_not_know_the_job(project, fake_ssh, capsys):
    fake_ssh.reply("sc-login", stdout=slurm_lists())

    cli.main(["status"])

    assert "Slurm does not list job 28390001" in capsys.readouterr().out


def test_status_refuses_a_job_id_that_is_not_a_number(project, fake_ssh, capsys):
    assert cli.main(["status", "123; echo injected"]) == 1
    assert "not a job ID" in capsys.readouterr().err
    assert fake_ssh.calls == []


def test_status_refuses_a_last_job_that_is_not_a_job_id(project, fake_ssh, capsys):
    (project / ".sc-starter" / "last-job").write_text("123; echo injected\n")

    assert cli.main(["status"]) == 1
    assert "does not hold a job ID" in capsys.readouterr().err
    assert fake_ssh.calls == []


def test_status_without_any_job_says_so(tmp_path, monkeypatch, fake_ssh, capsys):
    monkeypatch.chdir(tmp_path)

    assert cli.main(["status"]) == 1
    assert "No job was submitted from this folder" in capsys.readouterr().err


def test_log_prints_the_output_file_of_one_run(project, fake_ssh, capsys):
    fake_ssh.reply("sc-export", stdout="fitting run 3\n")

    assert cli.main(["log", "3"]) == 0

    assert capsys.readouterr().out == "fitting run 3\n"
    [call] = fake_ssh.calls
    assert call["host"] == "sc-export"
    assert "*-28390001_3.out" in call["command"]


def test_log_into_a_file_on_windows_writes_what_its_code_page_lacks(
    project, fake_ssh, monkeypatch
):
    """Windows writes into files and pipes in the ANSI code page, cp1252 here."""
    fake_ssh.reply("sc-export", stdout="Batches: 100%|██| 2/2\n".encode())
    written = io.BytesIO()
    monkeypatch.setattr(
        sys, "stdout", io.TextIOWrapper(written, encoding="cp1252", newline="\n")
    )

    assert cli.main(["log", "3"]) == 0

    sys.stdout.flush()
    assert written.getvalue() == b"Batches: 100%|??| 2/2\n"


def test_log_asks_which_run_of_an_array(project, fake_ssh, capsys):
    assert cli.main(["log"]) == 1
    assert "Which run?" in capsys.readouterr().err


def test_log_says_when_there_is_no_output_yet(project, fake_ssh, capsys):
    fake_ssh.reply("sc-export", code=layout.NO_OUTPUT)

    assert cli.main(["log", "4"]) == 1
    assert "no output file *-28390001_4.out" in capsys.readouterr().err


def test_log_says_when_the_project_is_not_on_the_cluster(project, cluster, capsys):
    assert cli.main(["log", "3"]) == 1

    err = capsys.readouterr().err
    assert "There is no ~/sc-projects/my-project on the cluster" in err


def test_log_reads_the_output_file_on_the_cluster(project, cluster, capsys):
    cluster.folder().mkdir(parents=True)
    (cluster.folder() / "fit-28390001_3.out").write_text("fitting run 3\n")
    (cluster.folder() / "fit-28390001_30.out").write_text("fitting run 30\n")

    assert cli.main(["log", "3"]) == 0
    assert capsys.readouterr().out == "fitting run 3\n"

    assert cli.main(["log", "4"]) == 1
    assert "no output file *-28390001_4.out" in capsys.readouterr().err


def test_status_leaves_out_the_reason_none(project, fake_ssh, capsys):
    queue = "28390001_1|PENDING|None||0:00\n"
    fake_ssh.reply("sc-login", stdout=slurm_lists(queue=queue))

    cli.main(["status"])

    out = capsys.readouterr().out
    assert "PENDING" in out
    assert "(None)" not in out


@pytest.mark.parametrize(
    "damaged",
    ["", "null", '{"array": 5}'],
    ids=["cut off", "no object", "array not a spec"],
)
def test_status_with_a_damaged_job_note_shows_what_slurm_lists(
    project, fake_ssh, capsys, damaged
):
    """As after the computer went off while submit wrote the note."""
    (project / ".sc-starter" / "jobs" / "28390001" / "job.json").write_text(damaged)
    fake_ssh.reply("sc-login", stdout=OUTPUT)

    assert cli.main(["status"]) == 0
    assert "Job 28390001: 1 COMPLETED, 1 FAILED" in capsys.readouterr().out


def test_log_refuses_a_run_the_job_does_not_have(project, fake_ssh, capsys):
    assert cli.main(["log", "7"]) == 1
    assert "Job 28390001 has no run 7" in capsys.readouterr().err
    assert fake_ssh.calls == []


def test_log_says_when_the_output_file_is_empty(project, fake_ssh, capsys):
    fake_ssh.reply("sc-export", stdout="")

    assert cli.main(["log", "3"]) == 0
    assert "is empty" in capsys.readouterr().out


def test_log_of_a_job_from_elsewhere_asks_which_run(project, cluster, capsys):
    """Submitted by hand, so there is no job note: its output files tell."""
    cluster.folder().mkdir(parents=True)
    (cluster.folder() / "fit-28390077_1.out").write_text("fit 1\n")

    assert cli.main(["log", "--job", "28390077"]) == 1

    err = capsys.readouterr().err
    assert "Which run?" in err
    assert "`sc-starter log --job 28390077 3`" in err


def test_log_of_a_single_job_from_elsewhere(project, cluster, capsys):
    cluster.folder().mkdir(parents=True)
    (cluster.folder() / "hello-28390078.out").write_text("hello\n")

    assert cli.main(["log", "--job", "28390078"]) == 0
    assert capsys.readouterr().out == "hello\n"


def test_log_asks_which_run_of_a_script_with_its_own_array(project, cluster, capsys):
    """sweep.slurm says #SBATCH --array itself, so the note knows no runs."""
    (project / "sweep.slurm").write_text("#!/bin/bash\n#SBATCH --array=1-10\n")
    notes.save(project, "28390009", "sweep.slurm", None)
    cluster.folder().mkdir(parents=True)
    (cluster.folder() / "sweep-28390009_3.out").write_text("run 3\n")

    assert cli.main(["log"]) == 1
    assert "Which run?" in capsys.readouterr().err

    assert cli.main(["log", "3"]) == 0
    assert capsys.readouterr().out == "run 3\n"
