# Text embeddings on a GPU: grouping parliamentary questions by meaning

In this example you build a project in Python that uses a language model,
test it on your computer and then run it on a GPU of the cluster.

Members of the UK House of Commons put written questions to the
government, and each question goes to the ministry in charge. The project
turns 8,000 such questions into *embeddings*: lists of numbers that place
questions with similar meaning close together. With them, you find the
questions closest to a search in your own words, and you sort all
questions into eight groups without telling the computer which ministry
was asked. Then you check whether the groups come out as the ministries.

Language models run much faster on a GPU than on the ordinary processor
of a computer, the CPU.

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

The packages include PyTorch, the library that runs the model. On Linux,
it comes with the libraries for NVIDIA GPUs and needs about 6 GB of disk
space. On Windows and macOS it is much smaller. The project works on
Linux, on Windows and on Macs with Apple processors and macOS 14 or
newer. It does not work on older Macs with Intel processors, for which
PyTorch no longer offers current versions.

## Plan the project

The project has two tasks. It searches the questions for a few phrases of
your own, and it groups all 8,000 questions by their meaning. For the
groups, it uses *k-means*, a method that puts close embeddings into the
same group. Both tasks need the embeddings of all questions at once. On
the cluster, the project is therefore a single job with a single run,
and needs no `runs.txt`.

The embeddings come from a language model. On a CPU, the embeddings of
8,000 questions take a little over a minute. On a GPU of the cluster,
they take about four seconds. For 8,000
questions, your computer is therefore enough. A million questions would
take hours on a CPU and minutes on the GPU. This project uses the GPU so
that you learn how to book one.

The cluster needs the packages and the model before the job runs. A
setup job installs the packages and downloads the model on a node without a
GPU. The job on the GPU then loads both and needs
no internet.

When the project is finished, the folder looks like this:

```text title="python-embeddings/"
python-embeddings/
├── data/questions.csv.gz   the questions
├── pyproject.toml          the project's packages
├── uv.lock                 their exact versions
├── .python-version         the version of Python
├── run.py                  embeds, searches and groups the questions
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
mkdir python-embeddings
cd python-embeddings
```

Open the folder in your editor. In VS Code, choose File › Open Folder and
select `python-embeddings`. All further commands on this page run in this
folder. If you open a new terminal later, move into the folder again with
`cd`.

The project describes its packages in a file called `pyproject.toml`. In
the other Python code-along, `uv add` writes this file. Here you write it
yourself, because it needs a setting that `uv add` does not write. Create
the file `pyproject.toml` in your editor:

