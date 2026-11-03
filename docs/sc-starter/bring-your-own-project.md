# Bring your own project

This page is the roadmap for a project of your own in Python or R, from
your computer to results from the cluster. Part 1 prepares the project:
what to change in your code and which files it needs. It is the same
with or without sc-starter. Part 2 runs the project on the cluster with
sc-starter. Each step links to the page with the details.

You need a computer that is set up as described in
[Set up your computer](../basics/setup.md), and for Part 2
[sc-starter](install.md). It helps to have done one code-along first,
such as
[Topic model in Python](../../examples/python/python-topic-model/README.md),
and to keep it open as an example.

## Part 1: Prepare your project

### 1. Decide what one run is

Think first about how your work splits into runs. A run is one execution
of your script with one setting. Typical runs are:

- one model for each number of topics, each set of variables or each
  sample
- one simulation for each seed or each combination of parameters
- one computation that is too long or too large for your computer, as a
  single run

Then estimate how long one run takes on your computer. A few runs of a
few minutes each do not need the cluster. The cluster helps with dozens
of runs, with runs of hours, and with runs that need a GPU or more memory
than your computer has.

**Check:** you can say what changes from run to run, how many runs there
are and how long one run takes.

### 2. Put the project into one folder

Put your scripts, your data and nothing else into one folder. Give it a
name with only letters, digits, dots, hyphens and underscores, such as
`survey-models`. Change every path in your code so that it starts inside
this folder, such as `data/survey.csv`. On the cluster, every run starts
in the copy of the project folder, so such paths work on your computer
and on the cluster. A full path from your computer, such as
`C:\Users\you\Documents\survey.csv`, does not exist on the cluster.

