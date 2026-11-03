"""Shared test fixtures."""

import io
import json
import sys
import tarfile
from pathlib import Path

import pytest

from sc_starter import ssh, transfer

FAKE_SSH = Path(__file__).with_name("fake_ssh.py")
LOCAL_CLUSTER = Path(__file__).with_name("local_cluster.py")
LOCAL_SLURM = Path(__file__).with_name("local_slurm")


class FakeSsh:
    """Sets the replies of the fake ssh and reads back the calls it got."""

    def __init__(self, folder: Path) -> None:
        self.folder = folder
        self.replies: dict[str, dict] = {}

    def reply(
        self,
        host: str,
        *,
        stdout: str | bytes = "",
        stderr: str = "",
        code: int = 0,
        interrupt: bool = False,
    ):
        """Set what the fake ssh prints and returns for calls to `host`.

        `interrupt` presses Ctrl+C while the call runs.
        """
        stdout_file = self.folder / f"{host}.stdout"
        if isinstance(stdout, str):
            stdout = stdout.encode()
        stdout_file.write_bytes(stdout)
        self.replies[host] = {
            "stdout_file": str(stdout_file),
            "stderr": stderr,
            "code": code,
            "interrupt": interrupt,
        }
        (self.folder / "replies.json").write_text(json.dumps(self.replies))

    @property
    def calls(self) -> list[dict]:
        files = sorted(
            self.folder.glob("call-*.json"), key=lambda path: int(path.stem[5:])
        )
        return [json.loads(path.read_text()) for path in files]

    def stdin(self, number: int) -> bytes:
        """What call number `number` (counting from 0) got on its input."""
        return (self.folder / f"call-{number}.stdin").read_bytes()

    def archive(self, number: int = -1) -> tarfile.TarFile:
        """The archive a call got on its input, as push sends it.

        `number` counts from 0, as in stdin(); without it, the last call.
        """
        if number < 0:
            number += len(self.calls)
        return tarfile.open(fileobj=io.BytesIO(self.stdin(number)))

    def uploaded(self, number: int = -1) -> dict[str, bytes]:
        """Name and content of every file in the archive of a call."""
        with self.archive(number) as tar:
            return {m.name: tar.extractfile(m).read() for m in tar.getmembers()}

    def cluster_has(self, project: Path, *names: str, age: float = 0) -> None:
        """Make the export node list `names` of `project` as push left them.

        `age` makes the copies there that many seconds older than here, or
        newer when it is below 0.
        """
        entries = []
        for name in names:
            path = project / name
            if transfer.needs_unix_line_endings(name):
                size = len(transfer.unix_text(path))
            else:
                size = path.stat().st_size
            entries.append(f"{size} {path.stat().st_mtime - age:.7f} {name}\0")
        self.reply("sc-export", stdout="".join(entries))


class LocalCluster:
    """A stand-in cluster on this computer: one home folder, and stand-ins for Slurm."""

    def __init__(self, folder: Path) -> None:
        self.home = folder / "home"
        self.bin = folder / "bin"  # stand-ins a test adds, see stand_in()
        self.slurm = folder / "slurm"  # what the Slurm stand-ins read and write
        for made in (self.home, self.bin, self.slurm):
            made.mkdir(parents=True)

    def folder(self, name: str = "my-project") -> Path:
        """The cluster folder of a project."""
        return self.home / "sc-projects" / name

    @property
    def calls(self) -> list[dict]:
        path = self.home.parent / "calls.jsonl"
        if not path.exists():
            return []
        return [json.loads(line) for line in path.read_text().splitlines()]

    @property
    def jobs(self) -> dict[str, str]:
        """What sbatch got, by job ID."""
        folder = self.slurm / "jobs"
        if not folder.exists():
            return {}
        return {job.name: job.read_text().strip() for job in sorted(folder.iterdir())}

    def queue(self, text: str) -> None:
        """Set the lines squeue prints, in its format `%i|%T|%r|%N|%M`."""
        (self.slurm / "queue").write_text(text)

    def accounting(self, text: str) -> None:
        """Set the lines sacct prints: JobID|State|ExitCode|NodeList|Elapsed."""
        (self.slurm / "accounting").write_text(text)

    def stand_in(self, command: str, script: str) -> None:
        """Replace `command` on the cluster with a shell script."""
        path = self.bin / command
        path.write_text(f"#!/bin/sh\n{script}\n")
        path.chmod(0o755)


@pytest.fixture(autouse=True)
def no_real_ssh(monkeypatch) -> None:
    """Make every test that reaches for the real ssh fail, loudly."""
    monkeypatch.setattr(
        ssh, "SSH", [sys.executable, "-c", "raise SystemExit('real ssh in a test')"]
    )


@pytest.fixture
def fake_ssh(tmp_path, monkeypatch) -> FakeSsh:
    """Replace ssh with tests/fake_ssh.py for one test."""
    folder = tmp_path / "fake-ssh"
    folder.mkdir()
    monkeypatch.setenv("FAKE_SSH_DIR", str(folder))
    monkeypatch.setattr(ssh, "SSH", [sys.executable, str(FAKE_SSH)])
    return FakeSsh(folder)


@pytest.fixture
def cluster(tmp_path, monkeypatch) -> LocalCluster:
    """Replace ssh with tests/local_cluster.py for one test."""
    if sys.platform != "linux":
        pytest.skip("the cluster runs Linux, with GNU tar and GNU find")
    local = LocalCluster(tmp_path / "cluster")
    monkeypatch.setenv("LOCAL_CLUSTER_HOME", str(local.home))
    monkeypatch.setenv("LOCAL_CLUSTER_BIN", f"{local.bin}:{LOCAL_SLURM}")
    monkeypatch.setenv("LOCAL_CLUSTER_SLURM", str(local.slurm))
    monkeypatch.setattr(ssh, "SSH", [sys.executable, str(LOCAL_CLUSTER)])
    return local
