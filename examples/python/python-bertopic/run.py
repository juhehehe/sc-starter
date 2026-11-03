"""Find the topics in parliamentary questions with BERTopic.

Usage: python run.py
Reads data/questions.csv.gz and writes to results/:
  topics.txt     each topic with its size, words and the ministry most of
                 its questions went to, and the share of outliers
  topics.csv     the same, to open in a spreadsheet
  questions.csv  each question with its ministry and its topic
"""

import csv
import gzip
import os
import sys
import time
from collections import Counter
from pathlib import Path

import torch
from bertopic import BERTopic
from hdbscan import HDBSCAN
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, CountVectorizer
from umap import UMAP

DATA = Path("data/questions.csv.gz")
RESULTS = Path("results")
# The same small, fast model for English sentences as in python-embeddings;
# setup.slurm downloads it.
MODEL = "sentence-transformers/all-MiniLM-L6-v2"
# The smallest group of questions that counts as a topic: larger gives
# fewer, broader topics, smaller gives more, narrower ones.
MIN_TOPIC_SIZE = 40
SEED = 1
WORDS = 6
# Words from the phrases that begin almost every written question, such as
# "what steps he is taking", "what assessment she has made of the potential
# impact" or "with reference to". They say nothing about the topic, so they
# are left out of its words, together with the usual English stop words.
PARLIAMENT_WORDS = [
    "2024",
    "2025",
    "answer",
    "assessment",
    "department",
    "discussions",
    "ensure",
    "impact",
    "made",
    "merits",
    "plans",
    "potential",
    "pursuant",
    "question",
    "recent",
    "reference",
    "steps",
    "taking",
    "uk",
]


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


def describe(topic_model, topics, ministries):
    """One row per topic: number, size, words, main ministry and its share.

    Topic -1 holds the outliers, the questions HDBSCAN put in no group; it
    is left out here and counted separately.
    """
    rows = []
    for topic in sorted(set(topics) - {-1}):
        members = [m for t, m in zip(topics, ministries, strict=True) if t == topic]
        ministry, count = Counter(members).most_common(1)[0]
        words = [word for word, _ in topic_model.get_topic(topic)[:WORDS]]
        rows.append(
            {
                "topic": topic,
                "size": len(members),
                "ministry": ministry,
                "share": count / len(members),
                "words": ", ".join(words),
            }
        )
    return rows


def report(rows, topics):
    """Return the text for results/topics.txt."""
    outliers = topics.count(-1) / len(topics)
    in_topics = sum(row["size"] for row in rows)
    # Of the questions in a topic, the share that went to the ministry
    # most common in that topic: near 1 if topics stay within ministries.
    purity = sum(row["share"] * row["size"] for row in rows) / in_topics
    lines = [
        f"{len(rows)} topics in {len(topics):,} questions; "
        f"{outliers:.0%} of the questions are in none (outliers).",
        f"Within a topic, {purity:.0%} of the questions went to its main ministry.",
        "",
        "topic  size  main ministry         words",
    ]
    for row in rows:
        ministry = f"{row['ministry']} {row['share']:.0%}"
        lines.append(
            f"{row['topic']:>5}  {row['size']:>4}  {ministry:<20}  {row['words']}"
        )
    return "\n".join(lines) + "\n"


def main():
    """Embed the questions, find the topics, and write the results."""
    begun = time.perf_counter()
    check_gpu()
    # PyTorch would start a thread for every core of the node; as many as
    # job.slurm booked, so they do not crowd onto the booked cores.
    if "SLURM_CPUS_PER_TASK" in os.environ:
        torch.set_num_threads(int(os.environ["SLURM_CPUS_PER_TASK"]))

    # The questions, their texts, and the ministry of each.
    questions = read_questions(DATA)
    texts = [question["question"] for question in questions]
    ministries = [question["ministry"] for question in questions]

    # Step 1, on the GPU: each question becomes a list of numbers that
    # describes its meaning. Computed once, before BERTopic, as its best
    # practices advise.
    # The GPU if there is one, else the CPU: the same on every computer, also
    # on Macs, whose own GPU sentence-transformers would otherwise pick.
    encoder = SentenceTransformer(
        MODEL, device="cuda" if torch.cuda.is_available() else "cpu"
    )
    started = time.perf_counter()
    embeddings = encoder.encode(texts)
    seconds = time.perf_counter() - started
    device = device_name(encoder)
    summary = f"Embedded {len(texts):,} questions in {seconds:.1f} s on {device}."
    print(summary)

    # Steps 2 and 3, on the CPU, with the settings from the BERTopic best
    # practices: UMAP shrinks the 384 numbers to 5, HDBSCAN finds dense
    # groups in them, and CountVectorizer picks the words that describe each
    # group, without stop words such as "the" or PARLIAMENT_WORDS, and with
    # pairs of words. The words do not change the groups.
    # The fixed random_state makes UMAP give the same result in every run.
    topic_model = BERTopic(
        embedding_model=encoder,
        umap_model=UMAP(
            n_neighbors=15,
            n_components=5,
            min_dist=0.0,
            metric="cosine",
            random_state=SEED,
        ),
        hdbscan_model=HDBSCAN(
            min_cluster_size=MIN_TOPIC_SIZE,
            metric="euclidean",
            cluster_selection_method="eom",
            prediction_data=True,
        ),
        vectorizer_model=CountVectorizer(
            stop_words=sorted(ENGLISH_STOP_WORDS) + PARLIAMENT_WORDS,
            min_df=2,
            ngram_range=(1, 2),
        ),
    )
    started = time.perf_counter()
    topics, _ = topic_model.fit_transform(texts, embeddings)
    topics = [int(topic) for topic in topics]
    print(f"Found the topics in {time.perf_counter() - started:.1f} s on the CPU.")

    # The topics, and each question with its topic, for a spreadsheet.
    rows = describe(topic_model, topics, ministries)
    RESULTS.mkdir(exist_ok=True)
    # UTF-8 everywhere: a few questions hold letters that Windows' own
    # encoding cannot write.
    with open(RESULTS / "topics.csv", "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    words = {row["topic"]: row["words"] for row in rows}
    with open(RESULTS / "questions.csv", "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["id", "ministry", "topic", "topic_words", "question"])
        for question, topic in zip(questions, topics, strict=True):
            writer.writerow(
                [
                    question["id"],
                    question["ministry"],
                    topic,
                    words.get(topic, "(outlier)"),
                    question["question"],
                ]
            )
    # The report, into topics.txt and onto the screen.
    text = report(rows, topics)
    (RESULTS / "topics.txt").write_text(f"{summary}\n\n{text}", encoding="utf-8")
    print(text)
    print(f"Done in {time.perf_counter() - begun:.0f} seconds.")


if __name__ == "__main__":
    main()
