"""Tests for the ssh calls and their error messages."""

import pytest

from sc_starter import Problem, ssh


def test_run_returns_output_and_never_prompts(fake_ssh):
    fake_ssh.reply("sc-login", stdout="login01\n")

    assert ssh.run("sc-login", "hostname -s") == "login01\n"
    [call] = fake_ssh.calls
    assert call["host"] == "sc-login"
    assert call["command"] == "hostname -s"
    assert "BatchMode=yes" in call["options"]


def test_ssh_on_windows_gets_no_connect_timeout(fake_ssh, monkeypatch):
    """Before OpenSSH 8.6, Windows' ssh would wait that long on every call."""
    monkeypatch.setattr(ssh.sys, "platform", "win32")

    ssh.run("sc-login", "true")

    [call] = fake_ssh.calls
    assert not [option for option in call["options"] if "ConnectTimeout" in option]


def test_an_exit_code_the_caller_knows_becomes_its_message(fake_ssh):
    fake_ssh.reply("sc-export", code=4)

    with pytest.raises(Problem) as raised:
        ssh.run("sc-export", "true", problems={4: "Run `sc-starter push` first."})

    assert str(raised.value) == "Run `sc-starter push` first."
    assert not isinstance(raised.value, ssh.CommandFailed)


def test_any_other_exit_code_stays_a_failed_command(fake_ssh):
    fake_ssh.reply("sc-export", stderr="tar: broken\n", code=2)

    with pytest.raises(ssh.CommandFailed) as raised:
        ssh.run("sc-export", "true", problems={4: "Run `sc-starter push` first."})

    assert raised.value.code == 2
    assert "tar: broken" in str(raised.value)


@pytest.mark.parametrize(
    ("stderr", "hint"),
    [
        (
            "ssh: Could not resolve hostname sc-login: Name or service not known",
            "step 5",
        ),
        (
            "ssh: connect to host login01.sc.uni-leipzig.de port 22: "
            "Connection timed out",
            "VPN",
        ),
        (
            "ssh: Could not resolve hostname login01.sc.uni-leipzig.de: "
            "Temporary failure in name resolution",
            "VPN",
        ),
        ("Host key verification failed.", "step 6"),
        (
            "@    WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!     @\n"
            "Host key verification failed.",
            "troubleshooting.md",
        ),
        ("Connection to login01.sc.uni-leipzig.de closed by remote host.", "broke off"),
        ("client_loop: send disconnect: Broken pipe", "broke off"),
        ("kex_exchange_identification: read: Connection reset by peer", "could not"),
        (
            "ssh: connect to host login01.sc.uni-leipzig.de port 22: "
            "Connection refused",
            "could not connect",
        ),
        ("user@login01.sc.uni-leipzig.de: Permission denied (publickey).", "agent"),
    ],
)
def test_ssh_failures_point_to_the_fix(fake_ssh, stderr, hint):
    fake_ssh.reply("sc-login", stderr=stderr, code=255)

    with pytest.raises(Problem) as error:
        ssh.run("sc-login", "true")

    assert hint in str(error.value)
    assert stderr in str(error.value)


def test_ssh_failures_drop_the_carriage_returns_of_ssh(fake_ssh):
    fake_ssh.reply(
        "sc-login",
        stderr="@    WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!     @\r\n"
        "Host key verification failed.\r\n",
        code=255,
    )

    with pytest.raises(Problem) as error:
        ssh.run("sc-login", "true")

    assert "\r" not in str(error.value)


def test_failing_remote_command_keeps_exit_code_and_message(fake_ssh):
    fake_ssh.reply("sc-login", stderr="ls: cannot access 'x'", code=2)

    with pytest.raises(ssh.CommandFailed, match="exit code 2") as error:
        ssh.run("sc-login", "ls x")

    assert error.value.code == 2
    assert "cannot access 'x'" in str(error.value)


def test_missing_ssh_says_how_to_get_it(monkeypatch):
    monkeypatch.setattr(ssh, "SSH", ["sc-starter-test-no-such-ssh"])

    with pytest.raises(Problem, match="OpenSSH Client"):
        ssh.run("sc-login", "true")
