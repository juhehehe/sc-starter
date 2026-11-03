# Text classifier on a GPU: teaching a language model which ministry a question goes to

In this example you train a small language model in Python. You test the
training on your computer and then run it on a GPU of the cluster.

Members of the UK House of Commons put written questions to the
government, and each question goes to the ministry in charge. In
[Text embeddings on a GPU](../python-embeddings/README.md), the computer
sorted 8,000 such questions into groups without knowing the ministries,
and the groups matched them only in part. Here a language model learns
from examples instead. It reads 6,400 questions together with their
ministry, and then predicts the ministry of 800 questions it has never
seen.

Training a language model runs much faster on a GPU than on the ordinary
processor of a computer, the CPU.

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

The packages include PyTorch, the library that does the calculations. On
Linux, it comes with the libraries for NVIDIA GPUs and needs about 6 GB
of disk space. On Windows and macOS it is much smaller. The project works
on Linux, on Windows and on Macs with Apple processors and macOS 14 or
newer. It does not work on older Macs with Intel processors.

The [embeddings code-along](../python-embeddings/README.md) uses the same
questions and explains more of the basics, such as the data. It helps to
do it first.

## Plan the project

The project starts from DistilBERT, a small language model that has read
a large amount of English text. A model like this calculates in stages
called *layers*. On top of DistilBERT, the script adds a new layer that
picks one of the eight ministries. *Training* means showing the
model questions with their ministry, again and again, and adjusting its
numbers so that it picks the right ministry more often. One pass through
all training questions is an *epoch*. The script trains for three.

To see what the training brings, the script compares three versions of
the model on the 800 questions it never saw:

- the model before any training
- the model with only the new layer trained
- the whole model trained

The script splits the questions into three parts. The model learns from
80%, 6,400 questions. After each epoch, the script checks it on 10%, and
it keeps the last 10% for the final test.

The whole project is one job on the cluster, with a single run. On a GPU of the cluster, the two trainings took 32
seconds. On a CPU, training on a sample of 400 questions takes two and a
half minutes. Training on all
questions would take about an hour there.

So you test the script on your computer with a small sample, and train
on all questions on the GPU. The script takes the size of the sample as
an *argument*. On your computer,
`uv run run.py 400` uses 400 questions. The job on the cluster runs
`python run.py`, which uses all of them. A sample needs at least 80
questions, so that each part holds every ministry.

When the project is finished, the folder looks like this:

```text title="python-classifier/"
python-classifier/
├── data/questions.csv.gz   the questions
├── pyproject.toml          the project's packages
├── uv.lock                 their exact versions
├── .python-version         the version of Python
├── run.py                  trains and tests the model
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
mkdir python-classifier
cd python-classifier
```

Open the folder in your editor. In VS Code, choose File › Open Folder and
select `python-classifier`. All further commands on this page run in this
folder. If you open a new terminal later, move into the folder again with
`cd`.

Create the file `pyproject.toml` in your editor:

