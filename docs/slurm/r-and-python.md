# R and Python in a job

This page shows how a job script uses R and Python, with a small job for
each that prints its version.

The compute nodes have R and Python as *modules*, software that the
cluster provides for everyone. A job script switches a module on with
`module load`. Name the full version, so that your job keeps the same R
when a newer one arrives. `module spider R` on the login node lists all
versions of R, and `module spider Python` all versions of Python.

## A job with R

In the folder `first-jobs` on your computer, create a file called
`hello-r.slurm`:

```bash title="hello-r.slurm"
#!/bin/bash
# A first job: does R run on a compute node?
# On the cluster, in this folder: sbatch hello-r.slurm; once the job has
# ended, cat hello-r-*.out shows what it printed.

#SBATCH --job-name=hello-r        # name shown in the queue (squeue --me)
#SBATCH --partition=cpu-xeonv3    # which group of machines; sinfo -s lists them all
#SBATCH --cpus-per-task=1         # one CPU core
#SBATCH --mem=1G                  # 1 GB of memory
#SBATCH --time=00:05:00           # Slurm stops the job after 5 minutes
#SBATCH --output=%x-%j.out        # output file; %x becomes the job name, %j the job ID

# R comes as a module; `module spider R` on the login node lists all versions.
# Name the full version, so the job keeps the same R when a newer one arrives.
module load R/4.5.2-gfbf-2025b
# As in the SC documentation; avoids locale warnings from R.
export LC_ALL=C.UTF-8

Rscript -e 'cat(R.version.string, "on", Sys.info()[["nodename"]], "\n")'
```

The `#SBATCH` lines ask for the same as in `hello.slurm`, and the
comment behind each one says what it sets. `module load` switches on R
in the version named. `export LC_ALL=C.UTF-8` sets the language settings
of the job, as the SC documentation does; without it, R warns about
them. `Rscript -e` runs the R code in the quotes after it, here one line
that prints the version of R and the name of the node. The finished file
is also in this repository, as
[first-jobs/hello-r.slurm](../../first-jobs/hello-r.slurm).

Copy the file into the folder `first-jobs` on the cluster and log in. On
your computer, in the folder that contains `first-jobs`:

```bash title="Your computer"
scp first-jobs/hello-r.slurm sc-export:first-jobs/
ssh sc-login
```

A single file needs no `-r`. Then, on the cluster, submit the R job:

```bash title="Cluster"
cd first-jobs
sbatch hello-r.slurm
```

`squeue --me` lists the job while it waits or runs. Once it is gone from
the list, show what it printed:

```bash title="Cluster"
cat hello-r-*.out
```

**Check:** it prints the version of R and the node, for example:

```text title="Output"
R version 4.5.2 (2025-10-31) on t002.sc.intern.uni-leipzig.de
```

Type `exit` to leave the cluster.

## A job with Python

Next to `hello-r.slurm`, create a file called `hello-python.slurm`:

```bash title="hello-python.slurm"
#!/bin/bash
# A first job: does Python run on a compute node?
# On the cluster, in this folder: sbatch hello-python.slurm; once the job
# has ended, cat hello-python-*.out shows what it printed.

#SBATCH --job-name=hello-python   # name shown in the queue (squeue --me)
#SBATCH --partition=cpu-xeonv3    # which group of machines; sinfo -s lists them all
#SBATCH --cpus-per-task=1         # one CPU core
#SBATCH --mem=1G                  # 1 GB of memory
#SBATCH --time=00:05:00           # Slurm stops the job after 5 minutes
#SBATCH --output=%x-%j.out        # output file; %x becomes the job name, %j the job ID

# Python comes as a module; `module spider Python` on the login node lists
# all versions. The examples with packages install their own Python with uv
# in a setup.slurm; this job needs nothing but Python itself.
module load Python/3.12.3-GCCcore-13.3.0

python -c 'import platform, sys; print("Python", sys.version.split()[0], "on", platform.node())'
```

`module load` switches on Python, and `python -c` runs the Python code in
the quotes after it. It prints the version of Python and the name of the
node. The finished file is also in this repository, as
[first-jobs/hello-python.slurm](../../first-jobs/hello-python.slurm).

Copy it to the cluster and submit it, as with the R job:

```bash title="Your computer"
scp first-jobs/hello-python.slurm sc-export:first-jobs/
ssh sc-login
```

```bash title="Cluster"
cd first-jobs
sbatch hello-python.slurm
```

**Check:** once the job is gone from `squeue --me`,
`cat hello-python-*.out` prints the version of Python and the node:

```text title="Output"
Python 3.12.3 on t002.sc.intern.uni-leipzig.de
```

Type `exit` to leave the cluster.

## Packages

Projects that use packages need them on the cluster in the same versions
as on your computer. A *setup job*, a job script of its own, installs them
once before the runs. [Packages: uv and renv](../project/packages.md) explains how.
