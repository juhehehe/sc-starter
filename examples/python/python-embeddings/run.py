"""Turn parliamentary questions into embeddings, find similar ones, group them.

Usage: python run.py
Reads data/questions.csv.gz and writes to results/:
  similar.txt  the questions closest to a few searches in our own words
  groups.csv   each question with its ministry and the group it landed in
  compare.txt  how well the groups match the ministries
"""

import csv
import gzip
import os
import sys
import time
from collections import Counter
from pathlib import Path

import torch
from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score

DATA = Path("data/questions.csv.gz")
RESULTS = Path("results")
# A small, fast model for English sentences; setup.slurm downloads it.
MODEL = "sentence-transformers/all-MiniLM-L6-v2"
# The closest questions to these need not share a single word with them.
SEARCHES = [
    "long waits for hip and knee operations",
    "small boats crossing the Channel",
    "potholes on local roads",
    "farmers hit by floods",
    "crumbling concrete in school buildings",
]
CLOSEST = 5


def read_questions(path):
    """Return one dict per question, with its ministry and its text."""
    with gzip.open(path, "rt", encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def check_gpu():
    """Stop if Slurm gave this job a GPU that PyTorch cannot use.

    Otherwise the model would quietly run on the CPU, slowly, while the
    booked GPU sits idle.
    """
    if os.environ.get("SLURM_GPUS_ON_NODE") and not torch.cuda.is_available():
        sys.exit("This job has a GPU, but PyTorch cannot use it. See README.md.")


def device_name(model):
    """Return the name of the GPU, such as "NVIDIA A30", or "CPU"."""
    if model.device.type == "cuda":
        return torch.cuda.get_device_name(model.device)
    return "CPU"


def closest(model, embeddings, questions):
    """Return the CLOSEST questions to each search, with their similarity."""
    lines = []
    searches = model.encode(SEARCHES, normalize_embeddings=True)
    for search, similarity in zip(SEARCHES, searches @ embeddings.T, strict=True):
        lines.append(f'Search: "{search}"')
        for i in similarity.argsort()[::-1][:CLOSEST]:
            question = questions[i]
            lines.append(
                f"  {similarity[i]:.2f}  {question['ministry']}: {question['question']}"
            )
        lines.append("")
    return lines


def order_groups(groups, ministries, names):
    """Renumber the groups 1, 2, ... in the order of their largest ministry.

    k-means numbers its groups at random. In this order, a group that
    matches a ministry sits in that ministry's row of the table, and a good
    match reads as a diagonal.
    """
    largest = {}
    for group in set(groups):
        members = [m for g, m in zip(groups, ministries, strict=True) if g == group]
        largest[group] = Counter(members).most_common(1)[0][0]
    order = sorted(largest, key=lambda group: (names.index(largest[group]), group))
    number = {group: n for n, group in enumerate(order, start=1)}
    return [number[group] for group in groups]


def compare(groups, questions, names):
    """Return two scores, the table of ministries against groups, and subjects."""
    ministries = [question["ministry"] for question in questions]
    count = Counter(zip(ministries, groups, strict=True))
    numbers = sorted(set(groups))

    lines = [
        f"Adjusted Rand index:          {adjusted_rand_score(ministries, groups):.2f}"
        "   (0: no better than chance, 1: groups = ministries)",
        "Normalized mutual information: "
        f"{normalized_mutual_info_score(ministries, groups):.2f}"
        "   (0: unrelated, 1: groups = ministries)",
        "",
        "Questions of each ministry (rows) in each group (columns):",
        "",
        f"{'':<15}" + "".join(f"{n:>6}" for n in numbers),
    ]
    for name in names:
        lines.append(f"{name:<15}" + "".join(f"{count[name, n]:>6}" for n in numbers))

    # What each group is about: the subjects of its Hansard headings, the
    # part before the colon, such as "Asylum" in "Asylum: Hotels".
    lines += ["", "Most common subjects in each group:", ""]
    for n in numbers:
        subjects = Counter(
            question["heading"].split(":")[0]
            for question, group in zip(questions, groups, strict=True)
            if group == n
        )
        top = ", ".join(subject for subject, _ in subjects.most_common(4))
        lines.append(f"{n:>2}: {top}")
    return lines


def main():
    """Embed the questions, search and group them, and write the results."""
    begun = time.perf_counter()
    check_gpu()
    # PyTorch would start a thread for every core of the node; as many as
    # job.slurm booked, so they do not crowd onto the booked cores.
    if "SLURM_CPUS_PER_TASK" in os.environ:
        torch.set_num_threads(int(os.environ["SLURM_CPUS_PER_TASK"]))

    # The questions, the ministry of each, and the eight ministries in order.
    questions = read_questions(DATA)
    ministries = [question["ministry"] for question in questions]
    names = sorted(set(ministries))
    # The GPU if there is one, else the CPU: the same on every computer, also
    # on Macs, whose own GPU sentence-transformers would otherwise pick.
    model = SentenceTransformer(
        MODEL, device="cuda" if torch.cuda.is_available() else "cpu"
    )

    # Normalized to length 1, so that the dot product of two embeddings is
    # their cosine similarity, from -1 to 1.
    started = time.perf_counter()
    embeddings = model.encode(
        [question["question"] for question in questions], normalize_embeddings=True
    )
    seconds = time.perf_counter() - started
    summary = (
        f"Embedded {len(questions):,} questions in {seconds:.1f} seconds "
        f"on {device_name(model)}, with {MODEL}."
    )
    print(summary)

    RESULTS.mkdir(exist_ok=True)
    # UTF-8 everywhere: a few questions hold letters that Windows' own
    # encoding cannot write.
    (RESULTS / "similar.txt").write_text(
        "\n".join(closest(model, embeddings, questions)), encoding="utf-8"
    )

    # As many groups as ministries; the seed makes k-means repeatable.
    groups = KMeans(n_clusters=len(names), n_init=10, random_state=1).fit_predict(
        embeddings
    )
    groups = order_groups(list(groups), ministries, names)

    # Each question with its ministry and its group, for a spreadsheet.
    with open(RESULTS / "groups.csv", "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["id", "date", "ministry", "group", "heading", "question"])
        for question, group in zip(questions, groups, strict=True):
            writer.writerow(
                [question[c] for c in ("id", "date", "ministry")]
                + [group]
                + [question[c] for c in ("heading", "question")]
            )

    # The scores and the table, into compare.txt and onto the screen.
    report = "\n".join(compare(groups, questions, names))
    (RESULTS / "compare.txt").write_text(f"{summary}\n\n{report}\n", encoding="utf-8")
    print(report)
    print(f"\nDone in {time.perf_counter() - begun:.0f} seconds.")


if __name__ == "__main__":
    main()