```toml title="pyproject.toml"
[project]
name = "python-classifier"
version = "0.1.0"
description = "Teach a small language model on a GPU which ministry a parliamentary question goes to"
requires-python = ">=3.12"
# The versions this example was tested with. PyTorch from PyPI brings
# CUDA 13, which needs GPU driver 580 or newer and does not run on V100
# cards. The Trainer of transformers needs accelerate; scikit-learn splits
# the data and scores the predictions.
dependencies = [
    "accelerate==1.15.0",
    "scikit-learn==1.9.1",
    "torch==2.14.1",
    "transformers==5.20.2",
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

The part under `[project]` names the four packages the project needs, in
fixed versions, so that your results match the ones shown here:

- transformers loads DistilBERT and trains it.
- accelerate helps transformers to use the GPU.
- torch is PyTorch, which does the calculations.
- scikit-learn splits the questions into parts and scores the
  predictions.

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

**Check:** Ask transformers and torch for their versions:

```bash title="Your computer"
uv run python -c "import torch, transformers; print(torch.__version__, transformers.__version__)"
```

```text title="Output"
2.14.1+cu130 5.20.2
```

The ending `+cu130` means that this PyTorch can use *CUDA* 13, NVIDIA's
software for calculating on its GPUs. On Windows and macOS, the version
of torch ends differently or not at all.

### 2. Download the data

The data are the same questions as in the embeddings code-along: 8,000
written questions to eight ministries, asked in 2025 and answered, 1,000
per ministry. That page describes the file. Download it with curl. On
Windows, type `curl.exe` instead of `curl`:

```bash title="Your computer"
curl -L --create-dirs -o data/questions.csv.gz https://raw.githubusercontent.com/juhehehe/sc-starter/main/examples/python/python-classifier/data/questions.csv.gz
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
`run.py`. You will add the code in nine parts. Paste each part at the end
of the file.

The first part describes the script and imports the libraries:

```python title="run.py"
"""Teach a small language model which ministry a parliamentary question goes to.

Usage: python run.py [SAMPLE]
Reads data/questions.csv.gz, trains on 80% of the questions, tests on 10%
it never saw, and writes to results/ (with SAMPLE, such as 400, only that
many questions, for a quick test on your computer):
  scores.txt       accuracy before training, with only the new top layer
                   trained and with the whole model trained; F1 and the
                   table of ministries against predictions
  predictions.csv  each test question with its ministry and the predicted one
  model/           the trained model, to load with transformers
"""

import csv
import gzip
import os
import sys
from collections import Counter
from pathlib import Path

import torch
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    Trainer,
    TrainingArguments,
    set_seed,
)
```

The second part holds the settings. The model `distilbert-base-uncased`
is a small version of the language model BERT. It reads English and does
not tell capital letters from small ones. The first time you use it,
transformers downloads it from Hugging Face, a website that hosts
language models. `SEED` is the *seed*, the number that fixes all random
numbers of the script, so that it gives the same result every time on
the same kind of computer:

```python title="run.py"
DATA = Path("data/questions.csv.gz")
RESULTS = Path("results")
# A small English language model; setup.slurm downloads it.
MODEL = "distilbert/distilbert-base-uncased"
# How often the model goes through all training questions.
EPOCHS = 3
SEED = 1
```

The third part reads the questions and checks the GPU, as in the
embeddings code-along. On the cluster, Slurm sets the variable
`SLURM_GPUS_ON_NODE` when a job has a GPU. If
PyTorch then cannot use it, the script stops instead of training slowly
on the CPU:

```python title="run.py"
def read_questions(path):
    """Return one dict per question, with its ministry and its text."""
    with gzip.open(path, "rt", encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def check_gpu():
    """Stop if Slurm gave this job a GPU that PyTorch cannot use.

    Otherwise the model would quietly train on the CPU, slowly, while the
    booked GPU sits idle.
    """
    if os.environ.get("SLURM_GPUS_ON_NODE") and not torch.cuda.is_available():
        sys.exit("This job has a GPU, but PyTorch cannot use it. See README.md.")
```

The fourth part splits the questions into the three parts. *Stratified*
means that each part has the same share of each ministry:

```python title="run.py"
def split(questions):
    """80% to train on, 10% to check after each epoch, 10% for the final test.

    Stratified, so each part has the same share of each ministry; the seed
    makes the split the same in every run.
    """
    ministries = [question["ministry"] for question in questions]
    train, rest = train_test_split(
        questions, test_size=0.2, stratify=ministries, random_state=SEED
    )
    ministries = [question["ministry"] for question in rest]
    check, test = train_test_split(
        rest, test_size=0.5, stratify=ministries, random_state=SEED
    )
    return train, check, test
```

The fifth part turns the questions into the numbers the model reads. A
*tokenizer* cuts each question into words and pieces of words, and gives
each piece a number. The part also defines how the score is computed
after each epoch:

