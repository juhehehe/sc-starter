# Runs longer than the time limit: a simulation that saves and continues

In this example you build a simulation in Python that saves its
progress along the way and continues from its last save in the next job.
Every job has a time limit. When the time is up, Slurm stops the job, and
whatever the program had not saved is lost.

The simulation shows how opinions among three million people merge into
camps. It takes seven to ten minutes, but its job script gives each job
only two, on purpose. Slurm stops the first job, and you submit it again.
The next job continues where the last save left off. After a few jobs,
the simulation is done, with exactly the same result as in one go.

```mermaid
flowchart LR
    accTitle: One simulation in several jobs
    accDescr: Job 1 saves its progress along the way and stops at its time limit. Job 2 continues from the last save, and so on, until the last job finishes the simulation.
    job1["Job 1"] -- "last save" --> job2["Job 2"]
    job2 -- "last save" --> last["Last job"]
```

You write the code on your computer and test there that saving and
continuing work. Then you let the cluster run the simulation in pieces.

The finished files are next to this page: [run.py](run.py) and
[job.slurm](job.slurm). If something does not work, you can compare your
files with them.

**Time:** 45 min

## Before you start

You need a computer that is set up for the cluster, as described in the
[setup guide](../../../docs/basics/setup.md), and sc-starter, as
[Install sc-starter](../../../docs/sc-starter/install.md) describes. When you type
`sc-starter check` in a terminal, it should print `Ready.`

