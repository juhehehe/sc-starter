"""Simulate how opinions in a large population merge into camps, in pieces.

Usage: python run.py
A run that takes longer than the time limit of its job. It saves its state
every few rounds to checkpoint.pickle; when Slurm stops the job, submit it
again and it continues from the last save. When all rounds are done, it
writes results/camps.txt: the camps of opinion at the end, their size, and
a fingerprint of all opinions to compare runs.

The model is the bounded confidence model of Deffuant et al. (2000): each
person holds an opinion between 0 and 1; two people chosen at random meet,
and if their opinions differ by less than TOLERANCE, both move halfway
towards each other. Only the standard library, so nothing to install.
"""

import hashlib
import os
import pickle
import random
import sys
import time
from array import array
from pathlib import Path

PEOPLE = 3_000_000
# In one round, as many meetings as there are people.
ROUNDS = 100
TOLERANCE = 0.11
# How far each moves towards the other: 0.5 is halfway, so they agree.
STEP = 0.5
SEED = 1
# Save every few rounds, about every 15 to 20 seconds on the cluster:
# often enough that a stop loses little, rarely enough that saving
# takes little time.
SAVE_EVERY = 5
CHECKPOINT = Path("checkpoint.pickle")
RESULTS = Path("results")


def start():
    """Start a new population: random opinions, round 0, a seeded generator."""
    rng = random.Random(SEED)
    opinions = [rng.random() for _ in range(PEOPLE)]
    return {"round": 0, "opinions": opinions, "rng": rng.getstate()}


def settings():
    """Return the settings that a save must match to continue from it."""
    return {"people": PEOPLE, "tolerance": TOLERANCE, "step": STEP, "seed": SEED}


def load():
    """Load the saved state, or start a new one if there is none.

    Stops if the save was made with other settings: continuing from it
    would mix two different simulations. pickle runs code stored in the
    file, so continue only from saves your own jobs wrote.
    """
    if not CHECKPOINT.exists():
        print("No checkpoint: starting from round 0.")
        return start()
    with open(CHECKPOINT, "rb") as file:
        state = pickle.load(file)
    if state["settings"] != settings():
        sys.exit(f"{CHECKPOINT} was made with other settings; remove it to start over.")
    if state["round"] > ROUNDS:
        sys.exit(
            f"{CHECKPOINT} is at round {state['round']}, past ROUNDS = {ROUNDS}; "
            "remove it to start over."
        )
    print(f"Continuing from round {state['round']} of {ROUNDS}.")
    return state


def save(state):
    """Write the state to CHECKPOINT so that a stop never leaves it broken.

    Written to a temporary file first and then renamed: renaming replaces
    the old file in one step, so if Slurm stops the job while writing, the
    last complete save is still there.
    """
    temporary = CHECKPOINT.with_suffix(".tmp")
    with open(temporary, "wb") as file:
        pickle.dump({**state, "settings": settings()}, file)
    os.replace(temporary, CHECKPOINT)


def one_round(opinions, rng):
    """PEOPLE meetings of two people chosen at random.

    Each meeting changes the opinions the next one starts from; that is why
    the rounds must run one after another and cannot be split into a Slurm
    array.
    """
    for _ in range(PEOPLE):
        i = rng.randrange(PEOPLE)
        j = rng.randrange(PEOPLE)
        a, b = opinions[i], opinions[j]
        if abs(a - b) < TOLERANCE:
            move = (b - a) * STEP
            opinions[i] = a + move
            opinions[j] = b - move


def camps(opinions):
    """Find the camps of opinion: (opinion, share of people), and the rest.

    Opinions are sorted and split wherever the gap to the next is larger
    than 0.01; as in Deffuant et al. (2000), a group counts as a camp if it
    holds more than 1% of the people.
    """
    ordered = sorted(opinions)
    groups = [[ordered[0]]]
    for opinion in ordered[1:]:
        if opinion - groups[-1][-1] > 0.01:
            groups.append([opinion])
        else:
            groups[-1].append(opinion)
    large = [group for group in groups if len(group) > 0.01 * PEOPLE]
    found = [(sum(group) / len(group), len(group) / PEOPLE) for group in large]
    return found, 1 - sum(share for _, share in found)


def fingerprint(opinions):
    """Return a short code that is the same only if all opinions are the same."""
    return hashlib.sha256(array("d", opinions).tobytes()).hexdigest()[:16]


def report(opinions):
    """Return the text for results/camps.txt."""
    found, scattered = camps(opinions)
    lines = [
        f"{PEOPLE:,} people, tolerance {TOLERANCE}, after {ROUNDS} rounds.",
        "",
        f"{len(found)} camps:",
        "",
        "  opinion   share of people",
    ]
    lines += [f"  {opinion:7.3f}   {share:6.1%}" for opinion, share in found]
    lines += [
        "",
        f"In no camp: {scattered:.1%}",
        f"Fingerprint of all opinions: {fingerprint(opinions)}",
    ]
    return "\n".join(lines) + "\n"


def main():
    """Run the rounds that are still missing, save along the way, report."""
    # Go on from the last save, with the random numbers where they were.
    state = load()
    rng = random.Random()
    rng.setstate(state["rng"])
    opinions = state["opinions"]

    started = time.perf_counter()
    for number in range(state["round"] + 1, ROUNDS + 1):
        one_round(opinions, rng)
        if number % SAVE_EVERY == 0 or number == ROUNDS:
            # The generator's state goes into the save too, so that the
            # meetings after a restart are the same as without one.
            save({"round": number, "opinions": opinions, "rng": rng.getstate()})
            minutes = (time.perf_counter() - started) / 60
            print(
                f"Round {number} of {ROUNDS} saved after {minutes:.1f} minutes, "
                f"{len(camps(opinions)[0])} camps.",
                flush=True,
            )

    # All rounds are done: the camps, into camps.txt and onto the screen.
    RESULTS.mkdir(exist_ok=True)
    text = report(opinions)
    (RESULTS / "camps.txt").write_text(text)
    print(text)


if __name__ == "__main__":
    main()
