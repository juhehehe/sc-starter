---
# The website shows the first paragraph of each entry as a tooltip
# wherever the term appears, except for these words, which the text also
# uses in their everyday sense (to run a command).
no_tooltip: [Run]
# Names keep their capital letter inside a sentence; the other terms are
# written in small letters there.
names: [Git, Slurm]
---

# Glossary

The technical words used in this guide.

## Cluster

A group of computers that work together and are shared by many people.
In this guide, the cluster is the Scientific Computing (SC) cluster of
Leipzig University.

A cluster is useful when your own computer is too slow, has too little
memory, or when you want to run the same analysis many times.

Read more: [How your computer reaches the cluster](../basics/setup.md#how-your-computer-reaches-the-cluster) ·
[Why use a cluster?](https://hpc-carpentry.github.io/hpc-intro/10-hpc-intro.html)
(HPC Carpentry)

## Compute node

One of the computers of the cluster that run jobs. Slurm decides which
compute node runs your job, and in this guide you do not log in to one
yourself.

The cluster has many compute nodes of different kinds. Most have only
processors, some also have GPUs. Groups of compute nodes of the
same kind are called partitions.

Read more: [Partitions](cluster-at-a-glance.md#partitions) on the page
"The cluster at a glance"

## Core

One processing unit of a computer's processor. A processor with 16
cores can work on 16 things at the same time.

In a job script, `--cpus-per-task` sets how many cores each run gets.
More cores only help if your program uses them, and many programs use
only one unless you tell them otherwise. Your script can read the number
of cores it was given from the environment variable
`SLURM_CPUS_PER_TASK`.

Read more: [Using resources effectively](https://hpc-carpentry.github.io/hpc-intro/18-resources.html)
(HPC Carpentry)

## Environment

The packages that a project installs for itself, stored inside the
project folder. For Python with uv this is the hidden folder `.venv`, for
R with renv it is `renv/library`.

Because each project has its own environment, two projects can use
different versions of the same package without getting in each other's
way. On the cluster, the setup job builds the environment from the lock
file, so it holds the same versions as on your computer.

Read more: [Packages: uv and renv](../project/packages.md)

## Environment variable

A named value that a program can read while it runs. Slurm sets several
environment variables for every run.

The two you will meet most often are `SLURM_ARRAY_TASK_ID`, the number of
the run, and `SLURM_CPUS_PER_TASK`, the number of cores the run was
given. In Python you read them with `os.environ`, in R with
`Sys.getenv()`.

Read more: [Environment variables](https://hpc-carpentry.github.io/hpc-intro/14-environment-variables.html)
(HPC Carpentry) · [Cheat sheet](cheat-sheet.md)

## Exit code

A number with which a program reports whether it finished without an
error. `0` means no error, any other number means that something went
wrong.

`sc-starter status` shows the exit code of each run in the column `exit`,
for example `0:0`. The first number is the exit code of the run's last
command. The second is the number of the signal that stopped the run, if
any, and is usually 0.

Read more: [status](../sc-starter/commands.md#status) in the command reference

## Export node

The server of the cluster through which files are copied to and from
it. Its address is `export01.sc.uni-leipzig.de`, and this guide calls it
`sc-export`.

sc-starter uses the export node to upload your project and to bring the
results back. The export node and the login node see the same home
directory.

Read more: [Write the SSH settings](../basics/setup.md#5-write-the-ssh-settings)

## Fingerprint

A short code that identifies a server, such as
`SHA256:3saqgn+bVpG3PyG7mtwM2nPQY0NfK9auNCxLCWb85wQ`.

The first time you connect to a server, SSH shows you its fingerprint.
You compare it with the fingerprint that SC publishes, to be sure you are
connected to the real cluster. SSH remembers the fingerprint and warns you
if it ever changes.

Read more: [Log in for the first time](../basics/setup.md#6-log-in-for-the-first-time) ·
[All fingerprints](cluster-at-a-glance.md#machines)

## Git

A program that keeps track of the versions of your files, so that you can
see what changed and go back to an earlier version.

You do not need Git for this guide. If you use it, sc-starter leaves the
folder `.git`, where Git keeps the history, on your computer, and Git
ignores sc-starter's notes in `.sc-starter`.

Read more: [Git: your code on your computer and on the cluster](../project/git.md) ·
[Version control with Git](https://swcarpentry.github.io/git-novice/)
(Software Carpentry)

## GPU

A graphics processing unit, or graphics card. GPUs can do many simple
calculations at the same time, which makes them much faster than
processors for training and using language models.

Some partitions of the cluster have GPUs. A job asks for one with two
`#SBATCH` lines, for example `--partition=gpu-a30` and `--gpus=a30:1`.
Only ask for a GPU if your code uses it, because GPUs are in high demand
and a run that books one often waits longer.

Read more: [GPUs on the cluster](cluster-at-a-glance.md#gpus) ·
[Graphics processing unit](https://en.wikipedia.org/wiki/Graphics_processing_unit)
(Wikipedia)

## Home directory

Your own folder on the cluster, `/home/sc.uni-leipzig.de/YOUR_LOGIN`,
written `~` for short. Other users of the cluster cannot read it.

All nodes of the cluster see the same home directory. A file you
upload through the export node is therefore available to your jobs on the
compute nodes. sc-starter keeps each project in `~/sc-projects`. The home
directory holds 100 GB in total, and the command `sc_quotas` shows how
much of it you use.

Read more: [Keep your account tidy](keep-your-account-tidy.md)

## Job

A piece of work that you hand to Slurm. It consists of a job script and
one or more runs.

Slurm puts each job in its queue, gives it a job ID and starts it when
the computers it needs are free.

Read more: [Working on the cluster](../basics/working-on-the-cluster.md) ·
[Working with sc-starter](../sc-starter/working-with-sc-starter.md) ·
[Scheduler fundamentals](https://hpc-carpentry.github.io/hpc-intro/13-scheduler.html)
(HPC Carpentry)

## Job array

A job with many runs. Slurm runs the same job script once for each run
number, and each run reads its own line of `runs.txt`.

`sc-starter submit` creates a job array whenever the project has a
`runs.txt`. All runs share one job ID, and Slurm starts each of them as
soon as there is room for it.

Read more: [Starting the runs](../sc-starter/working-with-sc-starter.md#starting-the-runs-with-submit) ·
[Job array support](https://slurm.schedmd.com/job_array.html) (Slurm
documentation)

## Job ID

The number Slurm gives a job when you submit it, such as `28514701`.

`sc-starter submit` prints the job ID. `sc-starter status` and
`sc-starter log` use the job ID of your last job unless you give them
another one.

Read more: [Command reference](../sc-starter/commands.md)

## Job script

A text file that tells Slurm what a job needs and what it should do. In
this guide, job scripts end in `.slurm`.

The lines at the top that begin with `#SBATCH` ask for resources: time,
memory, cores and perhaps a GPU. The lines below them are the commands
that each run carries out. Each project has a job script called
`job.slurm`, and often a second one called `setup.slurm`.

Read more: [Write the job script](../../examples/python/python-topic-model/README.md#7-write-the-job-script)
in the Python topic model example · [sbatch](https://slurm.schedmd.com/sbatch.html)
(Slurm documentation)

## Lock file

A file that records the exact version of every package a project uses,
including the packages those packages depend on. For Python with uv it is
`uv.lock`, for R with renv it is `renv.lock`.

The lock file makes your environment reproducible. The setup job on the
cluster reads it and installs exactly the same versions as on your
computer, so your code runs with the same package versions in both
places.

Read more: [Packages: uv and renv](../project/packages.md) ·
[Locking and syncing](https://docs.astral.sh/uv/concepts/projects/sync/)
(uv documentation)

## Login node

The server of the cluster you log in to. Its address is
`login01.sc.uni-leipzig.de`, and this guide calls it `sc-login`.

Everyone who uses the cluster shares the login node. It is meant for
starting jobs and checking on them, and you must not run your
computations on it. sc-starter uses the login node to hand your jobs to
Slurm.

Read more: [Write the SSH settings](../basics/setup.md#5-write-the-ssh-settings) ·
[Working on a remote HPC system](https://hpc-carpentry.github.io/hpc-intro/12-cluster.html)
(HPC Carpentry)

## Module

Software that the cluster provides for all users. A job script loads it
with a line such as `module load R/4.5.2-gfbf-2025b` for R.

Modules let many versions of a program live on the cluster side by side.
`module spider R` on the login node lists all versions of R. The R
examples in this guide load R as a module. The Python examples with
packages install their own Python with uv instead.

Read more: [Modules](cluster-at-a-glance.md#modules) ·
[Accessing software via modules](https://hpc-carpentry.github.io/hpc-intro/15-modules.html)
(HPC Carpentry)

## Node

One computer of the cluster. The cluster has a login node, an export node
and many compute nodes.

## Output file

The file in which Slurm saves everything a run prints, including error
messages, such as `python-topic-model-28514701_3.out`.

Slurm creates the output file when the run starts. `sc-starter log`
shows it, and `sc-starter pull` copies all output files to your computer.
When a run fails, its output file is the first place to look.

Read more: [log](../sc-starter/commands.md#log) in the command reference

## Package

Code that other people have written for Python or R, which a project
installs and uses. Examples are tomotopy for topic models and ggplot2 for
figures.

In Python, you add packages with uv, in R with `install.packages()` and
renv. The packages go into the project's environment, and the lock file
records their versions.

Read more: [Packages: uv and renv](../project/packages.md) ·
[Glossary of Python packaging](https://packaging.python.org/en/latest/glossary/)

## Partition

A group of compute nodes of the same kind, such as `cpu-xeonv3` for
nodes with processors only or `gpu-a30` for nodes with A30 GPUs.

A job script names the partition its runs should go to, with
`#SBATCH --partition`. `sinfo -s` on the login node lists all partitions
with their state.

Read more: [Partitions](cluster-at-a-glance.md#partitions)

## Passphrase

The password of your SSH key file. Without it, a copy of the file is
useless to anyone else.

You choose the passphrase when you create the key. Use several words that
you do not use anywhere else, and keep them in a password manager. Thanks
to the SSH agent, you type it rarely.

Read more: [Turn on the SSH agent](../basics/setup.md#turn-on-the-ssh-agent)

## Path

The address of a file or folder, such as `data/survey.csv` or
`C:\Users\you\Documents\survey.csv`.

A path that starts inside the project folder, such as `data/survey.csv`,
is called relative, and it works wherever the project folder is. A full
path from your computer, such as one starting with `C:\` or `/home/you`,
does not exist on the cluster. Use relative paths in your code.

Read more: [Navigating files and directories](https://swcarpentry.github.io/shell-novice/02-filedir.html)
(Software Carpentry)

## Queue

The waiting list in which Slurm keeps all jobs that have not started
yet. A run in the queue has the state `PENDING`.

Slurm decides the order in which jobs leave the queue. A job usually
waits longer when the cluster is busy or when it asks for a lot, for
example a GPU or many cores. `squeue --me` on the login node shows your
jobs in the queue.

Read more: [Scheduling basics](https://hpc-wiki.info/hpc/Scheduling_Basics)
(HPC-Wiki)

## renv

An R package that gives an R project its own set of packages, like uv
does for Python.

`renv::init()` starts it in a project, and `renv::snapshot()` writes the
versions of the packages you use into `renv.lock`. On the cluster,
`renv::restore()` in the setup job installs the same versions.

Read more: [Packages: uv and renv](../project/packages.md) ·
[Introduction to renv](https://rstudio.github.io/renv/articles/renv.html)

## Run

One execution of a job's commands on a compute node. A job has one run,
or one run for each line of its run list.

Slurm treats each run like a small job of its own. The time, memory and
cores in the job script apply to each run separately.

## Run list

The file `runs.txt` of a project, with one complete command per line.
Line 3 is run 3.

A run list has no empty lines and no comments, so that the line numbers
are the run numbers. Each run of the job script reads its own line and
runs it.

Read more: [List the runs](../../examples/python/python-topic-model/README.md#6-list-the-runs)
in the Python topic model example

## SC portal

The website where you manage your account for the cluster,
[portal.sc.uni-leipzig.de](https://portal.sc.uni-leipzig.de). You log in
with your university login.

In the portal you apply for access to the cluster, upload your public
SSH key and ask SC support for help.

Read more: [Apply for access](../basics/setup.md#1-apply-for-access)
in the setup guide

## Seed

A starting number for random numbers. With the same seed, a program draws
the same random numbers every time.

Many models start from random guesses, for example topic models and
simulations. If the script sets a seed, a run can be repeated, and a run
on the cluster usually gives the same result as on your computer.

## Setup job

A job that installs a project's packages on the cluster, once, before
the first runs. Its job script is called `setup.slurm`.

Installing packages counts as computing, so it must not happen on the
login node. The setup job runs on a compute node instead, and builds the
project's environment from its lock file.

Read more: [Write the setup script](../../examples/python/python-topic-model/README.md#8-write-the-setup-script)
in the Python topic model example

## Shell

The program that reads the commands you type and carries them out. On the
cluster it is called bash, on Windows it is PowerShell.

The shell runs inside a terminal. After you type `ssh sc-login`, the
shell in your terminal is the one on the cluster, and your commands run
there.

Read more: [Working in the terminal](../basics/terminal.md) ·
[Introducing the shell](https://swcarpentry.github.io/shell-novice/01-intro.html)
(Software Carpentry)

## Slurm

The program that shares the cluster among its users. You hand it a job
script, it puts the job in a queue, and it starts the job on a compute
node when the computers it needs are free.

Many university clusters use Slurm, so much of what you learn here also
works elsewhere. Its main commands are `sbatch` to submit a job, `squeue`
to see waiting and running jobs, `sacct` to see finished jobs and
`scancel` to stop a job. sc-starter runs `sbatch`, `squeue` and `sacct`
for you. To stop a job, you use `scancel` yourself.

Read more: [Quick start user guide](https://slurm.schedmd.com/quickstart.html)
(Slurm documentation) · [Workload Manager Slurm](https://www.sc.uni-leipzig.de/05_Instructions/Slurm/)
(SC documentation)

## SSH

Secure Shell, a program that lets you type commands on another computer
over an encrypted connection. It comes with Linux, macOS and Windows.

You use SSH to log in to the cluster, with `ssh sc-login`. sc-starter
also uses SSH, to copy files and to talk to Slurm.

Read more: [How your computer reaches the cluster](../basics/setup.md#how-your-computer-reaches-the-cluster) ·
[Connecting securely to an HPC cluster](https://hpc-carpentry.github.io/hpc-intro/11-connecting.html)
(HPC Carpentry)

## SSH agent

A small program on your computer that keeps your SSH key unlocked, so that
you do not have to type the passphrase for every connection.

On Linux, you type the passphrase once after each restart. On macOS and
Windows, you type it only once on that computer.

Read more: [Turn on the SSH agent](../basics/setup.md#turn-on-the-ssh-agent)

## SSH key

A pair of files that lets you log in without a password: a public key,
which you give to the cluster, and a private key, which stays on your
computer.

The public key works like a lock and the private key like the key that
opens it. The cluster asks your computer to prove that it has the matching
private key, and your computer can prove this without sending the key.

Read more: [Create an SSH key](../basics/setup.md#3-create-an-ssh-key) ·
[SSH keys](https://docs.ycrc.yale.edu/clusters-at-yale/access/ssh/)
(Yale Center for Research Computing)

## Terminal

The window in which you type commands. On macOS and Linux the program is
called Terminal, on Windows you use PowerShell.

VS Code also has a terminal built in: choose Terminal › New Terminal, and
it opens in the folder you are working in. That is often the easiest way
to type commands in a project folder.

Read more: [Working in the terminal](../basics/terminal.md) ·
[Terminal basics](https://code.visualstudio.com/docs/terminal/basics)
(VS Code documentation)

## Time limit

The longest a run may take, set in the job script with `--time`, for
example `--time=00:20:00` for 20 minutes. Slurm stops the run when the
time is up.

A run that hits its time limit ends with the state `TIMEOUT`. On this
cluster, a run may take at most two days, and a run without `--time`
gets one hour. Shorter time limits usually mean shorter waits in the
queue.

Read more: [Limits](cluster-at-a-glance.md#limits) ·
[Runs longer than the time limit](../../examples/python/python-long-run/README.md)

## uv

A program that sets up Python projects. It installs the version of
Python a project needs, and the packages the project uses inside the
project folder.

The commands you use most are `uv add` to install a package,
`uv run` to run a script with the project's packages, and `uv sync` to
install everything listed in the lock file. You install uv on your
computer once, and the setup job installs it on the cluster.

Read more: [Packages: uv and renv](../project/packages.md) ·
[Getting started with uv](https://docs.astral.sh/uv/getting-started/)

## VPN

Virtual private network, an encrypted link between your computer and the
university. While it is connected, your computer counts as part of the
university network and can reach the cluster.

On campus you do not need the VPN. From home or while travelling, you
connect it before you use the cluster, with OpenConnect on Linux or the
Cisco Secure Client on macOS and Windows.

Read more: [Connect to the university network](../basics/setup.md#2-connect-to-the-university-network) ·
[VPN access](https://www.urz.uni-leipzig.de/servicedesk-und-hilfe/hilfe-zu-unseren-services/netz-und-zugang/hilfe-vpn-zugang-zum-uni-netz-vpn-webvpn)
(URZ)