```python title="run.py"
def encode(questions, tokenizer, label_of):
    """Turn questions into the numbers the model reads, with their answer.

    No padding here: the Trainer pads each batch to its longest question.
    """
    tokens = tokenizer(
        [question["question"] for question in questions], truncation=True
    )
    return [
        {
            "input_ids": tokens["input_ids"][i],
            "attention_mask": tokens["attention_mask"][i],
            "labels": label_of[question["ministry"]],
        }
        for i, question in enumerate(questions)
    ]


def accuracy(prediction):
    """Return the share of questions put to the right ministry, after each epoch."""
    return {
        "accuracy": accuracy_score(
            prediction.label_ids, prediction.predictions.argmax(axis=1)
        )
    }
```

The sixth part builds the table of ministries against predictions, as in
the embeddings code-along:

```python title="run.py"
def table(truth, predicted, names):
    """Return the ministries (rows) against the predictions (columns), as text.

    The columns are numbered in the order of the rows, so correct
    predictions read as a diagonal, as in python-embeddings.
    """
    count = Counter(zip(truth, predicted, strict=True))
    numbers = range(1, len(names) + 1)
    lines = [f"{'':<15}" + "".join(f"{n:>6}" for n in numbers)]
    for name in names:
        lines.append(
            f"{name:<15}" + "".join(f"{count[name, other]:>6}" for other in names)
        )
    lines += [
        "",
        "Columns: " + ", ".join(f"{n} {name}" for n, name in enumerate(names, 1)),
    ]
    return lines
```

The seventh part loads the model and sets how to train it:

```python title="run.py"
def make_model(names, label_of):
    """Load the pre-trained model with a new layer on top that picks a ministry.

    The new layer starts from random numbers; setting the seed here makes
    them the same each time, so every variant starts from the same model.
    """
    set_seed(SEED)
    return AutoModelForSequenceClassification.from_pretrained(
        MODEL,
        num_labels=len(names),
        id2label=dict(enumerate(names)),
        label2id=label_of,
    )


def settings(learning_rate):
    """Return how to train: the same for both versions but the learning rate."""
    return TrainingArguments(
        output_dir=str(RESULTS),
        num_train_epochs=EPOCHS,
        learning_rate=learning_rate,
        per_device_train_batch_size=16,
        per_device_eval_batch_size=64,
        weight_decay=0.01,
        eval_strategy="epoch",
        # Training takes under a minute, so no checkpoints along the way;
        # python-long-run shows how to plan runs that take longer.
        save_strategy="no",
        logging_steps=100,
        # Mixed precision where the GPU supports it: faster, nearly the same results.
        bf16=torch.cuda.is_available() and torch.cuda.is_bf16_supported(),
        # The GPU if there is one, else the CPU: the same on every computer,
        # also on Macs, whose own GPU the Trainer would otherwise pick.
        use_cpu=not torch.cuda.is_available(),
        # Progress bars would fill the Slurm output file.
        disable_tqdm=True,
        report_to="none",
        seed=SEED,
    )
```

`make_model()` loads DistilBERT and puts the new layer on top, one output
for each ministry. The new layer starts from random numbers, and
`set_seed()` makes them the same every time. `settings()` describes the
training: three epochs, 16 questions at a time, and a check after each
epoch. The *learning rate* sets how far the model adjusts its numbers at
each step. `use_cpu` makes the script train on the CPU when there is no
NVIDIA GPU, also on Macs, so that it behaves the same everywhere.

The eighth part asks the model for its predictions:

```python title="run.py"
def guesses(trainer, test_set, names):
    """Return the ministry that the model picks for each test question."""
    prediction = trainer.predict(test_set)
    return [names[i] for i in prediction.predictions.argmax(axis=1)]
```

The last part puts everything together:

