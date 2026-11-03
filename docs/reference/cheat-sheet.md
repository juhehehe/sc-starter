# Cheat sheet

This page lists the commands of this guide. `JOB_ID` stands for the number of
a job, which `sc-starter submit` prints. `RUN` stands for the number of a
run, which is its line in `runs.txt`. `my-project` stands for the name of
your project folder.

## sc-starter

On your computer, in the project folder.

| Command | What it does |
|---|---|
| `sc-starter check` | tests the connection to the cluster and prints `Ready.` |
| `sc-starter submit setup.slurm` | uploads what changed and runs `setup.slurm` once, to install the packages |
| `sc-starter submit` | uploads what changed and runs `job.slurm` once for each line of `runs.txt` |
| `sc-starter submit --lines failed.txt` | starts only the runs whose numbers are in the file |
| `sc-starter status` | shows each run of the last job |
| `sc-starter log RUN` | shows what a run printed |
| `sc-starter log` | shows what a job without `runs.txt` printed, such as the setup job |
| `sc-starter pull` | brings back `results/` and the output files |
| `sc-starter push` | uploads what changed, without starting a job |
| `sc-starter status JOB_ID` | shows an earlier job |
| `sc-starter log --job JOB_ID RUN` | shows what a run of an earlier job printed |
| `ssh sc-login scancel JOB_ID` | stops a job with all its runs |
| `sc-starter --version` | shows the version of sc-starter |

Install, update and remove sc-starter on your computer:

| Command | What it does |
|---|---|
| `uv tool install https://github.com/juhehehe/sc-starter/archive/refs/heads/main.zip` | installs sc-starter |
| `uv tool install --reinstall https://github.com/juhehehe/sc-starter/archive/refs/heads/main.zip` | updates it to the newest version |
| `uv tool uninstall sc-starter` | removes it |

[Commands](../sc-starter/commands.md) describes every command and its messages.

## The terminal

| Command | What it does |
|---|---|
| `pwd` | shows the folder you are in |
| `ls` | lists the files and folders in it |
| `cd my-project` | moves into the folder `my-project`; `cd ..` moves up one folder |
| `mkdir my-project` | creates the folder `my-project` |
| `cat runs.txt` | shows the content of a file |

## SSH and copying files

On your computer.

| Command | What it does |
|---|---|
| `ssh sc-login` | logs you in to the cluster; `exit` leaves it |
| `ssh sc-login COMMAND` | runs one command on the cluster, such as `ssh sc-login sinfo -s` |
| `ssh-add -l` | lists the keys in the SSH agent |
| `ssh sc-export mkdir -p my-project` | creates a folder on the cluster, which scp needs before it copies into it |
| `scp FILE sc-export:my-project/` | copies a file to the cluster |
| `scp -r sc-export:my-project/results .` | copies a folder from the cluster into the folder you are in |
| `rsync -av --exclude .venv my-project sc-export:` | copies a folder to the cluster, only what changed, without `.venv`; not on Windows |

## Slurm

On the cluster, after `ssh sc-login`, or with `ssh sc-login` in front.

| Command | What it does |
|---|---|
| `sbatch job.slurm` | submits a job script |
| `sbatch --array=1-6 job.slurm` | submits it as a job array with runs 1 to 6 |
| `squeue --me` | lists your jobs that wait or run |
| `sacct -X -j JOB_ID` | shows how a job went, also after it ended |
| `scancel JOB_ID` | stops a job with all its runs |
| `reportseff JOB_ID` | shows how much of the booked time, cores and memory a job used |
| `sinfo -s` | lists the partitions; a star marks the standard one |
| `module spider R` | lists the versions of R; the same for `Python` |
| `sc_quotas` | shows how full your home directory is |

## The lines of a job script

| Line | What it sets |
|---|---|
| `#SBATCH --job-name=my-project` | the name in the queue and in the output files |
| `#SBATCH --partition=cpu-xeonv3` | the partition; `sinfo -s` lists them |
| `#SBATCH --cpus-per-task=1` | the cores of each run |
| `#SBATCH --mem=2G` | the memory of each run |
| `#SBATCH --time=00:20:00` | the time limit of each run, here 20 minutes |
| `#SBATCH --gpus=a30:1` | one GPU of the type A30, together with `--partition=gpu-a30` |
| `#SBATCH --output=%x-%A_%a.out` | the output file of each run: job name, job ID and run number |
| `#SBATCH --output=%x-%j.out` | the output file of a job without `runs.txt`: job name and job ID |
| `#SBATCH --mail-type=END,FAIL` | an email when the job has ended or failed |

