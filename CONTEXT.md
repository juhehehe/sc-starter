# sc-starter

Run Python and R projects as Slurm jobs on the SC cluster of Leipzig
University from your own computer: submit the project, follow its runs, pull
the results.

## Language

### Places

**Your computer**:
The computer of the user, laptop or desktop, where the project lives and
sc-starter runs.
_Avoid_: laptop, local machine, client

**Cluster**:
The SC machines of Leipzig University, reached over SSH from inside the
university network.
_Avoid_: HPC, server

**Login node**:
The cluster machine `sc-login`, which takes Slurm commands and never
computes.
_Avoid_: head node, login server

**Export node**:
The cluster machine `sc-export`, through which files go to and from the
cluster.
_Avoid_: transfer node, data node

**Compute node**:
A cluster machine on which Slurm runs the runs of a job.
_Avoid_: worker, node (alone)

**Partition**:
A group of compute nodes of one kind, named in the job script.
_Avoid_: queue

### Project

**Project**:
One folder on your computer with code, data, job scripts and, for many runs, a
run list. It is known by its folder name.
_Avoid_: repo, workspace

**Cluster folder**:
`~/sc-projects/<folder name>`, the copy of a project on the cluster.
_Avoid_: remote folder, target

**Job script**:
A `.slurm` file whose `#SBATCH` lines book resources and whose commands say
what to run.
_Avoid_: batch script, Slurm script

**Setup job**:
A job from `setup.slurm` that installs the packages of a project on the
cluster, once.
_Avoid_: install job

**Run list**:
`runs.txt`: one complete command per line, without comments or empty lines;
line N is run N.
_Avoid_: job file, task list

**Results**:
The files that runs write into `results/`, which pull brings back.
_Avoid_: output

**Output file**:
The `.out` file into which Slurm writes everything a run prints.
_Avoid_: log file, Slurm output

**Environment**:
The packages a project installs for itself, built on the cluster by its
setup job.
_Avoid_: venv, library (alone)

### Jobs and runs

**Job**:
One submission to Slurm, with one job ID. It has one run, or one per line
of the run list.
_Avoid_: array job, job for a single run

**Run**:
One execution of a job's commands on a compute node: one line of the run
list, or the only run of a job without one. Slurm treats each run as a job
of its own, so its limits on time, memory and cores apply per run.
_Avoid_: task, array task

**Job ID**:
The number Slurm gives a job when it is submitted, which submit prints.
_Avoid_: job number, array job ID

**Run number**:
The line number of a run in the run list the job was submitted with.
_Avoid_: task ID, array index, line

**Last job**:
The job submitted last from a project folder; status and log mean it when
no job is named.
_Avoid_: latest job, current job

**Job note**:
What sc-starter keeps on your computer about a submitted job: its ID, the time,
its job script and run numbers, and copies of the job script and run list.
_Avoid_: job record, job state

**Book**:
To ask Slurm for time, cores, memory or a GPU for each run, in the job
script.
_Avoid_: request, allocate, reserve

**State**:
What Slurm reports for a run, such as `PENDING`, `RUNNING`, `COMPLETED`,
`FAILED`, `TIMEOUT`, `OUT_OF_MEMORY` or `CANCELLED`.
_Avoid_: status (that is the command)

**Failed run**:
A run that ended in any state but `COMPLETED`.
_Avoid_: FAILED (that is one state among them)

**First jobs**:
The tiny jobs in `first-jobs/` that show the cluster runs your code: Slurm,
R, Python, a job array, the limits of memory and time, and a GPU.
_Avoid_: smoke tests, probes

### Commands

**Push**:
To upload what is new or changed in a project to its cluster folder,
without deleting anything there or overwriting a newer copy.
_Avoid_: sync, deploy

**Submit**:
To push a project and hand one of its job scripts to Slurm, which queues
it; its runs start when Slurm finds room.
_Avoid_: start, run (as a verb for submitting)

**Pull**:
To bring the results and the output files back into the project.
_Avoid_: download, fetch, sync