```python title="run.py"
def main():
    """Train and test both versions of the model, and write the results."""
    check_gpu()
    # PyTorch would start a thread for every core of the node; as many as
    # job.slurm booked, so they do not crowd onto the booked cores.
    if "SLURM_CPUS_PER_TASK" in os.environ:
        torch.set_num_threads(int(os.environ["SLURM_CPUS_PER_TASK"]))

    questions = read_questions(DATA)
    # A sample with the same share from each ministry, for a quick test.
    if len(sys.argv) > 1:
        questions, _ = train_test_split(
            questions,
            train_size=int(sys.argv[1]),
            stratify=[question["ministry"] for question in questions],
            random_state=SEED,
        )
    # The ministries in order, each with a number, as the model needs.
    names = sorted({question["ministry"] for question in questions})
    label_of = {name: i for i, name in enumerate(names)}
    train, check, test = split(questions)
    truth = [question["ministry"] for question in test]

    # The three parts, turned into the numbers that the model reads.
    tokenizer = AutoTokenizer.from_pretrained(MODEL)
    train_set = encode(train, tokenizer, label_of)
    check_set = encode(check, tokenizer, label_of)
    test_set = encode(test, tokenizer, label_of)

    # The whole model learns: the new layer and the pre-trained model below
    # it. Learning rate, batch size and weight decay as in the Hugging Face
    # guide to text classification with this model.
    trainer = Trainer(
        model=make_model(names, label_of),
        args=settings(learning_rate=2e-5),
        train_dataset=train_set,
        eval_dataset=check_set,
        processing_class=tokenizer,
        compute_metrics=accuracy,
    )
    # The same model before any training, for comparison.
    before = accuracy_score(truth, guesses(trainer, test_set, names))
    print("Training the whole model.")
    output = trainer.train()
    print(f"Trained in {output.metrics['train_runtime']:.0f} seconds.")
    predicted = guesses(trainer, test_set, names)

    # For comparison: only the new layer learns, the pre-trained model below
    # it stays as it is. Its larger learning rate is a choice: a new layer
    # alone hardly moves in three epochs with the small steps that suit the
    # whole model, and the comparison would be unfair.
    model = make_model(names, label_of)
    for parameter in model.base_model.parameters():
        parameter.requires_grad = False
    top_trainer = Trainer(
        model=model,
        args=settings(learning_rate=1e-3),
        train_dataset=train_set,
        eval_dataset=check_set,
        processing_class=tokenizer,
        compute_metrics=accuracy,
    )
    print("Training only the new top layer.")
    output = top_trainer.train()
    print(f"Trained in {output.metrics['train_runtime']:.0f} seconds.")
    top_only = accuracy_score(truth, guesses(top_trainer, test_set, names))

    # The trained model, and each test question with the predicted ministry.
    RESULTS.mkdir(exist_ok=True)
    trainer.save_model(str(RESULTS / "model"))
    # UTF-8: a few questions hold letters that Windows' own encoding
    # cannot write.
    with open(RESULTS / "predictions.csv", "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["id", "ministry", "predicted", "heading", "question"])
        for question, guess in zip(test, predicted, strict=True):
            writer.writerow(
                [
                    question["id"],
                    question["ministry"],
                    guess,
                    question["heading"],
                    question["question"],
                ]
            )

    # The scores and the table, into scores.txt and onto the screen.
    lines = [
        f"{MODEL}, trained {EPOCHS} epochs on {len(train):,} questions; "
        f"tested on {len(test):,} questions it never saw.",
        "",
        "Accuracy, the share put to the right ministry:",
        f"  before training                  {before:.2f}",
        f"  only the new top layer trained   {top_only:.2f}",
        f"  whole model trained              {accuracy_score(truth, predicted):.2f}",
        "",
        "The whole model trained:",
        "",
        f"Macro F1: {f1_score(truth, predicted, average='macro'):.2f}   "
        "(0 to 1, each ministry counts the same)",
        "",
        "Questions of each ministry (rows) by predicted ministry (columns):",
        "",
        *table(truth, predicted, names),
    ]
    report = "\n".join(lines)
    (RESULTS / "scores.txt").write_text(report + "\n", encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
```

