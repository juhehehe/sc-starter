"""The way to the cluster: every remote step is one call of the ssh command.

The host names are the two short names that the setup guide writes into
~/.ssh/config: `sc-login` for Slurm commands and `sc-export` for copying
files, because SC stops file operations on the login node after 10 minutes.
OpenSSH on Windows cannot share one connection between calls, so each
command makes as few calls as it can.
"""

import subprocess
import sys
from collections.abc import Collection
from typing import IO

from sc_starter import Problem

LOGIN = "sc-login"
EXPORT = "sc-export"

# The ssh program. Tests replace it with a stand-in: one that plays back
# replies, or one that runs the commands on a stand-in cluster on this computer.
SSH = ["ssh"]

# BatchMode: never ask for a password or passphrase; the key comes from the
# SSH agent, as the setup guide arranges.
OPTIONS = ["-o", "BatchMode=yes"]

# Give up after a few seconds instead of hanging when the VPN is off. Not
# on Windows: its OpenSSH before 8.6 would wait that long on every call,
# and Windows itself gives up after about 20 seconds.
CONNECT_TIMEOUT = ["-o", "ConnectTimeout=10"]

# ssh exits with 255 when it failed itself; any other code comes from the
# remote command.
SSH_FAILED = 255

GUIDE = "the setup guide, docs/basics/setup.md"

UNREACHABLE = (
    "timed out",
    "No route to host",
    "Network is unreachable",
    "Could not resolve hostname",
)

BROKEN_OFF = ("closed by remote host", "Broken pipe", "Connection reset")


class CommandFailed(Problem):
    """The connection worked, but the command on the cluster failed."""

    def __init__(self, host: str, code: int, stderr: str) -> None:
        """Keep the host and the exit code, and say both in the message."""
        super().__init__(
            f"The command on {host} failed (exit code {code}).\n{stderr.strip()}"
        )
        self.code = code


# The exit codes a remote command uses for problems one can fix oneself,
# each with the message that says how; the codes are in layout.py. The
# caller knows its own command, so it passes them; any other code but 0
# ends as CommandFailed, unless the caller of fetch counts it as fine.
Problems = dict[int, str] | None


def run(host: str, remote_command: str, problems: Problems = None) -> str:
    """Run a short command on `host` and return what it printed."""
    result = _call(host, remote_command, problems)
    return result.stdout.decode("utf-8", errors="replace")


def send(
    host: str, remote_command: str, source: IO[bytes], problems: Problems = None
) -> None:
    """Run `remote_command` on `host` with the file `source` as its input."""
    _call(host, remote_command, problems, stdin=source)


def fetch(
    host: str,
    remote_command: str,
    target: IO[bytes],
    problems: Problems = None,
    fine: Collection[int] = (),
) -> int:
    """Run `remote_command` on `host` and write what it prints into `target`.

    Return its exit code: 0, or one of `fine`, the codes by which the
    command says something that is not a failure.
    """
    return _call(host, remote_command, problems, stdout=target, fine=fine).returncode


def _call(
    host: str,
    remote_command: str,
    problems: Problems,
    *,
    stdin=None,
    stdout=subprocess.PIPE,
    fine: Collection[int] = (),
) -> subprocess.CompletedProcess:
    options = OPTIONS if sys.platform == "win32" else [*OPTIONS, *CONNECT_TIMEOUT]
    try:
        result = subprocess.run(
            [*SSH, *options, host, remote_command],
            stdin=stdin,
            # Without input of its own, an empty one: else ssh would pass on
            # what is typed in the terminal. Not DEVNULL, on which the
            # OpenSSH 7.7 of Windows 10 1809 waits forever.
            input=b"" if stdin is None else None,
            stdout=stdout,
            stderr=subprocess.PIPE,
        )
    except FileNotFoundError:
        raise Problem(
            "The ssh command was not found. On Windows, add the optional "
            "feature 'OpenSSH Client'; macOS and Linux come with it."
        ) from None
    # ssh ends its own messages with \r\n, on every system.
    stderr = result.stderr.decode("utf-8", errors="replace").replace("\r\n", "\n")
    if result.returncode == SSH_FAILED:
        raise Problem(explain_ssh_failure(host, stderr))
    if problems and result.returncode in problems:
        raise Problem(problems[result.returncode])
    if result.returncode != 0 and result.returncode not in fine:
        raise CommandFailed(host, result.returncode, stderr)
    return result


def explain_ssh_failure(host: str, stderr: str) -> str:
    """Match the usual ssh errors to the step of the setup guide that fixes them.

    The original message is always kept at the end, for everything this
    does not recognise.
    """
    said = stderr.strip()
    if f"hostname {host}:" in said:
        hint = (
            f"ssh does not know the name {host}. "
            f"Write the SSH settings from {GUIDE} (step 5)."
        )
    elif any(text in said for text in UNREACHABLE):
        hint = (
            "Cannot reach the cluster. Is the VPN on? "
            "On the university network it works without."
        )
    # Before the next one: ssh then also says that the verification failed.
    elif "REMOTE HOST IDENTIFICATION HAS CHANGED" in said:
        hint = (
            f"{host} shows another key than the one ssh remembers. Usually SC "
            'has renewed it; read "REMOTE HOST IDENTIFICATION HAS CHANGED" in '
            "docs/reference/troubleshooting.md before you go on."
        )
    elif "Host key verification failed" in said:
        hint = (
            f"ssh does not know {host} yet. Log in once by hand with "
            f"`ssh {host}` and compare the fingerprint ({GUIDE}, step 6)."
        )
    elif "Permission denied" in said:
        hint = (
            "The cluster did not accept your key. Is it loaded in the SSH "
            f"agent (step 3) and uploaded to the portal (step 4)? See {GUIDE}."
        )
    elif any(text in said for text in BROKEN_OFF) and "kex_" not in said:
        # The key exchange comes first: there it is the connecting that failed.
        hint = f"The connection to {host} broke off before the command finished."
    else:
        hint = f"ssh could not connect to {host}."
    return f"{hint}\nssh said: {said}"
