"""One run of the topic model: fit LDA with K topics on the political blogs.

Usage: python run.py <K>
Writes results/k-<K>.csv with two quality measures and
results/k-<K>-topics.txt with the most probable words of each topic.
"""

import csv
import gzip
import os
import sys
import time
from pathlib import Path

import numpy as np
import tomotopy as tp

DATA = Path("data/poliblog5k.csv.gz")
RESULTS = Path("results")
# Rounds of Gibbs sampling; enough for 5,000 posts to settle.
ITERATIONS = 1000
# Both quality measures look at the top words of each topic.
TOP_WORDS = 10


def read_posts(path):
    """Return the words of each post, one list per post."""
    with gzip.open(path, "rt", encoding="utf-8", newline="") as file:
        return [row["words"].split() for row in csv.DictReader(file)]


def exclusivity(model):
    """Measure how much the top words of a topic belong to that topic only.

    The measure of exclusivity() in the R package stm, so that this example
    and r-topic-model report the same thing. Within each topic, every word
    gets two ranks: how frequent it is in the topic, and how exclusive (the
    share of the word's weight across all topics that lies in this topic).
    FREX combines both, with 70% weight on exclusivity. The score of a
    topic is the sum over its top words, at most 10; this returns the mean
    over topics.
    """
    weights = np.array([model.get_topic_word_dist(t) for t in range(model.k)])
    shares = weights / weights.sum(axis=0)
    frex = 1 / (0.7 / ranks(shares) + 0.3 / ranks(weights))
    top = np.argsort(-weights, axis=1)[:, :TOP_WORDS]
    return float(np.take_along_axis(frex, top, axis=1).sum(axis=1).mean())


def ranks(values):
    """Return the rank of each value within its row, from 1/n for the lowest to 1."""
    return (values.argsort(axis=1).argsort(axis=1) + 1) / values.shape[1]


def main():
    """Fit the model with the K given on the command line, and save it."""
    if len(sys.argv) != 2 or not sys.argv[1].isdigit():
        sys.exit("Usage: python run.py <number of topics>")
    k = int(sys.argv[1])

    # The model with K topics and a fixed seed, so that the same K gives
    # the same topics, and the posts it learns from.
    model = tp.LDAModel(k=k, seed=1)
    for words in read_posts(DATA):
        model.add_doc(words)

    # Left alone, tomotopy starts one worker per core of the whole node, and
    # they crowd onto the cores this job booked. So as many workers as
    # job.slurm books; one on your own computer.
    cores = int(os.environ.get("SLURM_CPUS_PER_TASK", "1"))
    started = time.perf_counter()
    model.train(iterations=ITERATIONS, workers=cores)
    minutes = (time.perf_counter() - started) / 60

    # UMass coherence: do the top words of a topic appear in the same posts?
    coherence = tp.coherence.Coherence(model, coherence="u_mass", top_n=TOP_WORDS)

    # The two measures and the time, as one row of results/k-<K>.csv.
    RESULTS.mkdir(exist_ok=True)
    with open(RESULTS / f"k-{k:02d}.csv", "w", newline="") as file:
        writer = csv.writer(file)
        # The job, so that combine.py can tell results of an earlier job apart.
        writer.writerow(["k", "coherence", "exclusivity", "minutes", "job"])
        writer.writerow(
            [
                k,
                round(coherence.get_score(), 4),
                round(exclusivity(model), 4),
                round(minutes, 2),
                os.environ.get("SLURM_ARRAY_JOB_ID", ""),
            ]
        )

    # The seven most probable words of each topic, to read what it is about.
    topics = [
        f"Topic {t + 1:2d}: "
        + ", ".join(word for word, _ in model.get_topic_words(t, top_n=7))
        for t in range(k)
    ]
    (RESULTS / f"k-{k:02d}-topics.txt").write_text("\n".join(topics) + "\n")
    print(f"K = {k} done in {minutes:.1f} minutes")


if __name__ == "__main__":
    main()