```toml title="pyproject.toml"
[project]
name = "python-embeddings"
version = "0.1.0"
description = "Embeddings of parliamentary questions on a GPU: find similar ones, group them"
requires-python = ">=3.12"
# The versions this example was tested with. PyTorch from PyPI brings
# CUDA 13, which needs GPU driver 580 or newer and does not run on V100
# cards.
dependencies = [
    "scikit-learn==1.9.1",
    "sentence-transformers==6.1.0",
    "torch==2.14.1",
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

The part under `[project]` names the project, the versions of Python it
works with and the three packages it needs. sentence-transformers turns
texts into embeddings. torch is PyTorch, which does the calculations.
scikit-learn provides k-means and the scores. Each package has a fixed
version, such as `torch==2.14.1`, so that your results match the ones
shown here.

The part under `[tool.uv]` tells uv to work out the versions for three
systems only: Linux, Windows and Macs with Apple processors. Intel Macs
are left out, because PyTorch offers no current version for them.

Now choose Python 3.12 for the project and install the packages:

```bash title="Your computer"
uv python pin 3.12
uv sync
```

`uv python pin` writes the file `.python-version`. `uv sync` installs
Python 3.12 if needed, works out the exact version of every package,
writes them into `uv.lock`, and installs them into the folder `.venv`.
PyTorch is large, so this can take several minutes.

**Check:** Ask the three main packages for their versions:

```bash title="Your computer"
uv run python -c "import torch, sentence_transformers, sklearn; print(torch.__version__, sentence_transformers.__version__, sklearn.__version__)"
```

```text title="Output"
2.14.1+cu130 6.1.0 1.9.1
```

The ending `+cu130` means that this PyTorch can use *CUDA* 13, NVIDIA's
software for calculating on its GPUs. On Windows and macOS, the version
of torch ends differently or not at all, because PyTorch there runs on
the CPU.

### 2. Download the data

The data are written questions to eight ministries in the House of
Commons, asked in 2025 and answered, 1,000 per ministry drawn at random:

| Short name | Ministry |
|---|---|
| Defence | Ministry of Defence |
| Education | Department for Education |
| Environment | Department for Environment, Food and Rural Affairs |
| Foreign Office | Foreign, Commonwealth and Development Office |
| Health | Department of Health and Social Care |
| Home Office | Home Office |
| Transport | Department for Transport |
| Treasury | HM Treasury |

Download the file into a new folder called `data` with curl. On Windows, type `curl.exe` instead of
`curl`, because in PowerShell the word `curl` starts a different command:

```bash title="Your computer"
curl -L --create-dirs -o data/questions.csv.gz https://raw.githubusercontent.com/juhehehe/sc-starter/main/examples/python/python-embeddings/data/questions.csv.gz
```

The file is a compressed table of 0.5 MB, with one row per question. Its
columns are:

- `id` and `uin`, the numbers of the question in Parliament's records
- `date`, the day it was asked
- `ministry`, the ministry that answered it
- `heading`, the subject that Parliament gave it, such as `Asylum: Hotels`
- `question`, the text of the question

Every question begins with "To ask the Secretary of State for Defence",
which gives the ministry away. The file leaves this beginning out, so a
question reads "what steps he is taking to ...". It also leaves out the
names of the MPs.

The script [prepare_data.py](prepare_data.py) made the file from the
[Written Questions API](https://questions-statements-api.parliament.uk)
of Parliament. For each ministry, it asks the API for up to 150 answered
questions from each month of 2025, so that the questions spread over the
whole year. It cuts off the beginning "To ask …", leaves out the few
questions that begin differently and the ones that were asked twice, and
draws 1,000 of the rest at random, with a fixed seed. It needs nothing
but Python itself and took 19 minutes, because the API answers slowly.
You do not need to run it. To make the file again, type
`uv run prepare_data.py` in the folder of the code-along.

Contains Parliamentary information licensed under the
[Open Parliament Licence v3.0](https://www.parliament.uk/site-information/copyright-parliament/open-parliament-licence/).

**Check:** Count the questions and show the first one:

```bash title="Your computer"
uv run python -c "import csv, gzip; rows = list(csv.DictReader(gzip.open('data/questions.csv.gz', 'rt', encoding='utf-8'))); print(len(rows), 'questions'); print(rows[0]['ministry'], '|', rows[0]['heading'], '|', rows[0]['question'][:60])"
```

```text title="Output"
8000 questions
Health | Coronavirus: Vaccination | if he will make an assessment of the potential impact of not
```

### 3. Write the script

In your editor, create a new file in the project folder and save it as
`run.py`. You will add the code in eight parts. Paste each part at the
end of the file.

The first part describes the script and imports the libraries:

```python title="run.py"
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
```

The second part holds the settings: where the data are, where the results
go, which model to use, and the searches:

```python title="run.py"
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
```

The model all-MiniLM-L6-v2 is small and fast and works for English
sentences. It turns each question into 384 numbers. The first time you use
it, sentence-transformers downloads it from Hugging Face, a website that
hosts language models, and keeps it in a folder on your computer.

The third part reads the questions:

```python title="run.py"
def read_questions(path):
    """Return one dict per question, with its ministry and its text."""
    with gzip.open(path, "rt", encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))
```

The fourth part makes sure that the GPU is used when there is one:

```python title="run.py"
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

When a job has a GPU, Slurm sets the variable `SLURM_GPUS_ON_NODE`. If PyTorch then
cannot reach the GPU through CUDA, `check_gpu()` stops the script, as its
comment explains. On your computer, the variable does not exist, and the
script runs on the CPU.

