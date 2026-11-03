# First jobs with sc-starter

This page runs the first jobs of the Slurm section again, now with
sc-starter, and shows which commands it types for you. It is a first try.
[Working with sc-starter](working-with-sc-starter.md) then explains each
command in the order of a project.

You need the folder `first-jobs` from [Your first job](../slurm/first-job.md) and
the pages after it, and sc-starter, as
[Install sc-starter](install.md) describes. You type every command on
this page on your computer, in a terminal in the folder `first-jobs`.

## The first job

Submit `hello.slurm`:

```bash title="Your computer"
sc-starter submit hello.slurm
```

```text title="Output"
Uploaded 6 files (0.0 MB) to sc-export:~/sc-projects/first-jobs
Submitted job 28412452. See how it goes with `sc-starter status`.
```

sc-starter copied the folder into `sc-projects/first-jobs` in your home
directory on the cluster, logged in and submitted the job. By hand, these
were `scp -r first-jobs sc-export:`, then `ssh sc-login`, `cd first-jobs`
and `sbatch hello.slurm`. The number is the job ID, as with `sbatch`.

Now see how the job is doing:

```bash title="Your computer"
sc-starter status
```

```text title="Output"
Job 28412452: 1 COMPLETED

run  state      exit  node  elapsed
-    COMPLETED  0:0   t002  00:00:00
```

While the job waits or runs, the state is `PENDING` or `RUNNING`. Type the
command again after a few seconds. By hand, this was `squeue --me` and
`sacct -X -j` on the cluster.

**Check:** `sc-starter log` shows what the job printed:

```text title="Output"
Job:   28412452
Node:  t002.sc.intern.uni-leipzig.de
CPUs:  1
Time:  Tue Oct 20 04:10:36 PM CEST 2026
```

By hand, this was `cat` on the cluster. To bring the output file into the
folder on your computer, as `scp` did by hand:

```bash title="Your computer"
sc-starter pull
```

```text title="Output"
Pulled 1 file (0.0 MB) into this folder.
```

## R and Python

```bash title="Your computer"
sc-starter submit hello-r.slurm
sc-starter status
```

This time the output of `submit` has no line `Uploaded`, because nothing
in the folder has changed since the last job.

**Check:** when the state is `COMPLETED`, `sc-starter log` prints:

```text title="Output"
R version 4.5.2 (2025-10-31) on t002.sc.intern.uni-leipzig.de
```

Then do the same with `hello-python.slurm`.

**Check:** `sc-starter log` prints:

```text title="Output"
Python 3.12.3 on t002.sc.intern.uni-leipzig.de
```

## A job array

The job array is in a folder of its own, `hello-array`. sc-starter treats
it as a project of its own, with its own copy on the cluster. Go there and
submit it:

```bash title="Your computer"
cd hello-array
sc-starter submit
```

```text title="Output"
Uploaded 2 files (0.0 MB) to sc-export:~/sc-projects/hello-array
Submitted job 28514701 with runs 1-3. See how it goes with `sc-starter status`.
```

Without a name, `sc-starter submit` submits `job.slurm`, with one run for
each line of `runs.txt`. It counts the lines itself. By hand, this was
`sbatch --array=1-3 job.slurm`.

`sc-starter status` lists each run with its line of `runs.txt`:

```text title="Output"
Job 28514701: 3 COMPLETED

run  state      exit  node  elapsed   command
1    COMPLETED  0:0   t002  00:00:01  echo "A model with 5 topics"
2    COMPLETED  0:0   t002  00:00:01  echo "A model with 10 topics"
3    COMPLETED  0:0   t002  00:00:01  echo "A model with 20 topics"
```

**Check:** `sc-starter log 2` shows what run 2 printed:

```text title="Output"
Run 2 on t002: echo "A model with 10 topics"
A model with 10 topics
```

Go back to the folder `first-jobs` with `cd ..`.

## A GPU

```bash title="Your computer"
sc-starter submit hello-gpu.slurm
sc-starter status
```

GPUs are in demand. The job may wait for a while as
`PENDING (Priority)`, because other jobs are ahead of it, or
`PENDING (Resources)`, because no GPU is free; both are normal.

**Check:** when the state is `COMPLETED`, `sc-starter log` prints:

```text title="Output"
name, driver_version, memory.total [MiB]
NVIDIA A30, 580.178.04, 24576 MiB
Node: paula11.sc.intern.uni-leipzig.de
```

## What sc-starter did for you

| Step | By hand | With sc-starter |
|---|---|---|
| copy the folder to the cluster | `scp -r first-jobs sc-export:` | `sc-starter submit`, which copies only what is new or changed |
| submit a job | `ssh sc-login`, `cd first-jobs`, `sbatch hello.slurm` | `sc-starter submit hello.slurm` |
| submit a job array | `sbatch --array=1-3 job.slurm` | `sc-starter submit`, with one run for each line of `runs.txt` |
| follow the job | `squeue --me`, `sacct -X -j 28412452` | `sc-starter status` |
| read what it printed | `cat hello-28412452.out` | `sc-starter log` |
| bring the output back | `scp sc-export:first-jobs/hello-28412452.out first-jobs/` | `sc-starter pull` |

You still write the job scripts yourself, as on the pages of the Slurm
section.

## Cleaning up

sc-starter keeps its copies in the folder `sc-projects` in your home
directory on the cluster. To remove the two of this page:

```bash title="Your computer"
ssh sc-export rm -r sc-projects/first-jobs sc-projects/hello-array
```
