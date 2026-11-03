"""Tests for checking runs.txt and reading run numbers."""

import pytest

from sc_starter import Problem, runs


def write_runs(folder, text):
    (folder / "runs.txt").write_bytes(text.encode())


def test_counts_runs_with_any_line_endings(tmp_path):
    write_runs(tmp_path, "python fit.py 1\r\npython fit.py 2\r\n")

    assert runs.count_runs(tmp_path) == 2


def test_no_runs_file_means_no_array(tmp_path):
    assert runs.count_runs(tmp_path) is None


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("", "runs.txt is empty"),
        ("python fit.py 1\n\npython fit.py 2\n", "line 2 is empty"),
        ("# grid over k\npython fit.py 1\n", "line 1 is a comment"),
        ("\ufeff# grid over k\npython fit.py 1\n", "line 1 is a comment"),
        ("python fit.py \\\n  --k 1\n", "line 1 ends with"),
    ],
)
def test_refuses_runs_that_would_not_match_line_numbers(tmp_path, text, message):
    write_runs(tmp_path, text)

    with pytest.raises(Problem, match=message):
        runs.count_runs(tmp_path)


@pytest.mark.parametrize("hidden", ["\r", "\v", "\f", "\x85", " "])
def test_refuses_line_breaks_that_sed_does_not_see(tmp_path, hidden):
    """splitlines() would count two runs here; sed in the job script sees one."""
    write_runs(tmp_path, f"python fit.py 1{hidden}python fit.py 2\n")

    with pytest.raises(Problem, match="line 1 has a hidden line break"):
        runs.count_runs(tmp_path)


def test_counts_a_last_line_without_line_ending(tmp_path):
    write_runs(tmp_path, "python fit.py 1\npython fit.py 2")

    assert runs.count_runs(tmp_path) == 2


def test_counts_runs_after_the_mark_windows_puts_before_utf8(tmp_path):
    write_runs(tmp_path, "\ufeffpython fit.py 1\r\npython fit.py 2\r\n")

    assert runs.count_runs(tmp_path) == 2


def test_refuses_runs_not_saved_as_utf8(tmp_path):
    """PowerShell 5.1 writes UTF-16 with `>`."""
    (tmp_path / "runs.txt").write_bytes("python fit.py 1\r\n".encode("utf-16"))

    with pytest.raises(Problem, match="not saved as UTF-8"):
        runs.count_runs(tmp_path)


def test_reads_run_numbers_sorted_and_once(tmp_path):
    path = tmp_path / "failed.txt"
    path.write_text("7\n3\n7\n")

    assert runs.read_run_numbers(path, count=10) == [3, 7]


def test_reads_run_numbers_after_the_mark_windows_puts_before_utf8(tmp_path):
    """`Set-Content -Encoding utf8` in PowerShell 5.1 writes the mark."""
    path = tmp_path / "failed.txt"
    path.write_bytes("﻿3\r\n7\r\n".encode())

    assert runs.read_run_numbers(path, count=10) == [3, 7]


def test_refuses_run_numbers_not_saved_as_utf8(tmp_path):
    """PowerShell 5.1 writes UTF-16 with `>`."""
    path = tmp_path / "failed.txt"
    path.write_bytes("3\r\n7\r\n".encode("utf-16"))

    with pytest.raises(Problem, match="failed.txt is not saved as UTF-8"):
        runs.read_run_numbers(path, count=10)


@pytest.mark.parametrize("text", ["0\n", "11\n", "three\n", ""])
def test_refuses_run_numbers_outside_runs(tmp_path, text):
    path = tmp_path / "failed.txt"
    path.write_text(text)

    with pytest.raises(Problem):
        runs.read_run_numbers(path, count=10)