The fifth part finds the questions closest to each search:

```python title="run.py"
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
```

The script turns each search into an embedding as well. The *cosine
similarity* of two embeddings, from −1 to 1, says how close their
meanings are. `searches @ embeddings.T` computes it for every search and
every question at once. `argsort()[::-1]` sorts the questions from the
closest to the furthest.

The sixth part numbers the groups, so that the table at the end is easy
to read:

```python title="run.py"
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
```

The seventh part compares the groups with the ministries:

```python title="run.py"
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
```

Two scores sum up how well the groups match the ministries. Both run from
0, where the groups have nothing to do with the ministries, to 1, where
the groups are the ministries. Then follows a table of how many questions
of each ministry landed in each group, and the most common subjects of
each group.

The last part puts everything together:

```python title="run.py"
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
```

`main()` first checks the GPU and limits PyTorch to the cores the job
booked. It then loads the questions and the model, on the GPU if there is one and
otherwise on the CPU. It turns all questions into embeddings and measures
how long that takes. k-means then sorts the embeddings into as many groups
as there are ministries. `random_state=1` is its *seed*, the number that
fixes its random start, so the groups come out the same every time.

Last, the script writes three files into `results`, as UTF-8, so that
letters such as "đ" in a few questions work on every system. It prints
how many seconds it took in all.

**Check:** Save the file and ask Python for one of its settings:

```bash title="Your computer"
uv run python -c "import run; print(run.MODEL)"
```

```text title="Output"
sentence-transformers/all-MiniLM-L6-v2
```

This loads the file without starting it, so it shows that the file is
saved and free of errors such as a missing bracket. The real test follows in step 4.

### 4. Test the project on your computer

Run the script:

```bash title="Your computer"
uv run run.py
```

The first time, it downloads the model, about 90 MB. It may warn that you
send "unauthenticated requests to the HF Hub" and, on Windows, that it
cannot create symlinks. Both warnings are harmless. Then it embeds the
questions on the CPU of your computer, which takes a minute or two. It
prints a line such as:

```text title="Output"
Embedded 8,000 questions in 64.8 seconds on CPU, with sentence-transformers/all-MiniLM-L6-v2.
```

