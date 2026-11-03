# Your first job

This page goes through a first job by hand: you write a small job script
line by line, copy it to the cluster, submit it, follow it and copy what
it printed back to your computer.

## Writing a job script

Create a folder called `first-jobs` on your computer. In it, create a file
called `hello.slurm` in a code editor. If you do not have one yet,
[VS Code](https://code.visualstudio.com/) is free for Linux, macOS and
Windows. Add the three parts
below one after another, in this order.

On Windows, set the editor to Unix line endings before you save. In VS
Code, click CRLF in the bar at the bottom of the window and choose LF.
Slurm refuses job scripts with the line endings of Windows.

### The first lines

```bash title="hello.slurm"
#!/bin/bash
# A first job: on which node does it run, and with how many cores?
```

The first line says that the commands in this file are for *bash*, the
program that reads and runs commands on Linux. The cluster runs Linux, so
every job script is a bash script, even if your own computer runs
Windows. Lines that start with `#` are comments.

### What the job asks for

```bash title="hello.slurm"
#SBATCH --job-name=hello
#SBATCH --partition=cpu-xeonv3
#SBATCH --cpus-per-task=1
#SBATCH --mem=1G
#SBATCH --time=00:05:00
#SBATCH --output=%x-%j.out
#SBATCH --mail-type=END,FAIL
```

Lines that start with `#SBATCH` are instructions for Slurm. For bash they
are comments, because they start with `#`. Slurm reads them only until
the first command of the script, so they come right after the first
lines. Each one sets one thing:

| Line | What it sets |
|---|---|
| `--job-name=hello` | the name of the job in the queue and in the name of its output file |
| `--partition=cpu-xeonv3` | the partition the job runs on |
| `--cpus-per-task=1` | the number of cores |
| `--mem=1G` | the memory: `1G` is 1 GB, and `500M` would be 500 MB |
| `--time=00:05:00` | the time limit, in hours, minutes and seconds; `1-12:00:00` is a day and a half, and 2 days is the most |
| `--output=%x-%j.out` | the *output file*, which gets everything the job prints; Slurm replaces `%x` with the job name and `%j` with the *job ID*, the number that Slurm gives each job |
| `--mail-type=END,FAIL` | an email to your university address when the job has ended or failed; you can leave this line out |

### What the job does

```bash title="hello.slurm"
echo "Job:   $SLURM_JOB_ID"
echo "Node:  $(hostname)"
echo "CPUs:  $SLURM_CPUS_PER_TASK"
echo "Time:  $(date)"
```

After the `#SBATCH` lines come the commands, written as you would type
them in a terminal. `echo` prints a line of text. Slurm gives every job a
few *environment variables*, named values that a command can read with
`$`. `SLURM_JOB_ID` holds the number of the job, and
`SLURM_CPUS_PER_TASK` the number of cores it got. `$(hostname)` runs the
command `hostname` and puts its answer, the name of the node, into the
line. `$(date)` does the same with the date and time.

In your own job scripts, this is where your script starts, for example
with `python run.py` or `Rscript run.R`.

**Check:** save the file and show it in the terminal, in the folder
`first-jobs`, with `cat hello.slurm`. It shows the three parts, starting with
`#!/bin/bash`. The finished file is also in this repository, as
[first-jobs/hello.slurm](../../first-jobs/hello.slurm).

## Submitting the job

The job script has to be on the cluster before Slurm can run it. On your
computer, open a terminal in the folder that contains `first-jobs`. Copy
the folder to the cluster and log in:

```bash title="Your computer"
scp -r first-jobs sc-export:
ssh sc-login
```

*scp* copies files over SSH, through the export node. `-r` copies a
folder with everything in it, and the colon at the end means "into my
home directory on the cluster".
[Copying files to and from the cluster](../project/copying-files.md) explains more
ways to copy.

**Check:** on the cluster, `ls first-jobs` shows `hello.slurm`.

Then, on the cluster, move into the folder and hand the job script to
Slurm with `sbatch`:

```bash title="Cluster"
cd first-jobs
sbatch hello.slurm
```

```text title="Output"
Submitted batch job 28412452
```

The number is the job ID of your job.

??? fix "If sbatch refuses the job"
    - `Batch script contains DOS line breaks`: the file has the line
      endings of Windows. Change them to LF in your editor, as described
      above, copy the folder again and submit again.
    - `invalid partition specified`: the name after `--partition` has a
      typo.
    - `Requested time limit is invalid`: the time limit is longer than the
      partition allows.

    [Troubleshooting](../reference/troubleshooting.md#batch-job-submission-failed)
    explains these messages in more detail.

## Following the job

`squeue` lists your jobs that are waiting or running:

```bash title="Cluster"
squeue --me
```

```text title="Output"
             JOBID PARTITION     NAME     USER ST       TIME  NODES NODELIST(REASON)
          28412452 cpu-xeonv    hello      you  R       0:02      1 t002
```

Slurm shortens names that are longer than their column, such as
`cpu-xeonv3`. The column `ST` shows the state of the job. `PD` means pending, and the
last column then says why the job waits. `(Priority)` means that other
jobs are ahead of it, and `(Resources)` that no node has room yet. `R`
means running, and the last column then names the node. When a job has
ended, it disappears from this list. The job `hello` ends within seconds,
so the list may already be empty.

`sacct` also shows jobs that have ended, with their final state:

```bash title="Cluster"
sacct -X -j 28412452
```

`-X` leaves out details that you rarely need, and `-j` names the job. The
column `State` shows one of these states:

| State | What it means |
|---|---|
| `PENDING` | the job waits in the queue |
| `RUNNING` | the job runs on a compute node |
| `COMPLETED` | the job has finished without an error |
| `FAILED` | the job script ended with an error, usually because its last command failed |
| `TIMEOUT` | Slurm stopped the job at its time limit |
| `OUT_OF_MEMORY` | Slurm stopped the job because it needed more memory than it asked for |
| `CANCELLED` | someone stopped the job with `scancel` |

To stop a job of yours, type `scancel` and its job ID, such as
`scancel 28412452`.

**Check:** the job has written its output file, which you can show with
`cat`. Its name comes from the job name and the job ID:

```bash title="Cluster"
cat hello-28412452.out
```

```text title="Output"
Job:   28412452
Node:  t002.sc.intern.uni-leipzig.de
CPUs:  1
Time:  Tue Oct 20 04:10:36 PM CEST 2026
```

Your job ID, node and time differ. The node is a compute node, such as
`t002`, not the login node. Slurm found a node with room and gave your
job the one core it asked for. Type `exit` to leave the cluster.

## Bringing the output back

The output file is now on the cluster, in the folder `first-jobs`. Copy
it to your computer with `scp`. To copy from the cluster to your
computer, swap the two places. On your computer, in the folder that
contains `first-jobs`, with the job ID of your job:

```bash title="Your computer"
scp sc-export:first-jobs/hello-28412452.out first-jobs/
```

**Check:** on your computer, `cat first-jobs/hello-28412452.out` shows
the same four lines as on the cluster.

Leave the folder `first-jobs` on the cluster. The next pages add more
jobs to it.

## Further reading

- [Scheduler fundamentals](https://hpc-carpentry.github.io/hpc-intro/13-scheduler.html),
  a workshop lesson by HPC Carpentry on submitting and following jobs.
- [Quick start user guide](https://slurm.schedmd.com/quickstart.html) in
  the Slurm documentation.