`sc-starter log` finds output files only under these two names.
`sc-starter submit` adds `--array=1-N` for the N lines of `runs.txt`.
Inside a run, Slurm sets these variables:

| Variable | What it holds |
|---|---|
| `SLURM_ARRAY_TASK_ID` | the number of the run |
| `SLURM_CPUS_PER_TASK` | the cores booked for each run |
| `SLURM_ARRAY_JOB_ID` | the job ID, in a job with `runs.txt` |
| `SLURM_JOB_ID` | the job ID in a job without `runs.txt`; in a job array, each run's own number |

[Your first job](../slurm/first-job.md) explains every line, and
[Bring your own project](../sc-starter/bring-your-own-project.md#7-write-the-job-scripts) has job
scripts to copy.

## Packages

On your computer, in the project folder.

| Python with uv | R with renv | What it does |
|---|---|---|
| `uv init --bare --python 3.12` | `renv::init()` | sets up the project's own packages |
| `uv add PACKAGE` | `install.packages("PACKAGE")`, then `renv::snapshot()` | installs a package and records its version |
| `uv sync --locked` | `renv::restore()` | installs exactly the recorded versions |
| `uv run run.py` | `Rscript run.R` | runs a script with the project's packages |

[Packages: uv and renv](../project/packages.md) explains both.

## Git

| Command | Where | What it does |
|---|---|---|
| `git add .` | your computer | marks all changed files for the next version |
| `git commit -m "MESSAGE"` | your computer | saves a version with a short message |
| `git push` | your computer | sends the new versions to GitHub |
| `git clone ADDRESS` | cluster | downloads the repository from GitHub, once |
| `git pull` | cluster | fetches the new versions since then |

[Git: your code on your computer and on the cluster](../project/git.md) explains
how to start.

## Cleaning up

On your computer.

| Command | What it does |
|---|---|
| `ssh sc-export rm -rI sc-projects/my-project` | removes a project from the cluster, after asking once |
| `ssh sc-export .local/bin/uv cache prune` | removes what uv no longer needs from its store |

[Keep your account tidy](keep-your-account-tidy.md) shows what else takes up space.

## Further reading

About the cluster in Leipzig:

- [The cluster at a glance](cluster-at-a-glance.md): computers, partitions, GPUs,
  limits and modules on one page.
- The [SC documentation](https://www.sc.uni-leipzig.de): access,
  storage, partitions, and Jupyter and RStudio on the cluster.
- [Workload Manager Slurm](https://www.sc.uni-leipzig.de/05_Instructions/Slurm/)
  in the SC documentation: job scripts, partitions, memory limits, and
  job arrays and GPU jobs, with examples for R.

Courses for beginners:

- [Using High-Performance Computing Systems](https://hpc-carpentry.github.io/hpc-intro/)
  by HPC Carpentry: what a cluster is, how to connect, and how Slurm
  works.
- [The Unix Shell](https://swcarpentry.github.io/shell-novice/) by
  Software Carpentry: the terminal from the start.
- [Cluster computing with R for social scientists](https://github.com/sodascience/workshop_ossc)
  by ODISSEI and SURF: parallel R and job arrays, with examples from the
  social sciences.

To look things up:

- [sbatch](https://slurm.schedmd.com/sbatch.html): every `#SBATCH`
  option.
- [Job arrays](https://slurm.schedmd.com/job_array.html): how Slurm runs
  one job script many times.
- [uv](https://docs.astral.sh/uv/) and
  [renv](https://rstudio.github.io/renv/articles/renv.html): the package
  managers.
- [Managing the cache of Hugging Face](https://huggingface.co/docs/huggingface_hub/guides/manage-cache):
  where downloaded models are kept and how to remove them.
- [reportseff](https://github.com/troycomi/reportseff): what the columns
  of `reportseff` mean.
