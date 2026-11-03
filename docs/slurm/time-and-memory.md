# Choosing time and memory

This page shows how to estimate how much time and memory a job needs, how
to check what it used, and what happens when it asks for too little.

## Estimating on your computer

You rarely know in advance how much time and memory a script needs.
Before you go to the cluster, run it once on your computer, with the
setting that will take longest, and watch how long it takes and how much
memory it uses. The task manager of your computer shows the memory: the
Activity Monitor on macOS, the Task Manager on Windows, and the System
Monitor on Linux. Write both numbers down.

Then start with one run on the cluster and generous values, about twice
what you measured. A job that has run once tells you how much it really
needs.

## Checking what a job used

When a job has finished, ask how much of what it booked it really used,
with `reportseff` and the job ID. For a job that booked 15 minutes, four
cores and 16 GB of memory:

```bash title="Cluster"
reportseff 28410356
```

```text title="Output"
     JobID    State       Elapsed  TimeEff   CPUEff   MemEff
  28410356  COMPLETED    00:00:46   5.1%     22.8%    14.5%
```

`TimeEff` is the share of the time limit that the job used, `CPUEff` the
share of its cores and `MemEff` the share of its memory. This job used
46 seconds of its 15 minutes, about one of its four cores and under 3 GB
of its memory.

## Trying it out

A small job shows what these numbers mean, and what Slurm does when a job
asks for too little. In the folder `first-jobs` on your computer, create a
file called `hello-limits.slurm`:

```bash title="hello-limits.slurm"
#!/bin/bash
# A first job: what happens when a job asks for too little memory or time?
# On the cluster, in this folder: sbatch hello-limits.slurm; then again
# with less memory or time, as docs/slurm/time-and-memory.md shows.

#SBATCH --job-name=hello-limits   # name shown in the queue (squeue --me)
#SBATCH --partition=cpu-xeonv3    # which group of machines; sinfo -s lists them all
#SBATCH --cpus-per-task=1         # one CPU core
#SBATCH --mem=200M                # 200 MB of memory
#SBATCH --time=00:02:00           # Slurm stops the job after 2 minutes
#SBATCH --output=%x-%j.out        # output file; %x becomes the job name, %j the job ID

module load Python/3.12.3-GCCcore-13.3.0

# Fill about 100 MB of memory and keep it for a minute and a half.
python -c 'import time; block = b"x" * 100_000_000; time.sleep(90); print("Done")'
```

The job fills about 100 MB of memory with the letter x, keeps it for a
minute and a half and then prints `Done`. It asks for 200 MB and two
minutes, so it has room to spare. It runs for more than a minute on
purpose: one minute is the shortest time limit, and the last test below
needs a job that runs past it. The finished file is also in this
repository, as [first-jobs/hello-limits.slurm](../../first-jobs/hello-limits.slurm).

Copy it to the cluster and submit it:

```bash title="Your computer"
scp first-jobs/hello-limits.slurm sc-export:first-jobs/
ssh sc-login
```

```bash title="Cluster"
cd first-jobs
sbatch hello-limits.slurm
```

**Check:** after about a minute and a half, `reportseff` with the job ID
shows that the job used about half of its memory and three quarters of
its time:

```text title="Output"
     JobID    State       Elapsed  TimeEff   CPUEff   MemEff
  28520101  COMPLETED    00:01:31  75.8%      0.1%    52.0%
```

`CPUEff` stays near zero, because the job mostly waits. A script that
calculates keeps its cores busy and shows close to 100%.

### Too little memory

Options that you give `sbatch` on the command line take the place of the
`#SBATCH` lines of the same name. So you can try other values without
changing the file. Submit the job again, this time with 50 MB of memory:

```bash title="Cluster"
sbatch --mem=50M hello-limits.slurm
```

**Check:** the job ends within seconds. `sacct -X -j` with its job ID
shows the state `OUT_OF_MEMORY`, and its output file ends with a message
from Slurm such as:

```text title="Output"
slurmstepd: error: Detected 1 oom_kill event in StepId=28520102.batch. Some of the step tasks have been OOM Killed.
```

### Too little time

Now give it one minute:

```bash title="Cluster"
sbatch --time=00:01:00 hello-limits.slurm
```

**Check:** after about a minute, `sacct -X -j` shows the state `TIMEOUT`,
and the output file ends with a message such as:

```text title="Output"
slurmstepd: error: *** JOB 28520103 ON t002 CANCELLED AT 2026-11-03T10:15:42 DUE TO TIME LIMIT ***
```

The job never printed `Done`, because Slurm stopped it before. Whatever a
job has not saved by then is lost.
[Runs longer than the time limit](../../examples/python/python-long-run/README.md)
shows how a job saves its work in time. Type `exit` to leave the cluster.

## Booking for the next runs

For the next runs, book about a quarter more than a run used, so that the
jobs start sooner and still have a margin. If the column `CPUEff` shows
much less than 100% with several cores, your code used fewer cores than it
booked, as
[Bring your own project](../sc-starter/bring-your-own-project.md#a-run-uses-the-cores-it-booked)
explains. [The cluster at a glance](../reference/cluster-at-a-glance.md) lists the most that a job
may ask for on each partition.
