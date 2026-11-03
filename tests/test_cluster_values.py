"""The cluster at a glance must list every cluster value the repository uses.

Partitions, GPU types, modules, hosts and fingerprints appear in many job
scripts and pages. When the cluster changes them, this test names each
place that still uses a value that page does not list, so that the page
and the scripts stay in step. The page is
docs/reference/cluster-at-a-glance.md.
"""

import re
from pathlib import Path

from sc_starter.layout import NOTES_DIR

REPO = Path(__file__).resolve().parents[1]
CLUSTER_PAGE = REPO / "docs" / "reference" / "cluster-at-a-glance.md"
# Folders with files the repository does not write itself. In NOTES_DIR
# are private copies of job scripts, which keep values the cluster retired.
SKIP = {".git", ".venv", ".pytest_cache", ".ruff_cache", "results", "renv", NOTES_DIR}

PATTERNS = {
    "partition": re.compile(r"--partition=([\w-]+)"),
    "GPU type": re.compile(r"--gpus=([a-z0-9]+)"),
    # Up to a space, or to the backtick that ends inline code in a page.
    "module": re.compile(r"module load ([^\s`]+)"),
    "host": re.compile(r"\b([\w-]+\.sc\.uni-leipzig\.de)\b"),
    "fingerprint": re.compile(r"(SHA256:[A-Za-z0-9+/]{43})"),
}


def repository_files():
    """Every job script and page of the repository except The cluster at a glance."""
    for path in sorted(REPO.rglob("*")):
        if path.suffix not in {".slurm", ".md"} or path == CLUSTER_PAGE:
            continue
        if SKIP.intersection(path.relative_to(REPO).parts):
            continue
        yield path


def values_in_use():
    """(kind, value, file) for each cluster value the repository names."""
    found = []
    for path in repository_files():
        text = path.read_text(encoding="utf-8")
        for kind, pattern in PATTERNS.items():
            for value in pattern.findall(text):
                found.append((kind, value, path.relative_to(REPO).as_posix()))
    return found


def test_the_scan_finds_the_values_of_the_examples():
    kinds = {kind for kind, _, _ in values_in_use()}

    assert kinds == set(PATTERNS)


def test_cluster_page_lists_every_value_in_use():
    listed = CLUSTER_PAGE.read_text(encoding="utf-8")

    missing = sorted(
        f"{file}: {kind} {value}"
        for kind, value, file in values_in_use()
        if f"`{value}`" not in listed
    )

    page = CLUSTER_PAGE.relative_to(REPO)
    assert not missing, f"Not in {page}:\n" + "\n".join(missing)
