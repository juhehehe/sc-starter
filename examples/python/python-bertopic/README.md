# BERTopic on a GPU: the topics of parliamentary questions

In this example you find the topics in 8,000 parliamentary questions with
BERTopic. BERTopic first turns each text into numbers that describe its
meaning, and then looks for groups of texts with similar meaning. You
test it on your computer and then run it on the cluster, partly on a
GPU.

The questions are the same as in
[Text embeddings on a GPU](../python-embeddings/README.md): written
questions of the UK House of Commons to eight ministries. There, the
computer sorted them into exactly eight groups. Here, BERTopic works out
how many topics there are, names each topic with its typical words, and
leaves out questions that fit no topic.

Only the first step of BERTopic, turning texts into numbers, benefits
from the GPU. The other steps run on the ordinary processor, the CPU. So
this project shows a job that needs both.

The finished files are next to this page: [pyproject.toml](pyproject.toml),
[run.py](run.py), [job.slurm](job.slurm) and [setup.slurm](setup.slurm).
If something does not work, you can compare your files with them.

**Time:** 60 min

## Before you start

You need a computer that is set up for the cluster, as described in the
[setup guide](../../../docs/basics/setup.md), and sc-starter, as
[Install sc-starter](../../../docs/sc-starter/install.md) describes. When you type
`sc-starter check` in a terminal, it should print `Ready.`