Then follow the scores and the table, which
[Reading the results](#reading-the-results) explains, and at the end:

```text title="Output"
Done in 71 seconds.
```

**Check:** The folder `results` holds three files: `similar.txt`,
`groups.csv` and `compare.txt`. The first line of the table in
`compare.txt` reads:

```text title="results/compare.txt"
Defence           392     1    38   521    40     7     1     0
```

The numbers should be the same on every computer, because the model and
the seed are the same.

<details class="fix" markdown>
<summary>If it did not work</summary>

If you see `ModuleNotFoundError`, the packages are missing. Run `uv sync`
from step 1 again, in the project folder.

If you see `FileNotFoundError` with the name of the data file, either the
terminal is not in the project folder or the data are missing. Move into
the folder with `cd`, or repeat step 2.

If the model cannot be downloaded, check your internet connection. Some
networks block Hugging Face. Then try another network.

</details>

### 5. Measure what the job needs

The last line of the test shows how long the script took. To see its
memory, run it again and open the task manager while it runs: Activity
Monitor on macOS, Task Manager on Windows, System Monitor on Linux. Find
the process python and note the highest memory value you see.

On a CPU, the script takes about 71 seconds and uses about 1.1 GB of
memory. On the GPU, the embeddings take seconds, and the
rest of the script, such as loading the model, takes a few seconds more.

**Check:** You know roughly how long the script took and how much memory
it used.

## Part 2: Prepare the project for the cluster

### 6. Write the job script

A *job script* tells Slurm what the job needs and what it should do.
Create a file called `job.slurm`:

```bash title="job.slurm"
#!/bin/bash
# Turn all questions into embeddings on one GPU, find similar ones, group
# them. One job, so there is no runs.txt. Submit from your computer with
# `sc-starter submit`, after running `sc-starter submit setup.slurm` once.

#SBATCH --job-name=python-embeddings  # name in the queue and in the output file
#SBATCH --partition=gpu-a30           # machines with A30 GPUs; sinfo -s lists them all
#SBATCH --gpus=a30:1                  # one GPU of type a30 (type:count)
#SBATCH --cpus-per-task=2             # the GPU embeds; two cores do the rest
#SBATCH --mem=4G                      # about twice what the script used on a computer
#SBATCH --time=00:10:00               # Slurm stops the job after 10 minutes
#SBATCH --output=%x-%j.out            # job name and job ID
#SBATCH --mail-type=END,FAIL          # email when the job has ended or failed

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
book the GPU:

- `--partition=gpu-a30` sends the job to the nodes with A30 GPUs.
- `--gpus=a30:1` books one GPU of the type A30.

The others come from your measurement in step 5. Two cores load the
model and prepare the texts, while the GPU does the embeddings. 4 GB of
memory is about twice the 1.1 GB the script used. 10 minutes leave
plenty of room for a script that took about a minute on a CPU.
[What the job really used](#what-the-job-really-used) shows how to check
these values after the job.

Below the `#SBATCH` lines are the commands of the job. The line with
`PATH` tells bash where uv is, which the setup job installed.
`HF_HUB_OFFLINE=1` tells sentence-transformers to load the model from
the folder where the setup job saved it, and never to download during
the job. The last line runs the script once. As on your computer, it
starts the script with `uv run`. `--no-sync` makes uv take the packages
that the setup job installed as they are, and install nothing during the
job. [Your first job](../../../docs/slurm/first-job.md) explains every line of
a job script in more detail.

**Check:** The Explorer of your editor shows the file `job.slurm`, not
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

#SBATCH --job-name=python-embeddings-setup  # name in the queue and in the output file
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
Submitted job 28408071. See how it goes with `sc-starter status`.
```

Before this line, sc-starter prints how many files it uploaded. It copied
your project to the cluster, into `sc-projects/python-embeddings` in your
home directory there. Your `.venv` stayed on your computer, because the
cluster builds its own. Run `sc-starter status` every minute or so. The
first time, the job takes a few minutes, because PyTorch with its GPU
libraries is large.

**Check:** `sc-starter status` shows the job as `COMPLETED`, and the
output of `sc-starter log` ends with:

```text title="Output"
Model ready: sentence-transformers/all-MiniLM-L6-v2
```

Above it, the log may show a warning about "unauthenticated requests to
the HF Hub". It is harmless.

### 9. Start the job on the GPU

```bash title="Your computer"
sc-starter submit
```

```text title="Output"
Submitted job 28408127. See how it goes with `sc-starter status`.
```

Follow the job with `sc-starter status`. Many people want GPUs, so the
job may wait as `PENDING` for a while before it runs. That is normal.
When it has run, `sc-starter log` shows what it printed. Near the top, it
contains this line:

```text title="Output"
Embedded 8,000 questions in 3.9 seconds on NVIDIA A30, with sentence-transformers/all-MiniLM-L6-v2.
```

The embeddings took 3.9 seconds on the GPU, against about 65 seconds on
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

**Check:** `results/compare.txt` begins with the line about the GPU:
`Embedded 8,000 questions in … seconds on NVIDIA A30`.

## Reading the results

`results/compare.txt` holds the scores and the table:

```text title="results/compare.txt"
Embedded 8,000 questions in 3.9 seconds on NVIDIA A30, with sentence-transformers/all-MiniLM-L6-v2.

Adjusted Rand index:          0.37   (0: no better than chance, 1: groups = ministries)
Normalized mutual information: 0.46   (0: unrelated, 1: groups = ministries)

Questions of each ministry (rows) in each group (columns):

                    1     2     3     4     5     6     7     8
Defence           392     1    38   521    40     7     1     0
Education         110   705     2     0     7    60    19    97
Environment       112     1   623    34    15    78    21   116
Foreign Office     80    12    46   578    34   203     1    46
Health            153     7    44    29   757     9     0     1
Home Office       233    20    11    24     4   529    99    80
Transport         146     3    14     5     5    51   677    99
Treasury          186    11     9    10     6    99    38   641

Most common subjects in each group:

 1: Armed Forces, Asylum, Defence, Ministry of Defence
 2: Schools, Special Educational Needs, Pupils, Teachers
 3: Agriculture, Food, Flood Control, Water Charges
 4: Defence, Gaza, Sudan, Armed Forces
 5: Health Services, Cancer, NHS, Dental Services
 6: Asylum, Visas, Police, Immigration
 7: Railways, Roads, Bus Services, Electric Vehicles
 8: Small Businesses, Agriculture, Employers' Contributions, Taxation
```

Six groups each go mostly to one ministry: schools, farming and floods,
the NHS, asylum and policing, transport, and tax. Defence and the Foreign
Office share group 4, with Gaza, Sudan and the armed forces. Group 1 is
different: it holds 1,412 questions from all ministries. Half of them ask
for figures, such as "how many", "how much" or "what proportion",
compared with 1 to 4% in the other groups. So the model sorts partly by
what a question asks for, not only by its subject.

`results/similar.txt` holds the searches. "farmers hit by floods" found
"what steps he is taking to support farmers impacted by flooding", and
"crumbling concrete in school buildings" found questions about
"reinforced autoclaved aerated concrete" in schools. Neither shares many
words with its search. For "small boats crossing the Channel", the two
closest questions are about small boats, but the next three are about
boats and the sea in general, from other ministries. The questions are
shortened here:

```text title="results/similar.txt"
Search: "small boats crossing the Channel"
  0.57  Home Office: how many small boats crossing the English Channel have been towed by ...
  0.50  Home Office: what recent assessment she has made of the effectiveness of current ...
  0.41  Defence: what amphibious vessels are available to the a) Royal Navy and b) Royal ...
  0.36  Environment: what assessment she has made of the potential impact of bottom trawling ...
  0.36  Transport: what steps she plans to take to support the use of shore power technology ...