`main()` first checks the GPU and limits PyTorch to the cores the job
booked. With an argument, it then takes a sample of that many questions, with the same
share from each ministry. It splits the questions and tests the model
before training. Then it trains the whole model, and after that a second
copy with only the new layer. The other layers of that copy are frozen:
`requires_grad = False` tells PyTorch not to change them.

Last, the script saves the trained model, the predictions and the
scores into `results`, as UTF-8, so that letters such as "đ" in a few
questions work on every system.

**Check:** Save the file and ask Python for one of its settings:

```bash title="Your computer"
uv run python -c "import run; print(run.MODEL)"
```

```text title="Output"
distilbert/distilbert-base-uncased
```

This loads the file without starting it, so it shows that the file is
saved and free of errors such as a missing bracket.

### 4. Test the training on your computer

Train on a sample of 400 questions:

```bash title="Your computer"
uv run run.py 400
```

The first time, transformers downloads DistilBERT, about 270 MB. It may
warn that you send "unauthenticated requests to the HF Hub" and, on
Windows, that it cannot create symlinks. Both warnings are harmless.

The script then prints a `LOAD REPORT`. The rows marked `UNEXPECTED` are
parts of DistilBERT for guessing words, which this project does not use.
The rows marked `MISSING` are the new parts on top that pick the
ministry, which the training fills. So the report is expected.

During the training, nothing appears for a while. After each epoch, the
script prints a line that contains `eval_accuracy`, the share of the
check questions it got right.

Training the whole model takes about two minutes and training the new
layer under one. At the end, the script
prints the scores:

```text title="Output"
distilbert/distilbert-base-uncased, trained 3 epochs on 320 questions; tested on 40 questions it never saw.

Accuracy, the share put to the right ministry:
  before training                  0.17
  only the new top layer trained   0.65
  whole model trained              0.65
```

Your numbers may differ by a few hundredths. With 40 test questions, a
single question moves the accuracy by 0.025, and other computers
calculate slightly differently. With so few questions, the model learns
little, and 40 test questions are too few to compare the versions. That
is fine. The test only shows that the script works from start to end.

**Check:** The folder `results` holds `scores.txt`, `predictions.csv` and
a folder `model` with the trained model.

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

The two lines that start with `Trained in` show how long the trainings
took. Loading Python, the model and the data takes about 25 seconds more.
The test takes about three minutes and uses about 2.1 GB of memory. To see the memory on your computer, run
the test again and open the task manager while it runs: Activity Monitor
on macOS, Task Manager on Windows, System Monitor on Linux. Find the
process python and note the highest value you see.

On the GPU, both trainings on all questions take under a minute. Loading
Python, the model and the data takes a few seconds more.

Then delete the folder `results`, for example in the Explorer of VS Code.
It holds the model from the test, about 260 MB. sc-starter never sends
`results` to the cluster, but it takes up space on your computer.

**Check:** You know roughly how long the test took and how much memory it
used, and the folder `results` is gone.

## Part 2: Prepare the project for the cluster

### 6. Write the job script

A *job script* tells Slurm what the job needs and what it should do.
Create a file called `job.slurm`:

