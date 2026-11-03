"""The whole way of a project with runs, on a stand-in cluster on this computer."""

from sc_starter import cli


def test_submit_status_log_and_pull(tmp_path, monkeypatch, cluster, capsys):
    project = tmp_path / "my-project"
    project.mkdir()
    (project / "job.slurm").write_text(
        "#!/bin/bash\n#SBATCH --job-name=fit\n#SBATCH --output=%x-%A_%a.out\n"
    )
    (project / "runs.txt").write_text("python fit.py 1\npython fit.py 2\n")
    (project / "fit.py").write_text("print('fit')\n")
    monkeypatch.chdir(project)

    assert cli.main(["submit"]) == 0
    assert "Submitted job 28390001 with runs 1-2" in capsys.readouterr().out
    assert cluster.jobs == {"28390001": "--parsable --array=1-2 job.slurm"}

    # The runs end on the cluster, one of them failing.
    folder = cluster.folder()
    (folder / "fit-28390001_1.out").write_text("fit 1\n")
    (folder / "fit-28390001_2.out").write_text("Traceback\n")
    (folder / "results").mkdir()
    (folder / "results" / "fit-1.csv").write_text("k,1\n")
    cluster.accounting(
        "28390001_1|COMPLETED|0:0|t004|00:00:05\n28390001_2|FAILED|1:0|t005|00:00:03\n"
    )

    assert cli.main(["status"]) == 0
    out = capsys.readouterr().out
    assert out.startswith("Job 28390001: 1 COMPLETED, 1 FAILED")
    assert (project / "failed.txt").read_text() == "2\n"

    assert cli.main(["log", "2"]) == 0
    assert capsys.readouterr().out == "Traceback\n"

    assert cli.main(["pull"]) == 0
    assert (project / "results" / "fit-1.csv").read_text() == "k,1\n"
    assert (project / "fit-28390001_2.out").read_text() == "Traceback\n"

    assert cli.main(["submit", "--lines", "failed.txt"]) == 0
    assert cluster.jobs["28390002"] == "--parsable --array=2 job.slurm"