You also need a code editor. [VS Code](https://code.visualstudio.com/) is
free and works on all three systems. uv, which you installed for sc-starter, installs
Python and the packages.

The packages include PyTorch, the library that runs the language model.
On Linux, it comes with the libraries for NVIDIA GPUs and needs about
6 GB of disk space. On Windows and macOS it is much smaller. The project
works on Linux, on Windows and on Macs with Apple processors and macOS 14
or newer. It does not work on older Macs with Intel processors.

The [embeddings code-along](../python-embeddings/README.md) uses the same
questions and explains the basics, such as embeddings and the data. It
helps to do it first.

## Plan the project

BERTopic finds topics in three steps, with the settings that its
[best practices](https://maartengr.github.io/BERTopic/getting_started/best_practices/best_practices.html)
advise:

1. A language model turns each question into an *embedding*, 384 numbers
   that describe its meaning. This step runs on the GPU.
2. *UMAP* shrinks the 384 numbers to 5, and *HDBSCAN* looks for dense
   groups of questions among them. It decides how many groups there are,
   and leaves out questions that fit in none, the *outliers*. Each group
   is a topic. This step runs on the CPU.
3. For each topic, BERTopic picks the words that are common in it and
   rare elsewhere. This step runs on the CPU as well.

Steps 2 and 3 need all questions at once. On the cluster, the project is
therefore a single job. It books a GPU for step 1, and cores of the CPU
for steps 2 and 3.

On a CPU, the whole project takes about three minutes. On the cluster, the embeddings took two seconds on
the GPU, and the job took under a minute. With 8,000 questions, your
computer is enough. With half a million questions, step 1 would take
over an hour on a CPU and a few minutes on a GPU. Steps 2 and 3 would
then take long as well, because they stay on the CPU.

When the project is finished, the folder looks like this:

```text title="python-bertopic/"
python-bertopic/
├── data/questions.csv.gz   the questions
├── pyproject.toml          the project's packages
├── uv.lock                 their exact versions
├── .python-version         the version of Python
├── run.py                  finds and describes the topics
├── job.slurm               what the job on the GPU needs
├── setup.slurm             installs the packages and the model
└── results/                what the job writes
```

## Part 1: Build and test the project on your computer

### 1. Create the project

Open a terminal. Move to the folder where you keep your projects with
`cd`, for example `cd Documents`. Then create a folder for this project
and move into it:

```bash title="Your computer"
mkdir python-bertopic
cd python-bertopic
```

Open the folder in your editor. In VS Code, choose File › Open Folder and
select `python-bertopic`. All further commands on this page run in this
folder. If you open a new terminal later, move into the folder again with
`cd`.

Create the file `pyproject.toml` in your editor:

```toml title="pyproject.toml"
[project]
name = "python-bertopic"
version = "0.1.0"
description = "Topics in parliamentary questions with BERTopic, embeddings on a GPU"
requires-python = ">=3.12"
# The versions this example was tested with. PyTorch from PyPI brings
# CUDA 13, which needs GPU driver 580 or newer and does not run on V100
# cards. run.py uses UMAP, HDBSCAN and scikit-learn directly, so they are
# named too.
dependencies = [
    "bertopic==0.17.4",
    "hdbscan==0.8.44",
    "scikit-learn==1.9.1",
    "sentence-transformers==6.1.0",
    "torch==2.14.1",
    "umap-learn==0.5.12",
]

[tool.uv]
# The cluster, Windows and Apple silicon Macs. PyTorch has no current
# builds for Intel Macs, so they are left out.
environments = [
    "sys_platform == 'linux' and platform_machine == 'x86_64'",
    "sys_platform == 'win32' and platform_machine == 'AMD64'",
    "sys_platform == 'darwin' and platform_machine == 'arm64'",
]
```

The part under `[project]` names the packages the project needs, in
fixed versions, so that your results match the ones shown here:

- bertopic puts the three steps together.
- sentence-transformers and torch turn the questions into embeddings.
- umap-learn and hdbscan do step 2.
- scikit-learn picks the words of each topic in step 3.

The part under `[tool.uv]` tells uv to work out the versions for three
systems only: Linux, Windows and Macs with Apple processors.

Now choose Python 3.12 for the project and install the packages:

```bash title="Your computer"
uv python pin 3.12
uv sync
```

`uv python pin` writes the file `.python-version`. `uv sync` installs
Python 3.12 if needed, writes the exact version of every package into
`uv.lock`, and installs them into the folder `.venv`. PyTorch is large,
so this can take several minutes.

**Check:** Ask BERTopic for its version:

```bash title="Your computer"
uv run python -c "import bertopic; print(bertopic.__version__)"
```

```text title="Output"
0.17.4
```

### 2. Download the data

The data are the same 8,000 questions as in the embeddings code-along,
1,000 for each of eight ministries. That page describes the file.
Download it with curl. On Windows, type `curl.exe` instead of `curl`:

```bash title="Your computer"
curl -L --create-dirs -o data/questions.csv.gz https://raw.githubusercontent.com/juhehehe/sc-starter/main/examples/python/python-bertopic/data/questions.csv.gz
```

Contains Parliamentary information licensed under the
[Open Parliament Licence v3.0](https://www.parliament.uk/site-information/copyright-parliament/open-parliament-licence/).

**Check:** Count the questions:

```bash title="Your computer"
uv run python -c "import csv, gzip; print(len(list(csv.DictReader(gzip.open('data/questions.csv.gz', 'rt', encoding='utf-8')))), 'questions')"
```

```text title="Output"
8000 questions
```

### 3. Write the script

In your editor, create a new file in the project folder and save it as
`run.py`. You will add the code in six parts. Paste each part at the end
of the file.

The first part describes the script and imports the libraries:

```python title="run.py"
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
```

The second part holds the settings:

```python title="run.py"
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
```

`MODEL` is the same small language model as in the embeddings code-along.
`MIN_TOPIC_SIZE` is the smallest group of questions that counts as a
topic, as its comment explains. `SEED` is the *seed*, the number that
fixes the random numbers of UMAP, so that it gives the same result every
time on the same computer. `WORDS` is the number of words shown for each
topic.

`PARLIAMENT_WORDS` lists words to leave out of the topic words. Almost
every written question begins with phrases such as "what steps he is
taking" or "what assessment she has made of the potential impact". A
first run without this list named many topics with these words, such as
"defence, 2025, uk, reference, discussions, steps". With the list, the
same topic reads "defence, gaza, counterpart, armed, forces". The words
only describe the topics and do not change them. Every collection of
texts has such phrases of its own. Look at the words of your first run
and leave out what says nothing.

The third part reads the questions and checks the GPU, as in the
embeddings code-along. On the cluster, Slurm sets the variable
`SLURM_GPUS_ON_NODE` when a job has a GPU. If PyTorch then cannot use
it, the script stops instead of running slowly on the CPU:

```python title="run.py"
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
```

The fourth part describes each topic: its number, its size, its words,
and the ministry that most of its questions went to, with its share:

```python title="run.py"
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
```

The fifth part writes the report. Besides the table of topics, it gives
two shares. The first is the share of outliers. The second says how
often the questions of a topic went to its main ministry, which is near
100% if topics stay within ministries:

```python title="run.py"
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
```

The last part puts the three steps together:

```python title="run.py"
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
```

`main()` first checks the GPU and limits PyTorch to the cores the job
booked. Step 1 turns all questions into embeddings, on the GPU if there
is one, and measures how long that takes. `BERTopic(...)` then sets up
steps 2 and 3:

- `UMAP(...)` shrinks the embeddings to 5 numbers, with the fixed seed.
- `HDBSCAN(...)` finds the groups.
- `CountVectorizer(...)` picks the words, without common English words
  such as "the" and without `PARLIAMENT_WORDS`. It also takes pairs of
  words such as "asylum seekers".

`fit_transform()` runs steps 2 and 3 and gives each question its topic,
or −1 for an outlier. Last, the script writes three files into
`results`, as UTF-8, so that letters such as "đ" in a few questions work
on every system. `topics.txt` begins with the line about the embeddings,
which names the GPU or the CPU. At the end, the script prints how long it
took in all.

**Check:** Save the file and ask Python for one of its settings:

```bash title="Your computer"
uv run python -c "import run; print(run.MIN_TOPIC_SIZE)"
```

```text title="Output"
40
```

This loads the file without starting it, so it shows that the file is
saved and free of errors such as a missing bracket.

### 4. Test the project on your computer

Run the script on all questions:

```bash title="Your computer"
uv run run.py
```

The first time, it downloads the language model, about 90 MB. It may
warn that you send "unauthenticated requests to the HF Hub" and, on
Windows, that it cannot create symlinks. Both warnings are harmless. The
script then begins with lines such as:

```text title="Output"
Embedded 8,000 questions in 69.9 s on CPU.
Found the topics in 43.0 s on the CPU.
20 topics in 8,000 questions; 30% of the questions are in none (outliers).
Within a topic, 78% of the questions went to its main ministry.
```

Then followed the table of topics, and at the end a line such as
`Done in 116 seconds.` The largest topics are about defence, schools,
and water, food and farming.

**Check:** The folder `results` holds `topics.txt`, `topics.csv` and
`questions.csv`. Your number of topics may differ, as
[Reading the results](#reading-the-results) explains.

<details class="fix" markdown>
<summary>If it did not work</summary>

If you see `ModuleNotFoundError`, the packages are missing. Run `uv sync`
from step 1 again, in the project folder.

If you see `FileNotFoundError` with the name of the data file, either the
terminal is not in the project folder or the data are missing. Move into
the folder with `cd`, or repeat step 2.

</details>

### 5. Measure what the job needs

The last line of the test shows how long the script took. To see its
memory, run it again and open the task manager while it runs: Activity
Monitor on macOS, Task Manager on Windows, System Monitor on Linux. Find
the process python and note the highest value you see. The script takes
about two minutes and uses about 1.6 GB of memory.

On the GPU, step 1 takes seconds. Steps 2 and 3 take about as long as on
your computer.

**Check:** You know roughly how long the script took and how much memory
it used.

## Part 2: Prepare the project for the cluster

### 6. Write the job script

A *job script* tells Slurm what the job needs and what it should do.
Create a file called `job.slurm`:

```bash title="job.slurm"
#!/bin/bash
# Find the topics in all questions: embeddings on one GPU, then UMAP and
# HDBSCAN on the CPU cores. One job, so there is no runs.txt. Submit from
# your computer with `sc-starter submit`, after running
# `sc-starter submit setup.slurm` once.

#SBATCH --job-name=python-bertopic  # name in the queue and in the output file
#SBATCH --partition=gpu-a30         # machines with A30 GPUs; sinfo -s lists them all
#SBATCH --gpus=a30:1                # one GPU of type a30 (type:count)
#SBATCH --cpus-per-task=2           # UMAP and HDBSCAN run on the cores
#SBATCH --mem=4G                    # about twice what the script used on a computer
#SBATCH --time=00:10:00             # Slurm stops the job after 10 minutes
#SBATCH --output=%x-%j.out          # job name and job ID
#SBATCH --mail-type=END,FAIL        # email when the job has ended or failed

# uv, which setup.slurm installed for your account.
export PATH="$HOME/.local/bin:$PATH"

# Load the model from the cache that setup.slurm filled; never download
# during the job.
export HF_HUB_OFFLINE=1

# The project's Python and packages, which setup.slurm put into .venv.
# --no-sync uses them as they are and installs nothing.
uv run --no-sync python run.py
```

The lines that begin with `#SBATCH` are requests to Slurm. Two of them
book the GPU: `--partition=gpu-a30` sends the job to the nodes with
A30 GPUs, and `--gpus=a30:1` books one of them.

The others come from your measurement in step 5. UMAP with a fixed seed
uses one core, and HDBSCAN and the loading of the data use a second one.
4 GB of memory is about twice the 1.6 GB of the test. 10 minutes leave
plenty of room for a job that takes about a minute on the cluster.

Below the `#SBATCH` lines are the commands of the job. The line with
`PATH` tells bash where uv is, which the setup job installed.
`HF_HUB_OFFLINE=1` tells sentence-transformers to load the model from
the folder where the setup job saved it, and never to download during
the job. The last line runs the script once. As on your computer, it
starts the script with `uv run`. `--no-sync` makes uv take the packages
that the setup job installed as they are, and install nothing during the
job. [Your first job](../../../docs/slurm/first-job.md) explains every line of
a job script in more detail.

**Check:** The Explorer of VS Code shows the file `job.slurm`, not
`job.slurm.txt`.

### 7. Write the setup script

The setup job installs Python and the packages on the cluster and
downloads the model. It runs on a node without a GPU, because neither
needs one. Create a file called `setup.slurm`:

```bash title="setup.slurm"
#!/bin/bash
# Install this project's Python and packages on the cluster, once, and
# download the model. Submit from your computer with
# `sc-starter submit setup.slurm`, before the first `sc-starter submit`.
# It runs on a CPU node: installing needs no GPU, and the GPU job that
# follows then needs no internet.

#SBATCH --job-name=python-bertopic-setup    # name in the queue and in the output file
#SBATCH --partition=cpu-xeonv3              # standard CPU partition
#SBATCH --cpus-per-task=2                   # two cores for unpacking
#SBATCH --mem=4G                            # 4 GB of memory
#SBATCH --time=00:30:00                     # PyTorch is large; a few minutes the first time
#SBATCH --output=%x-%j.out                  # job name and job ID

# Stop at the first command that fails, so that the job ends as FAILED
# rather than COMPLETED. It comes after the #SBATCH lines, since Slurm
# reads those only up to the first command.
set -e

# uv installs Python and the packages. The first time, fetch uv itself
# into ~/.local/bin, the same place as on a Linux computer.
export PATH="$HOME/.local/bin:$PATH"
if ! command -v uv > /dev/null; then
  curl -LsSf https://astral.sh/uv/0.12.10/install.sh | env UV_NO_MODIFY_PATH=1 sh
fi

# Exactly the versions in uv.lock, into .venv in this folder. --locked
# stops if uv.lock does not match pyproject.toml.
uv sync --locked

# Load the model named in run.py once, which downloads it into the
# Hugging Face cache, ~/.cache/huggingface. The GPU job loads it from there.
.venv/bin/python -c 'from run import MODEL; from sentence_transformers import SentenceTransformer; SentenceTransformer(MODEL); print("Model ready:", MODEL)'
```

The first part installs uv for your account if it is not there yet, and
then installs exactly the package versions from `uv.lock`. The last line
loads the model once, which downloads it into a folder in your home
directory on the cluster. [Packages: uv and renv](../../../docs/project/packages.md)
explains the setup job in general.

**Check:** The Explorer shows the file `setup.slurm`.

## Part 3: Run the project on the cluster

### 8. Install the packages on the cluster

Check first that your computer still reaches the cluster:

```bash title="Your computer"
sc-starter check
```

It prints `Ready.` If not, it says what is missing, such as the VPN. Then
start the setup job:

```bash title="Your computer"
sc-starter submit setup.slurm
```

```text title="Output"
Submitted job 28412130. See how it goes with `sc-starter status`.
```

Before this line, sc-starter prints how many files it uploaded. It copied
your project to the cluster, into `sc-projects/python-bertopic` in your
home directory there. Run `sc-starter status` every minute or so. The
first time, the job takes a few minutes, because PyTorch with its GPU
libraries is large.

**Check:** `sc-starter status` shows the job as `COMPLETED`, and the
output of `sc-starter log` ends with:

```text title="Output"
Model ready: sentence-transformers/all-MiniLM-L6-v2
```

Above it, the log may show a warning about "unauthenticated requests to
the HF Hub". It is harmless.

### 9. Find the topics on the GPU

```bash title="Your computer"
sc-starter submit
```

```text title="Output"
Submitted job 28412203. See how it goes with `sc-starter status`.
```

Follow the job with `sc-starter status`. Many people want GPUs, so the
job may wait as `PENDING` for a while before it runs. That is normal.
When it has run, `sc-starter log` shows what it printed. It contains:

```text title="Output"
Embedded 8,000 questions in 2.1 s on NVIDIA A30.
Found the topics in 29.6 s on the CPU.
```

The embeddings took 2.1 seconds on the GPU, against about 70 seconds on
a CPU.

**Check:** `sc-starter status` shows the job as `COMPLETED`, and the log
names `NVIDIA A30`, not `CPU`.

<details class="fix" markdown>
<summary>If it did not work</summary>

If the log ends with `This job has a GPU, but PyTorch cannot use it`,
PyTorch on the cluster cannot reach the GPU.
[Troubleshooting](../../../docs/reference/troubleshooting.md#python-this-job-has-a-gpu-but-pytorch-cannot-use-it)
explains the causes.

If the log says `Cannot find the requested files in the disk cache and
outgoing traffic has been disabled`, the setup job has not downloaded the
model. Check its log with `sc-starter log --job` and the job ID of the
setup job, and submit `setup.slurm` again.

</details>

### 10. Bring the results back

```bash title="Your computer"
sc-starter pull
```

sc-starter copies the folder `results` from the cluster into your project
folder, together with the output files of both jobs.

**Check:** `results/topics.txt` begins with a line that names the GPU,
such as `Embedded 8,000 questions in 2.1 s on NVIDIA A30.`

## Reading the results

`results/topics.txt` from the cluster, from an earlier version of the
script that did not yet write the first line about the embeddings:

```text title="results/topics.txt"
22 topics in 8,000 questions; 30% of the questions are in none (outliers).
Within a topic, 78% of the questions went to its main ministry.

topic  size  main ministry         words
    0  1435  Defence 50%           defence, gaza, counterpart, armed, forces, armed forces
    1   921  Environment 88%       water, food, farmers, animal, waste, farming
    2   904  Education 91%         schools, children, school, education, support, pupils
    3   345  Home Office 86%       asylum, immigration, visa, seekers, asylum seekers, visas
    4   335  Transport 97%         rail, railways, railway, bus, train, great
    5   265  Home Office 90%       police, crime, policing, tackle, violence, abuse
    6   213  Health 98%            nhs, care, nhs england, england, health, people
    7   208  Treasury 96%          tax, business, rates, business rates, relief, pension
    8   191  Transport 91%         driving, safety, road, drivers, road safety, test
    9   101  Health 100%           cancer, cancers, treatments, screening, treatment, blood
   10    90  Transport 54%         electric, vehicle, vehicles, electric vehicle, electric vehicles, charging
   11    85  Foreign Office 58%    chagos, garcia, diego, diego garcia, concerning, agreement
   12    77  Health 96%            pharmacies, drugs, medicines, medication, community, pharmaceutical
   13    75  Education 19%         servants, civil servants, staff, civil, grade, performance
   14    56  Foreign Office 95%    development, development assistance, assistance, official development, official, oda
   15    53  Treasury 58%          debt, climate, global, international, fund, sovereign debt
   16    49  Treasury 86%          vat, businesses, hospitality businesses, independent, school, fees
   17    49  Treasury 96%          banking, loan charge, charge, loan, hubs, review
   18    47  Defence 100%          july spent, hms, maintenance, spent, july, rfa
   19    46  Health 91%            dental, nhs, nhs dental, adequacy nhs, dentistry, dentists
   20    44  Health 32%            hon member, member, hon, respond, respond correspondence, correspondence
   21    40  Transport 90%         heathrow, airport, airports, flights, heathrow airport, expansion
```

30% of the questions are outliers, and most topics stay within one
ministry. Some topics are very specific: dentists, cancer, pharmacies,
Heathrow, the Chagos Islands, driving tests and the loan charge. Topic 16
is about VAT, including the new VAT on private school fees. Others are
broad. Gaza sits in one large topic of defence and foreign affairs, half
of it from Defence and two fifths from the Foreign Office, as in the
embeddings code-along. Two topics cut across all ministries: the staff
of the ministries (13), and when a minister will answer an MP's letter
(20).

A run on a CPU found 20 topics instead of 22. Its
largest topics are about the same subjects, but their sizes differ, and
some of the smaller topics are others. The two computers calculate
slightly differently: the embeddings on a CPU and on a GPU differ in
their last decimal places, and UMAP takes shortcuts in its arithmetic
that can differ between processors. UMAP turns such small differences
into slightly different groups. The share of outliers and the share
within the main ministry stayed the same. Run on the same computer, the
script gives the same topics every time.

Unlike the embeddings code-along, nobody sets the number of groups here,
and each group gets words. The code-along
[Topic model in Python](../python-topic-model/README.md) uses another
kind of topic model, which counts words and gives each text a mix of
topics. BERTopic starts from the meaning and gives each question one
topic or none.

### What the job really used

`reportseff` shows how much of the booked time, cores and memory a job
used. Type it with the job ID of your GPU job:

```bash title="Your computer"
ssh sc-login reportseff 28412203
```

```text title="Output"
     JobID    State       Elapsed  TimeEff   CPUEff   MemEff
  28412203  COMPLETED    00:00:49   5.4%     24.5%     8.0%
```

A first job booked more: four cores, 16 GB and 15 minutes. It ran for 49
seconds, 5% of its time. It used about one of its four cores, because UMAP with a fixed seed uses only one, as the
[UMAP documentation on reproducibility](https://umap-learn.readthedocs.io/en/latest/reproducibility.html)
explains. It used under 1.5 GB of memory. That is why `job.slurm` on this
page books two cores, 4 GB and 10 minutes.

## Using the project with your own texts

Save your texts in the same form as `data/questions.csv.gz`, one row per
text, with the text in a column `question` and a category to compare
with in a column `ministry`. The column `id` may be empty. Then change `DATA` in `run.py`,
run the script on your computer, and adapt `PARLIAMENT_WORDS` to the
phrases that say nothing in your texts.

Change `MIN_TOPIC_SIZE` for finer or broader topics. For German texts, take a model for many languages, such as
`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, and German
stop words. Change `MODEL` in `run.py`, and run
`sc-starter submit setup.slurm` again before the next job, so that the
cluster downloads the new model.

[Bring your own project](../../../docs/sc-starter/bring-your-own-project.md) goes through
these points for a project of your own.

## Removing the project from the cluster

When you no longer need the project on the cluster, delete its folder
there:

```bash title="Your computer"
ssh sc-export rm -rI sc-projects/python-bertopic
```

`rm -rI` asks once before it deletes. Type `y` and press Enter. The packages and the model stay in the
stores of uv and Hugging Face in your home directory, so that later
projects can use them.
[Keep your account tidy](../../../docs/reference/keep-your-account-tidy.md) explains how to
see and remove them.

## Sources

- Data: written questions of the UK House of Commons, 2025, from the
  [Written Questions API](https://questions-statements-api.parliament.uk).
  Contains Parliamentary information licensed under the Open Parliament
  Licence v3.0.
- BERTopic (MIT): Grootendorst, M. (2022). BERTopic: Neural topic
  modeling with a class-based TF-IDF procedure.
  <https://doi.org/10.48550/arXiv.2203.05794>
- UMAP (BSD): McInnes, L., Healy, J., & Melville, J. (2018). UMAP:
  Uniform manifold approximation and projection for dimension reduction.
  <https://doi.org/10.48550/arXiv.1802.03426>
- HDBSCAN (BSD): McInnes, L., Healy, J., & Astels, S. (2017). hdbscan:
  Hierarchical density based clustering. *Journal of Open Source
  Software*, 2(11), 205. <https://doi.org/10.21105/joss.00205>
- Model: [all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)
  (Apache 2.0).