```bash title="job.slurm"
#!/bin/bash
# Train the classifier on one GPU. One job, so there is no runs.txt. Submit
# from your computer with `sc-starter submit`, after running
# `sc-starter submit setup.slurm` once.

#SBATCH --job-name=python-classifier  # name in the queue and in the output file
#SBATCH --partition=gpu-a30           # machines with A30 GPUs; sinfo -s lists them all
#SBATCH --gpus=a30:1                  # one GPU of type a30 (type:count)
#SBATCH --cpus-per-task=2             # the GPU trains; two cores do the rest
#SBATCH --mem=6G                      # more than twice what the job used
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
book the GPU: `--partition=gpu-a30` sends the job to the nodes with
A30 GPUs, and `--gpus=a30:1` books one of them.

The others come from your measurement in step 5. Two cores load the data
and the model, while the GPU trains. 6 GB of memory is more than twice
the 2.1 GB of the test, because all questions take more memory than 400.
10 minutes leave plenty of room for a job that takes about a minute on
the GPU.

Below the `#SBATCH` lines are the commands of the job. The line with
`PATH` tells bash where uv is, which the setup job installed.
`HF_HUB_OFFLINE=1` tells transformers to load the model from the folder
where the setup job saved it, and never to download during the job. The
last line runs the script on all questions, without an argument. As on
your computer, it starts the script with `uv run`. `--no-sync` makes uv
take the packages that the setup job installed as they are, and install
nothing during the job. [Your first job](../../../docs/slurm/first-job.md)
explains every line of a job script in more detail.

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

#SBATCH --job-name=python-classifier-setup  # name in the queue and in the output file
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

# Load the model named in run.py and its tokenizer once, which downloads
# them into the Hugging Face cache, ~/.cache/huggingface. The GPU job loads
# them from there.
.venv/bin/python -c 'from run import MODEL; from transformers import AutoModel, AutoTokenizer; AutoTokenizer.from_pretrained(MODEL); AutoModel.from_pretrained(MODEL); print("Model ready:", MODEL)'
```

The first part installs uv for your account if it is not there yet, and
then installs exactly the package versions from `uv.lock`. The last line
loads the model and its tokenizer once, which downloads them into a
folder in your home directory on the cluster.
[Packages: uv and renv](../../../docs/project/packages.md) explains the setup job
in general.

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
Submitted job 28410300. See how it goes with `sc-starter status`.
```

Before this line, sc-starter prints how many files it uploaded. It copied
your project to the cluster, into `sc-projects/python-classifier` in your
home directory there. Run `sc-starter status` every minute or so. The
first time, the job takes a few minutes, because PyTorch with its GPU
libraries is large.

**Check:** `sc-starter status` shows the job as `COMPLETED`, and the
output of `sc-starter log` ends with:

```text title="Output"
Model ready: distilbert/distilbert-base-uncased
```

Above it, the log may show a warning about "unauthenticated requests to
the HF Hub". It is harmless.

### 9. Train on the GPU

```bash title="Your computer"
sc-starter submit
```

```text title="Output"
Submitted job 28410356. See how it goes with `sc-starter status`.
```

Follow the job with `sc-starter status`. Many people want GPUs, so the
job may wait as `PENDING` for a while before it runs. That is normal.
When it has run, `sc-starter log` shows the two trainings, first the
whole model, then only the new layer. The lines with `eval_accuracy`
after the three epochs of the whole model read `0.8738`, `0.8912` and
`0.8988`. Each training ends with a line such as:

```text title="Output"
Trained in 22 seconds.
```

Your job IDs and times will differ. The scores should match.

**Check:** `sc-starter status` shows the job as `COMPLETED`, and the log
ends with the scores.

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
folder, together with the output files of both jobs. The trained model
in `results/model` is about 260 MB, so this may take a moment.

**Check:** `results/scores.txt` begins with
`distilbert/distilbert-base-uncased, trained 3 epochs on 6,400 questions`.

## Reading the results

`results/scores.txt`:

```text title="results/scores.txt"
distilbert/distilbert-base-uncased, trained 3 epochs on 6,400 questions; tested on 800 questions it never saw.

Accuracy, the share put to the right ministry:
  before training                  0.13
  only the new top layer trained   0.79
  whole model trained              0.89

The whole model trained:

Macro F1: 0.89   (0 to 1, each ministry counts the same)

Questions of each ministry (rows) by predicted ministry (columns):

                    1     2     3     4     5     6     7     8
Defence            88     2     1     4     2     2     0     1
Education           0    91     0     1     2     2     1     3
Environment         2     0    92     1     2     0     1     2
Foreign Office      9     1     0    84     1     2     0     3
Health              2     2     3     2    90     1     0     0
Home Office         0     0     5     3     1    81     5     5
Transport           0     0     2     0     0     0    97     1
Treasury            1     1     1     2     0     3     2    90

Columns: 1 Defence, 2 Education, 3 Environment, 4 Foreign Office, 5 Health, 6 Home Office, 7 Transport, 8 Treasury
```

Before training, the model put 13% of the test questions right. That is
as good as guessing one ministry in eight. With only the new layer
trained, it put 79% right. DistilBERT already tells subjects apart, and a
single layer on top learns to read the ministry from that. Training the
whole model adds another ten points, to 89%. *Macro F1* is a second score
from 0 to 1. It scores each ministry by its right, wrong and missed
predictions, and then averages over the ministries, so that each
ministry counts the same.

The table reads as a clear diagonal, unlike the groups in the embeddings
code-along. Nine Foreign Office questions went to Defence, the most
common mistake. They are about the military base on the Chagos Islands,
arms exports to Israel and the law of armed combat. The Home Office is
the hardest ministry, with 81 of 100 right and its mistakes spread over
five others. It answers for more than its name says, such as animal
experiments, which the model put to Environment.

`results/predictions.csv` lists every test question with its ministry and
the predicted one. The 87 mistakes are the rows in which the two differ.
You can open the file in a spreadsheet.

### What the job really used

`reportseff` shows how much of the booked time, cores and memory a job
used. Type it with the job ID of your GPU job:

```bash title="Your computer"
ssh sc-login reportseff 28410356
```

```text title="Output"
     JobID    State       Elapsed  TimeEff   CPUEff   MemEff
  28410356  COMPLETED    00:00:46   5.1%     22.8%    14.5%
```

A first job booked more: four cores, 16 GB and 15 minutes. It ran for 46
seconds, 5% of its time. It used about one of its four cores and under 3 GB of its memory. That is why `job.slurm` on this
page books two cores, 6 GB and 10 minutes.

## Using the project with your own texts

Save your texts like `data/questions.csv.gz`, one row per text, with the
text in a column `question` and its category in a column `ministry`. The
columns `id` and `heading` may be empty. Then change `DATA` in `run.py`,
and test the script on your computer with a small sample first.

For German texts, take a German model, such as
`distilbert/distilbert-base-german-cased`. Change `MODEL` in `run.py`, and
run `sc-starter submit setup.slurm` again before the next job, so that the
cluster downloads the new model.

Training that takes hours needs a plan for the time limit of the job,
which is at most two days on this cluster. The Trainer can save
checkpoints and continue from them, as
[Runs longer than the time limit](../python-long-run/README.md#planning-a-long-computation-of-your-own)
describes.

[Bring your own project](../../../docs/sc-starter/bring-your-own-project.md) goes through
these points for a project of your own.

## Removing the project from the cluster

When you no longer need the project on the cluster, delete its folder
there, with the trained model:

```bash title="Your computer"
ssh sc-export rm -rI sc-projects/python-classifier
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
- Model: [distilbert-base-uncased](https://huggingface.co/distilbert/distilbert-base-uncased)
  (Apache 2.0): Sanh, V., Debut, L., Chaumond, J., & Wolf, T. (2019).
  DistilBERT, a distilled version of BERT: smaller, faster, cheaper and
  lighter. <https://doi.org/10.48550/arXiv.1910.01108>
- Training: [transformers](https://huggingface.co/docs/transformers)
  (Apache 2.0) and its
  [guide to text classification](https://huggingface.co/docs/transformers/tasks/sequence_classification).