You also need a code editor. [VS Code](https://code.visualstudio.com/) is
free and works on all three systems. The project uses only what comes with Python,
so it needs no packages. uv, which you installed for sc-starter, provides
Python on your computer.

## Plan the project

The model is the bounded confidence model of Deffuant et al. (2000). Each
of three million people holds an opinion between 0 and 1, at first spread
at random. Again and again, two people chosen at random meet. If their
opinions differ by less than a tolerance, here 0.11, both move halfway
towards each other. Otherwise neither changes. One round is three million
such meetings, and the simulation runs 100 rounds.

Each meeting starts from the opinions that the meetings before it left
behind. The rounds therefore have to run one after another. Unlike the
topic models in the other code-alongs, this work cannot be split into
runs that take place side by side. It is one long computation.

This simulation takes minutes, so your own computer could run it in one
go. Real simulations of this kind can run for days, and that is when you
need the cluster. A job there may run for at most two days, so a
computation like this one has to work in pieces. So the program has to save its progress
every few rounds and, when it starts, continue from the last save. Four
questions decide how:

- What to save: everything the program needs to go on exactly where it
  was. Here, that is all opinions, the number of the round, and the state
  of the random number generator. With the generator's state, the
  meetings after a restart are exactly the same as without one.
- How often to save: a stop loses the rounds after the last save, and
  each save costs a little time. Here the program saves every 5 rounds,
  about every 20 seconds.
- How to save: so that a stop in the middle of saving leaves the last
  complete save intact.
- How to keep two jobs from working on the same save at once: with a
  line in the job script that lets a second job wait for the first.

The program writes its save into a file called `checkpoint.pickle`, its
*checkpoint*. When all rounds are done, it writes the result into
`results/camps.txt`.

When the project is finished, the folder looks like this:

```text title="python-long-run/"
python-long-run/
├── run.py              the simulation, which saves and continues
├── job.slurm           what each job needs
├── checkpoint.pickle   the last save, written by the jobs
└── results/camps.txt   the camps at the end
```

The project has no `runs.txt`, because it is a single run. It has no
`setup.slurm` either, because it needs no packages: the cluster provides
Python as a module.

## Part 1: Build and test the project on your computer

### 1. Create the project

Open a terminal. Move to the folder where you keep your projects with
`cd`, for example `cd Documents`. Then create a folder for this project
and move into it:

```bash title="Your computer"
mkdir python-long-run
cd python-long-run
```

Open the folder in your editor. In VS Code, choose File › Open Folder and
select `python-long-run`.

**Check:** uv finds Python 3.12. The first time, it downloads it, which
takes a few seconds:

```bash title="Your computer"
uv run --python 3.12 python --version
```

```text title="Output"
Python 3.12.14
```

The last number may differ.

### 2. Write the simulation

In your editor, create a new file in the project folder and save it as
`run.py`. You will add the code in eight parts. Paste each part at the
end of the file.

The first part describes the program and imports what it needs from the
standard library of Python:

```python title="run.py"
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
```

The second part holds the settings of the simulation and of saving:

```python title="run.py"
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
```

The third part starts a new simulation. `start()` draws the opinions with
a generator of random numbers that has a fixed *seed*, so that the
simulation starts the same way every time. The *state* is everything the
simulation needs to go on: the round, the opinions and the state of the
generator. `settings()` lists the settings that a save must match:

```python title="run.py"
def start():
    """Start a new population: random opinions, round 0, a seeded generator."""
    rng = random.Random(SEED)
    opinions = [rng.random() for _ in range(PEOPLE)]
    return {"round": 0, "opinions": opinions, "rng": rng.getstate()}


def settings():
    """Return the settings that a save must match to continue from it."""
    return {"people": PEOPLE, "tolerance": TOLERANCE, "step": STEP, "seed": SEED}
```

The fourth part loads the last save, or starts a new simulation if there
is none:

```python title="run.py"
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
```

`pickle` is Python's own way of writing objects to a file and reading
them back. If you change a setting, such as the tolerance, an old save no
longer fits, and the program stops instead of mixing two simulations.

The fifth part saves the state:

```python title="run.py"
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
```

The program writes the save into a temporary file first and then renames
it. If Slurm stops the job while it writes, only the temporary file is
broken, and the last complete save is still there.

The sixth part is one round of the simulation:

```python title="run.py"
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
```

The seventh part finds the camps of opinion and writes the report. A
group of similar opinions counts as a camp if it holds more than 1% of
the people. The *fingerprint* is a short code computed from all three
million opinions. Two simulations have the same fingerprint only if every
single opinion is the same, so it shows whether the pieces add up to the
same result as one run in one go:

```python title="run.py"
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
```

The last part puts everything together. It loads the last save, runs the
rounds that are still missing, saves every 5 rounds, and writes the
report at the end:

```python title="run.py"
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
```

`flush=True` makes Python write each line at once. Otherwise it would
collect the lines first, and a job stopped by Slurm might leave an empty
output file.

**Check:** Save the file and ask Python for one of its settings:

```bash title="Your computer"
uv run --python 3.12 python -c "import run; print(run.PEOPLE)"
```

```text title="Output"
3000000
```

This loads the file without starting the simulation, so it shows that
the file is saved and free of errors such as a missing bracket. The real test follows in
step 3.

### 3. Test saving and continuing on your computer

The important part of this program is that it continues after a stop.
Test exactly that. Start the simulation:

```bash title="Your computer"
uv run --python 3.12 run.py
```

`uv run --python 3.12` starts the script with Python 3.12. After about
20 seconds, the program prints its first line about a save, and then one
every 5 rounds:

```text title="Output"
No checkpoint: starting from round 0.
Round 5 of 100 saved after 0.3 minutes, 1 camps.
Round 10 of 100 saved after 0.7 minutes, 1 camps.
```

After the line for round 10, stop the program with Ctrl+C, also on
macOS, as Slurm would at the time limit. Python then prints a few lines
that end with `KeyboardInterrupt`. That is expected. Then start the
program again with the same command.

**Check:** The program continues where it saved last:

```text title="Output"
Continuing from round 10 of 100.
```

Let it run for a while, for the next step.

<details class="fix" markdown>
<summary>If it did not work</summary>

If the second start says `No checkpoint: starting from round 0.`, the
first start was stopped before its first save. Let it run until a line
says `saved`.

If it says `checkpoint.pickle was made with other settings`, you changed a
setting after the first start. Delete `checkpoint.pickle` and start
again.

</details>

### 4. Measure what a job needs

The running program shows how fast the simulation is. Read the minutes
in the line for round 15, after the first 5 rounds of this start, and
multiply them by 20 for all 100 rounds. 5 rounds take about 20 seconds,
so all 100 take about seven minutes.

While it runs, open the task manager of your computer: Activity Monitor
on macOS, Task Manager on Windows, System Monitor on Linux. Find the
process python and note its memory. It is about 250 MB.

Then stop the program with Ctrl+C and delete the file `checkpoint.pickle`
in the project folder. In VS Code, right-click it in the Explorer and
choose Delete. In a terminal, type `rm checkpoint.pickle` on Linux and
macOS, or `Remove-Item checkpoint.pickle` on Windows. If you left it,
sc-starter would send it to the cluster with the first job. The job
would change it there, and sc-starter would then refuse the second job,
so as not to overwrite the newer save on the cluster with your old one.

**Check:** You know roughly how long 100 rounds take and how much memory
the program uses, and `checkpoint.pickle` is no longer in the folder.

## Part 2: Prepare the project for the cluster

### 5. Write the job script

A *job script* tells Slurm what the job needs and what it should do.
Create a file called `job.slurm`:

```bash title="job.slurm"
#!/bin/bash
# One long simulation in pieces. One job, so there is no runs.txt. Submit
# from your computer with `sc-starter submit`; when the job stops at its time
# limit, submit it again, until `sc-starter status` shows COMPLETED.
# Only the standard library of Python, so there is no setup.slurm.

#SBATCH --job-name=python-long-run  # name in the queue and in the output files
#SBATCH --partition=cpu-xeonv3      # standard CPU partition; sinfo -s lists them all
#SBATCH --cpus-per-task=1           # the simulation uses one core
#SBATCH --mem=1G                    # 1 GB of memory
#SBATCH --time=00:02:00             # on purpose shorter than the simulation needs
#SBATCH --output=%x-%j.out          # job name and job ID, one file per job
#SBATCH --dependency=singleton      # wait while another job of this name runs: one save, one job

# Python from the cluster's module system.
module load Python/3.12.3-GCCcore-13.3.0

python run.py
```

The lines that begin with `#SBATCH` are requests to Slurm:

- One core, because the simulation uses one, and 1 GB of memory, four
  times the 250 MB it used on your computer.
- 2 minutes. The simulation needs about seven, so this time limit is too
  short on purpose. For a real computation, book the time you measured
  plus a margin. The saves are then a safety net, for a job that runs
  longer than expected.
- The output file is named after the job and its job ID. Each job writes
  a file of its own, so the logs of all pieces are kept.
- `--dependency=singleton` lets a job wait while another job of the same
  name is still running. Two jobs would otherwise continue from the same
  save and overwrite each other's progress.

Below the `#SBATCH` lines, `module load` switches on Python 3.12. The
last line starts the simulation,
once per job.
[Your first job](../../../docs/slurm/first-job.md) explains every line of a
job script in more detail.

**Check:** The Explorer of your editor shows the file `job.slurm`, not
`job.slurm.txt`.

## Part 3: Run the project on the cluster

### 6. Start the first job

Before you start, check that your computer still reaches the cluster:

```bash title="Your computer"
sc-starter check
```

It prints `Ready.` If not, it says what is missing, such as the VPN.

Then start the first job:

```bash title="Your computer"
sc-starter submit
```

```text title="Output"
Submitted job 28411276. See how it goes with `sc-starter status`.
```

Before this line, sc-starter prints how many files it uploaded. It copied
your project to the cluster, into `sc-projects/python-long-run` in your
home directory there, and handed `job.slurm` to Slurm. Your job ID will be
different.

Wait about two minutes, then look at the job and at what it printed:

```bash title="Your computer"
sc-starter status
sc-starter log
```

`status` shows the job as `TIMEOUT`: Slurm stopped it at its time limit.
`log` shows how far it got:

```text title="Output"
No checkpoint: starting from round 0.
Round 5 of 100 saved after 0.3 minutes, 1 camps.
Round 10 of 100 saved after 0.7 minutes, 1 camps.
Round 15 of 100 saved after 1.0 minutes, 1 camps.
Round 20 of 100 saved after 1.4 minutes, 1 camps.
Round 25 of 100 saved after 1.7 minutes, 1 camps.
Round 30 of 100 saved after 2.1 minutes, 1 camps.
[2026-10-20T15:21:44.003] error: *** JOB 28411276 ON t002 CANCELLED AT 2026-10-20T15:21:44 DUE TO TIME LIMIT ***
```

The last line comes from Slurm. The job ran a little past its two
minutes, and its last save was round 30.

**Check:** `sc-starter status` shows the job as `TIMEOUT`, and the last
line before Slurm's message ends with `saved after` and a number of
minutes.

### 7. Continue in further jobs

Submit the same job again:

```bash title="Your computer"
sc-starter submit
```

```text title="Output"
Submitted job 28411346. See how it goes with `sc-starter status`.
```

Nothing has changed on your computer, so sc-starter uploads nothing and
prints only this line. The save stays on the cluster, and the new job
continues from it. After two minutes, `sc-starter log` shows:

```text title="Output"
Continuing from round 30 of 100.
Round 35 of 100 saved after 0.3 minutes, 1 camps.
Round 40 of 100 saved after 0.7 minutes, 1 camps.
Round 45 of 100 saved after 1.0 minutes, 3 camps.
Round 50 of 100 saved after 1.4 minutes, 3 camps.
Round 55 of 100 saved after 1.7 minutes, 3 camps.
Round 60 of 100 saved after 2.1 minutes, 4 camps.
[2026-10-20T15:24:13.003] error: *** JOB 28411346 ON t002 CANCELLED AT 2026-10-20T15:24:13 DUE TO TIME LIMIT ***
```

Repeat `sc-starter submit` until `sc-starter status` shows `COMPLETED`.
In one try, it took four jobs: the third went from round 60 to 95, and
the fourth finished the last five rounds. Because of
`--dependency=singleton`, you may also submit the next job while one is
still running. It then waits as `PENDING` and starts when the first has
ended.

<details class="fix" markdown>
<summary>If it did not work</summary>

If `sc-starter submit` stops with `The cluster has a newer copy` and
names `checkpoint.pickle`, the file was still on your computer when you
submitted the first job. Delete it on your computer, not on the cluster,
and submit again.
[Troubleshooting](../../../docs/reference/troubleshooting.md#the-cluster-has-a-newer-copy)
explains the message.

If a job ends as `FAILED` and its log says `made with other settings`,
the save on the cluster comes from a simulation with other settings.
Remove it as described at the end of this page, and submit again.

If a job still shows `PENDING` after two minutes, the cluster is busy.
It starts on its own. Look again a few minutes later.

</details>

**Check:** `sc-starter status` shows the last job as `COMPLETED`, and
`sc-starter log` ends with the report:

```text title="Output"
Continuing from round 95 of 100.
Round 100 of 100 saved after 0.3 minutes, 4 camps.
3,000,000 people, tolerance 0.11, after 100 rounds.

4 camps:

  opinion   share of people
    0.142    25.1%
    0.387    25.2%
    0.617    24.9%
    0.859    24.8%

In no camp: 0.1%
Fingerprint of all opinions: 732bc6e8898304a7
```

### 8. Bring the results back

```bash title="Your computer"
sc-starter pull
```

sc-starter copies the folder `results` from the cluster into your project
folder, together with the output files, one per job, such as
`python-long-run-28411276.out`.

**Check:** `results/camps.txt` holds the report from the last log.

## Reading the results

With a tolerance of 0.11, the opinions end in four camps of about a
quarter each, as in the simulations of Lorenz (2010). With a tolerance of
0.22 there would be two camps, and above about 0.27 everyone agrees. The
logs show the camps form along the way: one spread of opinions up to
round 40, three camps from round 45, four from round 60.

The same simulation in one go, on an ordinary computer, took 9.4 minutes
and ended with the same fingerprint, `732bc6e8898304a7`. So in four pieces,
all three million opinions came out exactly as without a stop.

The jobs also show the price of saving only every 5 rounds. The rounds a
job computed after its last save were lost, and the next job did them
again.

## Planning a long computation of your own

- Check first whether your work really has to be one long computation.
  If it falls into pieces that do not depend on each other, such as many
  models, many seeds or many files, run them as many short runs side by
  side, as in [Topic model in Python](../python-topic-model/README.md).
- Time a short piece first, such as a few rounds or one epoch, and
  estimate the whole. Book that with a margin, at most two days in the
  normal partitions. Longer partitions exist for groups that SC lets in,
  as [The cluster at a glance](../../../docs/reference/cluster-at-a-glance.md#limits) describes.
- In a job of hours, a save every 10 to 30 minutes is plenty.
- At the time limit, Slurm sends the program the signal `TERM`, waits 30
  seconds on this cluster, and then ends it. A program can catch `TERM`
  and save at once. The option `--signal` of `sbatch` sends a warning
  earlier, as the
  [sbatch documentation](https://slurm.schedmd.com/sbatch.html#OPT_signal)
  explains.
- Libraries for machine learning can save for you. The `Trainer` of
  Hugging Face transformers saves checkpoints and continues from them with
  `trainer.train(resume_from_checkpoint=True)`, as its
  [guide to checkpointing](https://huggingface.co/docs/transformers/trainer_recipes#checkpointing)
  describes.

To try another tolerance, change `TOLERANCE` in `run.py`, for example to
0.22. A save made with the old tolerance is refused, so remove it on the
cluster before you submit:

```bash title="Your computer"
ssh sc-export rm sc-projects/python-long-run/checkpoint.pickle
```

## Removing the project from the cluster

When you no longer need the project on the cluster, delete its folder
there, with the last save and the results:

```bash title="Your computer"
ssh sc-export rm -rI sc-projects/python-long-run
```

`rm -rI` asks once before it deletes. Type `y` and press Enter.

## Sources

- Deffuant, G., Neau, D., Amblard, F., & Weisbuch, G. (2000). Mixing
  beliefs among interacting agents. *Advances in Complex Systems*, 3,
  87–98. <https://doi.org/10.1142/S0219525900000078>
- Lorenz, J. (2010). Heterogeneous bounds of confidence: Meet, discuss
  and find consensus! *Complexity*, 15(4), 43–52.
  <https://doi.org/10.1002/cplx.20295>
