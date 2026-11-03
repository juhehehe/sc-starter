"""On your computer, after `sc-starter pull`: put all runs side by side.

Usage: uv run combine.py
Reads results/k-*.csv, names missing runs, prints the table and draws
results/choose-k.png: coherence against exclusivity, one point per K.
"""

import csv
import sys
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt

RESULTS = Path("results")
NUMBERS = ["k", "coherence", "exclusivity", "minutes"]


def read_results():
    """Return one dict per finished run, ordered by K."""
    rows = []
    for path in RESULTS.glob("k-*.csv"):
        with open(path, newline="") as file:
            rows.extend(csv.DictReader(file))
    for row in rows:
        for name in NUMBERS:
            row[name] = float(row[name])
    return sorted(rows, key=lambda row: row["k"])


def planned_k():
    """Return the K of each line of runs.txt, such as 10 for `python run.py 10`."""
    lines = Path("runs.txt").read_text().splitlines()
    return [int(line.split()[-1]) for line in lines if line.strip()]


def draw(rows, path):
    """Draw both measures against K, side by side, each with its own scale."""
    k = [row["k"] for row in rows]
    panels = [
        ("coherence", "UMass coherence\nhigher: the words of a topic appear together"),
        ("exclusivity", "Exclusivity\nhigher: the words belong to one topic only"),
    ]
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.4), layout="constrained")
    for ax, (measure, title) in zip(axes, panels, strict=True):
        ax.plot(k, [row[measure] for row in rows], color="#2a78d6", marker="o")
        ax.set_title(title, loc="left", fontsize=10)
        ax.set_xticks(k)
        ax.set_xlabel("Number of topics (K)")
        ax.spines[["top", "right"]].set_visible(False)
    fig.suptitle("Political blogs 2008: more topics, less coherent, more exclusive")
    fig.savefig(path, dpi=100)
    plt.close(fig)


def main():
    """Put the results of all runs side by side, as a table and a figure."""
    rows = read_results()
    if not rows:
        sys.exit("No results yet. Run `sc-starter pull` first.")

    # Nothing on the cluster is deleted, so results/ may still hold runs
    # that an earlier runs.txt asked for.
    planned = planned_k()
    old = [int(row["k"]) for row in rows if int(row["k"]) not in planned]
    if old:
        print(
            "Left out results of runs not in runs.txt: "
            f"K = {', '.join(map(str, old))}.",
            file=sys.stderr,
        )
        rows = [row for row in rows if int(row["k"]) in planned]
    if not rows:
        sys.exit(
            "No results for the runs in runs.txt yet. Run `sc-starter pull` first."
        )

    # A run that fails in a later job leaves its earlier result in place.
    jobs = Counter(row["job"] for row in rows)
    print(
        "Runs per job: "
        + ", ".join(f"{count} from job {job}" for job, count in sorted(jobs.items()))
    )

    missing = sorted(set(planned) - {int(row["k"]) for row in rows})
    if missing:
        print(
            f"No results for K = {', '.join(map(str, missing))}. "
            "`sc-starter status` shows why.",
            file=sys.stderr,
        )

    # One line per run: K, the two measures and the minutes it took.
    print(f"{'k':>3} {'coherence':>10} {'exclusivity':>12} {'minutes':>8}")
    for row in rows:
        print(
            f"{row['k']:3.0f} {row['coherence']:10.4f} "
            f"{row['exclusivity']:12.4f} {row['minutes']:8.2f}"
        )

    draw(rows, RESULTS / "choose-k.png")
    print(f"Wrote {RESULTS / 'choose-k.png'}")


if __name__ == "__main__":
    main()
