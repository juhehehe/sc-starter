# Command reference

This page lists every sc-starter command, with its options, its output and
its most common messages.
[Working with sc-starter](working-with-sc-starter.md) explains what
happens behind them.

| Command | What it does |
|---|---|
| [`sc-starter check`](#check) | tests the connection to the cluster |
| [`sc-starter submit`](#submit) | uploads the project and starts `job.slurm`, one run per line of `runs.txt` |
| [`sc-starter submit SCRIPT`](#submit) | uploads the project and runs another job script once, such as `setup.slurm` |
| [`sc-starter status`](#status) | shows how each run of the last job is doing |
| [`sc-starter log RUN`](#log) | shows what a run printed |
| [`sc-starter pull`](#pull) | brings the results and output files back |
| [`sc-starter push`](#push) | uploads the project without starting a job |
| [`ssh sc-login scancel JOB_ID`](#stopping-a-job) | stops a job; this is a Slurm command, not part of sc-starter |
| `sc-starter --help` | lists the commands; `sc-starter submit --help` lists the options of one |
| `sc-starter --version` | shows the installed version |

## check

```text title="Usage"
sc-starter check
```

Connects once to each of the two nodes that sc-starter uses. You can run it in
any folder.

```text title="Output"
sc-login: ok (login01)
sc-export: ok (export01)
Ready.
```

If the connection fails, the message names the step of the setup guide
that solves the problem, such as connecting the VPN. See also
[I cannot connect](../reference/troubleshooting.md#connecting-to-the-cluster).

## submit

```text title="Usage"
sc-starter submit [SCRIPT] [--lines FILE]
```

Uploads what is new or changed in the project and then hands a job script
to Slurm.

| You type | What starts |
|---|---|
| `sc-starter submit` | `job.slurm`, once for each line of `runs.txt`, or once if there is no `runs.txt` |
| `sc-starter submit setup.slurm` | `setup.slurm` or any other job script you name, once |
| `sc-starter submit --lines failed.txt` | only the runs whose numbers are listed in the file, one number per line |

```text title="Output"
Uploaded 10 files (1.7 MB) to sc-export:~/sc-projects/python-topic-model
Submitted job 28514701 with runs 1-6. See how it goes with `sc-starter status`.
```

The first line appears only when files were uploaded. The number in the
second line is the job ID that Slurm gave the job.

Before it submits anything, sc-starter checks `runs.txt`. It stops and
names the line if a line is empty, starts with `#` or ends with `\`.
It also stops if a line contains a hidden line break, an invisible
character that text copied from a web page or a word processor can
contain. Delete the line and type it again to remove it. Finally,
sc-starter stops if a setup job from the same folder has not finished
yet:

```text title="Output"
sc-starter: setup.slurm (job 28404223) has not finished yet. Submit job.slurm once `sc-starter status` shows it COMPLETED.
```

## status

```text title="Usage"
sc-starter status [JOB_ID]
```

Shows each run of the last job you started from this folder. With a job
ID, it shows that job instead.

```text title="Output"
Job 28514701: 6 COMPLETED

run  state      exit  node  elapsed   command
1    COMPLETED  0:0   t010  00:00:53  python run.py 5
2    COMPLETED  0:0   t010  00:00:54  python run.py 10
3    COMPLETED  0:0   t010  00:01:02  python run.py 15
4    COMPLETED  0:0   t010  00:01:04  python run.py 20
5    COMPLETED  0:0   t010  00:01:07  python run.py 25
6    COMPLETED  0:0   t010  00:01:13  python run.py 30
```

The columns show the run number, its state, the exit code of its last
command, the node it ran on, how long it ran and its line of
`runs.txt`. An exit code of `0:0` means the command finished without an
error. These are the states you will see most often:

| State | Meaning |
|---|---|
| `PENDING (Priority)` | The run is waiting because other jobs are ahead of it. |
| `PENDING (Resources)` | The run is waiting until a node has the cores, memory or GPU it asked for. |
| `RUNNING` | The run is running on the node shown. |
| `COMPLETED` | The run has finished without an error. |
| `FAILED` | The run ended with an error. `sc-starter log` shows the message. |
| `TIMEOUT` | Slurm stopped the run because it reached its time limit, set by `--time` in `job.slurm`. |
| `OUT_OF_MEMORY` | Slurm stopped the run because it used more memory than it asked for with `--mem`. |
| `CANCELLED` | Someone stopped the run with `scancel`, either you or an administrator. |

If some runs did not complete, sc-starter writes their numbers to
`failed.txt` and tells you. If all runs completed, it removes an old
`failed.txt`. Right after you submit a job, Slurm may need a few seconds
before it lists it:

```text title="Output"
Slurm does not list job 28514701. Right after submitting, wait a few seconds and try again.
```

## log

```text title="Usage"
sc-starter log [RUN] [--job JOB_ID]
```

Shows the output file of a run of the last job. This is everything the
run printed, including error messages.

| You type | What it shows |
|---|---|
| `sc-starter log 3` | the output of run 3 |
| `sc-starter log` | the output of a job without `runs.txt`, such as the setup job |
| `sc-starter log --job 28514701 3` | the output of run 3 of an earlier job |

```text title="Output"
Run 3 on t010: python run.py 15
K = 15 done in 1.0 minutes
```

sc-starter finds the output files by their names. The job scripts in this
guide name them with `#SBATCH --output=%x-%A_%a.out` for jobs with
`runs.txt` and `#SBATCH --output=%x-%j.out` for jobs without. If you use
your own job script, give it the same line. Slurm creates the file when
the run starts, so a run that is still waiting has none yet.

## pull

```text title="Usage"
sc-starter pull
```

Copies the folder `results` and all output files from the project's copy
on the cluster into your project folder. Files with the same name are
replaced. Nothing else in your folder changes.

```text title="Output"
Pulled 19 files (0.0 MB) into this folder.
```

If some runs are still writing, sc-starter brings back what is there and
adds: `Some files were still being written and may be incomplete. Pull
again when the runs are done.`

## push

```text title="Usage"
sc-starter push
```

Uploads what is new or changed in the project, without starting a job.
`sc-starter submit` does this by itself, so you need `push` only when you
want the files on the cluster without running anything.

```text title="Output"
Uploaded 1 file (0.0 MB) to sc-export:~/sc-projects/python-topic-model; 9 files unchanged
```

If nothing has changed:

```text title="Output"
Nothing to upload: sc-export:~/sc-projects/python-topic-model is up to date (10 files).
```

In these cases sc-starter stops without uploading anything:

| The message begins with | The reason |
|---|---|
| `This folder has no job script (*.slurm)` | The terminal is not in a project folder. Move there with `cd`. |
| `The folder name … cannot be used on the cluster` | The folder name contains characters other than letters, digits, `.`, `_` and `-`. Rename the folder. |
| `The cluster has a newer copy` | A file has changed on the cluster since the last upload. [Troubleshooting](../reference/troubleshooting.md#the-cluster-has-a-newer-copy) explains what to do. |
| `Cannot read …` | Your computer does not allow sc-starter to read the file or folder named in the message. Check that it is not open in another program and that your user account may read it. |

## Stopping a job

sc-starter has no command to stop a job. Use Slurm's command `scancel`
with the job ID instead:

```bash title="Your computer"
ssh sc-login scancel 28514701
```

This stops all runs of the job, those still waiting and those running.
`sc-starter status` then shows them as `CANCELLED`. Files that the runs
have already written stay on the cluster.

## The notes sc-starter keeps

When you submit a job, sc-starter saves a note about it in the hidden
folder `.sc-starter` in your project. The note holds the job ID, the time,
the run numbers and copies of `job.slurm` and `runs.txt` as they were at
that moment. `status` and `log` use these notes to find your last job and
the command of each run. The folder stays on your computer. If you use
Git, Git ignores this folder.

## Installing, updating and removing sc-starter

| Command | What it does |
|---|---|
| `uv tool install https://github.com/juhehehe/sc-starter/archive/refs/heads/main.zip` | installs sc-starter |
| `uv tool install --reinstall https://github.com/juhehehe/sc-starter/archive/refs/heads/main.zip` | updates it to the newest version |
| `uv tool uninstall sc-starter` | removes it |