```

`results/groups.csv` lists every question with its ministry and its
group. You can open it in a spreadsheet.

### What the job really used

`reportseff` shows how much of the booked time, cores and memory a job
used. Type it with the job ID of your GPU job:

```bash title="Your computer"
ssh sc-login reportseff 28408127
```

```text title="Output"
     JobID    State       Elapsed  TimeEff   CPUEff   MemEff
  28408127  COMPLETED    00:00:19   2.1%     20.2%     7.6%
```

A first job booked more: six cores, 24 GB and 15 minutes.
It ran for 19 seconds, 2% of its time. It used about one of its six cores
and under 2 GB of its 24 GB of memory. That is why `job.slurm` on this
page books two cores, 4 GB and 10 minutes. Smaller jobs often start
sooner.

The same job on a node without a GPU, with six cores, took 37 seconds. The embeddings took 24.8 of them, and the table came out
exactly the same.

## Using the project with your own texts

Save your texts like `data/questions.csv.gz`, one row per text, with the
text in a column `question` and the categories you want to compare with
in a column `ministry`. The columns `id`, `date` and `heading` may be
empty. Then change `DATA` in `run.py`, and test the script on your
computer first.

For German texts, take a model for many languages, such as
`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`. Change
`MODEL` in `run.py`, and run `sc-starter submit setup.slurm` again before
the next job, so that the cluster downloads the new model. To try other
searches, change `SEARCHES` in `run.py`.

[Bring your own project](../../../docs/sc-starter/bring-your-own-project.md) goes through
these points for a project of your own.

## Removing the project from the cluster

When you no longer need the project on the cluster, delete its folder
there:

```bash title="Your computer"
ssh sc-export rm -rI sc-projects/python-embeddings
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
- Model: [all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)
  (Apache 2.0), through
  [sentence-transformers](https://sbert.net) (Apache 2.0): Reimers, N., &
  Gurevych, I. (2019). Sentence-BERT: Sentence embeddings using Siamese
  BERT-networks. *Proceedings of EMNLP-IJCNLP 2019*, 3982–3992.
  <https://doi.org/10.18653/v1/D19-1410>
- Groups and scores: [scikit-learn](https://scikit-learn.org) (BSD).