Small data, up to a few hundred megabytes, can live in `data/` in the
project. sc-starter sends it once and later only when it changes. Large
data, or data that several projects share, belongs in a folder of its
own on the cluster.
[Copying files to and from the cluster](../project/copying-files.md#large-data)
explains how to copy it, how your script finds it, and what to check
before you copy data to the cluster. Other users of the cluster cannot
read your home directory or the projects in it.

**Check:** copy the folder to another place on your computer and run the
script there. It still finds its data.

### 3. Write down the packages

Set up a package manager in the folder, if you do not use one yet, and
install your packages with it:

=== "Python"

    ```bash title="Your computer"
    uv init --bare --python 3.12
    uv python pin 3.12
    uv add numpy pandas
    ```

    Name the packages your project uses after `uv add`.

=== "R"

    Open R in the project folder, as described in
    [Starting a project](../project/packages.md#starting-a-project). In RStudio,
    choose File › New Project › Existing Directory. Then:

    ```r title="R"
    install.packages("renv")
    renv::init()
    ```

    `renv::init()` finds the packages that your scripts load and records
    them in `renv.lock`.

[Packages: uv and renv](../project/packages.md) explains both.

**Check:** for Python, `uv sync --locked` runs without an error. For R,
`renv::status()` reports that the project is in a consistent state.

### 4. Make one run one command

The cluster runs your script many times at once, on computers without a
screen, in a copy of your folder. Each rule below follows from that.

#### One run is one command with one setting

Whatever changes between runs, such as the number of topics or a seed,
is an *argument* of your script. Your script reads it at the start:

=== "Python"

    ```python title="run.py"
    import sys

    k = int(sys.argv[1])  # python run.py 10 gives k = 10
    ```

=== "R"

    ```r title="run.R"
    args <- commandArgs(trailingOnly = TRUE)
    k <- as.integer(args[1])  # Rscript run.R 10 gives k = 10
    ```

#### Each run writes its own file into results/

Runs that end at the same time would overwrite one shared file. So each
run writes its own file, with its setting in the name, such as
`results/k-10.csv`.

#### Random numbers have a seed

A *seed* is a number that fixes the random numbers a program draws. With
the same seed, a run gives the same result again, on your computer and on
the cluster. Fix it in the script, or take it as an argument when the
runs differ only in their seed.

#### A run uses the cores it booked

A compute node has dozens of cores, and many libraries use all of them
unless you tell them otherwise. Slurm then squeezes all this work onto
the few cores that your run booked, and everything slows down. Read the
number of booked cores from the environment variable
`SLURM_CPUS_PER_TASK`, and pass it to the library:

=== "Python"

    ```python title="run.py"
    import os

    cores = int(os.environ.get("SLURM_CPUS_PER_TASK", "1"))
    ```

=== "R"

    ```r title="run.R"
    cores <- as.integer(Sys.getenv("SLURM_CPUS_PER_TASK", "1"))
    ```

On your computer the variable does not exist, and the script uses one
core. Do not use `os.cpu_count()` or `parallel::detectCores()`, which
count all cores of the node.

#### A run asks no questions and shows no windows

Nobody watches a run while it works. A question such as `input()` in
Python or `readline()` in R gets no answer. Save figures to a file
instead of showing them. R needs one more line at the top of the
script, because compute nodes have no screen and R's usual way of saving
PNG files fails there:

```r title="run.R"
options(bitmapType = "cairo")
```

#### Runs download nothing

If every run downloaded the same data or model, many downloads would run
at once. Download them once, in the setup job or on your computer, and let
the runs read them from the project folder.

#### A run takes minutes, not seconds

Slurm needs a moment to start each run. If one run takes only a few
seconds, let one line of `runs.txt` do several of them, so that each run
takes about ten minutes or more.

**Check:** one run works from the terminal, with the setting as an
argument, such as `uv run python run.py 10` or `Rscript run.R 10`. It
writes one file into `results/`.

### 5. List the runs

Create the file `runs.txt` with one command per line, one line for each
run. Line 1 is run 1, line 2 is run 2, and so on:

```text title="runs.txt"
python run.py 5
python run.py 10
python run.py 20
```

The file may not have empty lines, comments or lines that end in `\`.
`sc-starter submit` checks this and names the line it does not accept.

For Python, the lines start with `python`, not `uv run python`, because
the job script runs each line with `uv run` itself. On your computer you
test the same line with `uv run` in front, as in
`uv run python run.py 5`. For R, the lines start with `Rscript`, without
`--vanilla`, so that R finds the project's packages.
[Many runs: job arrays](../slurm/job-arrays.md) shows how a job script reads its
line.

If your project has a single run, leave out `runs.txt`, as described in
[A project with a single run](#a-project-with-a-single-run).

**Check:** the first line of `runs.txt` runs on your computer, with
`uv run` in front for Python.

### 6. Measure the largest run

Find the run that will take longest, usually the one with the largest
setting. Run its line of `runs.txt` on your computer and watch how long
it takes and how much memory it uses. The task manager of your computer shows the
memory: the Activity Monitor on macOS, the Task Manager on Windows, and
the System Monitor on Linux. Write both numbers down, and the main
numbers of its result, so that you can compare them with the run on the
cluster in step 9.
[Choosing time and memory](../slurm/time-and-memory.md) explains how to estimate
and check what a job needs.

**Check:** you know how many minutes the largest run took, roughly how
much memory it used, and what it found.

### 7. Write the job scripts

#### The job script for the runs

This job script runs one line of `runs.txt` per run. Copy it into your
project as `job.slurm`, and change the four values described below it.
[Your first job](../slurm/first-job.md) explains the `#SBATCH` lines and
[Many runs: job arrays](../slurm/job-arrays.md#the-job-script) the lines that
read `runs.txt`. [Packages: uv and renv](../project/packages.md#on-the-cluster-the-setup-job)
explains the lines with uv, and [R and Python in a job](../slurm/r-and-python.md)
those with `module load`.

=== "Python"

    ```bash title="job.slurm"
    #!/bin/bash
    #SBATCH --job-name=my-project
    #SBATCH --partition=cpu-xeonv3
    #SBATCH --cpus-per-task=1
    #SBATCH --mem=2G
    #SBATCH --time=00:20:00
    #SBATCH --output=%x-%A_%a.out
    #SBATCH --mail-type=END,FAIL

    # uv, which setup.slurm installed for your account.
    export PATH="$HOME/.local/bin:$PATH"

    # This run's line of runs.txt, and nothing if there is no such line.
    run=$(sed -n "${SLURM_ARRAY_TASK_ID}p" runs.txt)
    [ -n "$run" ] || { echo "runs.txt has no line $SLURM_ARRAY_TASK_ID"; exit 1; }
    echo "Run $SLURM_ARRAY_TASK_ID on $(hostname -s): $run"
    # The line, with the packages that setup.slurm installed.
    uv run --no-sync bash -c "$run"
    ```

=== "R"

    ```bash title="job.slurm"
    #!/bin/bash
    #SBATCH --job-name=my-project
    #SBATCH --partition=cpu-xeonv3
    #SBATCH --cpus-per-task=1
    #SBATCH --mem=2G
    #SBATCH --time=00:20:00
    #SBATCH --output=%x-%A_%a.out
    #SBATCH --mail-type=END,FAIL

    # The same R that setup.slurm installed the packages for.
    module load R/4.5.2-gfbf-2025b
    export LC_ALL=C.UTF-8

    # This run's line of runs.txt, and nothing if there is no such line.
    run=$(sed -n "${SLURM_ARRAY_TASK_ID}p" runs.txt)
    [ -n "$run" ] || { echo "runs.txt has no line $SLURM_ARRAY_TASK_ID"; exit 1; }
    echo "Run $SLURM_ARRAY_TASK_ID on $(hostname -s): $run"
    bash -c "$run"
    ```

Change these values to fit your project:

- `--job-name`: the name of your project.
- `--time`: about twice as long as your largest run took on your
  computer.
- `--mem`: about twice the memory that your largest run used on your
  computer.
- `--cpus-per-task`: the number of cores one run uses. One, unless your
  code uses more and reads `SLURM_CPUS_PER_TASK`.

Keep the line `--output=%x-%A_%a.out` as it is: `sc-starter log` finds
the output file of a run by this name. Do not write `--array` into the
job script. sc-starter sets it from the number of lines in `runs.txt`,
and by hand you give it to `sbatch`, as
[Many runs: job arrays](../slurm/job-arrays.md#submitting-the-runs) shows. Step
10 lowers time and memory after a first run on the cluster.

If your project needs a GPU, see
[Asking for a GPU](../slurm/gpu-jobs.md).

#### The setup job

The setup job installs the project's packages on the cluster, once. Copy
it into your project as `setup.slurm`, and change the job name.

A Python project always needs it, because it also installs uv and
Python and creates `.venv`, which the job script uses. Only a project that
uses nothing but R itself, or nothing but Python's standard library, can
leave it out. Its job script then loads R or Python as a module, as the
code-alongs on segregation in R and on long runs do.

=== "Python"

    ```bash title="setup.slurm"
    #!/bin/bash
    #SBATCH --job-name=my-project-setup
    #SBATCH --partition=cpu-xeonv3
    #SBATCH --cpus-per-task=1
    #SBATCH --mem=2G
    #SBATCH --time=00:15:00
    #SBATCH --output=%x-%j.out

    # Stop at the first command that fails, so that the job ends as FAILED.
    set -e

    # uv, installed for your account the first time.
    export PATH="$HOME/.local/bin:$PATH"
    if ! command -v uv > /dev/null; then
      curl -LsSf https://astral.sh/uv/0.12.10/install.sh | env UV_NO_MODIFY_PATH=1 sh
    fi

    # Exactly the versions in uv.lock, into .venv.
    uv sync --locked
    ```

=== "R"

    ```bash title="setup.slurm"
    #!/bin/bash
    #SBATCH --job-name=my-project-setup
    #SBATCH --partition=cpu-xeonv3
    #SBATCH --cpus-per-task=2
    #SBATCH --mem=4G
    #SBATCH --time=00:30:00
    #SBATCH --output=%x-%j.out

    # Stop at the first command that fails, so that the job ends as FAILED.
    set -e

    module load R/4.5.2-gfbf-2025b
    export LC_ALL=C.UTF-8
    # Compile with both cores, if a package comes as source code.
    export MAKEFLAGS="-j${SLURM_CPUS_PER_TASK}"

    # Exactly the versions in renv.lock, into renv/library.
    Rscript -e 'renv::restore(prompt = FALSE)'
    ```

[Packages: uv and renv](../project/packages.md#on-the-cluster-the-setup-job)
explains these lines.

#### A project with a single run

Some projects run once: one long computation, or one job on a GPU. Leave
out `runs.txt`. `sc-starter submit` then starts `job.slurm` once, and the
job script runs your script directly instead of reading a line of
`runs.txt`:

=== "Python"

    ```bash title="job.slurm"
    #!/bin/bash
    #SBATCH --job-name=my-project
    #SBATCH --partition=cpu-xeonv3
    #SBATCH --cpus-per-task=1
    #SBATCH --mem=2G
    #SBATCH --time=02:00:00
    #SBATCH --output=%x-%j.out
    #SBATCH --mail-type=END,FAIL

    export PATH="$HOME/.local/bin:$PATH"
    uv run --no-sync python run.py
    ```

=== "R"

    ```bash title="job.slurm"
    #!/bin/bash
    #SBATCH --job-name=my-project
    #SBATCH --partition=cpu-xeonv3
    #SBATCH --cpus-per-task=1
    #SBATCH --mem=2G
    #SBATCH --time=02:00:00
    #SBATCH --output=%x-%j.out
    #SBATCH --mail-type=END,FAIL

    module load R/4.5.2-gfbf-2025b
    export LC_ALL=C.UTF-8
    Rscript run.R
    ```

The output file is named with `%x-%j.out`, as for the setup job, so that
`sc-starter log` finds it without a run number. The code-along
[Text embeddings on a GPU](../../examples/python/python-embeddings/README.md)
is such a project, with a GPU.

**Check:** `job.slurm` names your project after `--job-name`, and the
folder holds `job.slurm`, `runs.txt` if you have several runs, and
`setup.slurm` if you need one.

## Part 2: Run it with sc-starter

The steps of this part use sc-starter. By hand, they are those of
[Your first job](../slurm/first-job.md) and
[Many runs: job arrays](../slurm/job-arrays.md): copy the folder, submit with
`sbatch`, follow the runs, and copy the results back.

### 8. Install the packages on the cluster

```bash title="Your computer"
sc-starter submit setup.slurm
sc-starter status
```

The first command sends the project to the cluster and starts the setup
job. Repeat `sc-starter status` until the job has ended. A project
without `setup.slurm` skips this step.

**Check:** `sc-starter status` shows the setup job as `COMPLETED`. If it
shows `FAILED`, `sc-starter log` shows the error. Fix it and start the
setup job again.

### 9. Try the largest run on the cluster

Write the number of the largest run, which is its line in `runs.txt`,
into a file called `first.txt`. For run 1:

=== "Linux"

    ```bash title="Your computer"
    echo 1 > first.txt
    ```

=== "macOS"

    ```bash title="Your computer"
    echo 1 > first.txt
    ```

=== "Windows"

    ```powershell title="Your computer"
    Set-Content first.txt 1
    ```

    In Windows PowerShell, `echo 1 > first.txt` would save the file in
    a form that sc-starter cannot read.

Then start only that run:

```bash title="Your computer"
sc-starter submit --lines first.txt
sc-starter status
```

When it has completed, look at what it printed and bring its result
back:

```bash title="Your computer"
sc-starter log 1
sc-starter pull
```

A project with a single run submits it with `sc-starter submit` and
skips the file `first.txt`.

**Check:** the result from the cluster shows the numbers that you wrote
down in step 6, apart from the last decimal places.

### 10. Adjust time and memory

Ask how much of the booked time and memory the run used, with the job ID
that `submit` printed:

```bash title="Your computer"
ssh sc-login reportseff 28514701
```

Lower `--time` and `--mem` in `job.slurm` to about a quarter more than
the run used. The other runs are smaller, so they fit too. Smaller jobs
start sooner, because Slurm finds room for them more easily. If the column `CPUEff` shows much less than 100 % with
several cores, your code used fewer cores than it booked.
[Choosing time and memory](../slurm/time-and-memory.md#checking-what-a-job-used)
explains the columns.

**Check:** the values in `job.slurm` are a little above what the run
used.

### 11. Start all runs

```bash title="Your computer"
sc-starter submit
```

Follow the runs with `sc-starter status`, and bring the results back with
`sc-starter pull` when they have completed. If runs fail,
[When runs fail](working-with-sc-starter.md#when-runs-fail) explains how
to find out why and how to start just those again. Put the results
together on your computer with a script of your own, as the code-alongs
do with `combine.py` or `combine.R`.

**Check:** `sc-starter status` shows every run as `COMPLETED`, and
`results/` on your computer holds one file per run.

### 12. Clean up

When you have your results, remove the project's copy from the cluster,
as described in [Cleaning up](working-with-sc-starter.md#cleaning-up):

```bash title="Your computer"
ssh sc-export rm -rI sc-projects/survey-models
```

**Check:** `ssh sc-export ls sc-projects` no longer lists the project.
