"""Tests for the command line itself, before any subcommand runs."""

import sys

import pytest

from sc_starter import cli


def test_version_prints_name_and_version(capsys):
    with pytest.raises(SystemExit) as exit_info:
        cli.main(["--version"])

    assert exit_info.value.code == 0
    assert capsys.readouterr().out.startswith("sc-starter ")


def test_no_arguments_shows_help(capsys):
    assert cli.main([]) == 0
    assert "usage: sc-starter" in capsys.readouterr().out


def test_check_reports_both_hosts(fake_ssh, capsys):
    fake_ssh.reply("sc-login", stdout="login01\n")
    fake_ssh.reply("sc-export", stdout="export01\n")

    assert cli.main(["check"]) == 0
    out = capsys.readouterr().out
    assert "sc-login: ok (login01)" in out
    assert "sc-export: ok (export01)" in out
    assert [call["host"] for call in fake_ssh.calls] == ["sc-login", "sc-export"]


def test_check_stops_with_a_message_when_the_cluster_is_unreachable(fake_ssh, capsys):
    fake_ssh.reply(
        "sc-login",
        stderr="ssh: connect to host login01 port 22: Connection timed out",
        code=255,
    )

    assert cli.main(["check"]) == 1
    assert "Is the VPN on?" in capsys.readouterr().err
    assert len(fake_ssh.calls) == 1


@pytest.mark.skipif(sys.platform == "win32", reason="Ctrl+C is a signal on Unix")
def test_ctrl_c_stops_without_a_traceback(fake_ssh, capsys):
    fake_ssh.reply("sc-login", interrupt=True)

    assert cli.main(["check"]) == 130
    assert capsys.readouterr().err == "sc-starter: Stopped.\n"
