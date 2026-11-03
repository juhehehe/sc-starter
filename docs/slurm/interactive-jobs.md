# Interactive jobs

This page shows how to get a terminal on a compute node, to try something
out before you write a job script for it.

Everything you type on the login node runs there, next to the work of
everyone else who is logged in. So the login node is no place to try out
a script, not even for a minute. An *interactive job* books cores and
memory on a compute node, as a job script does, and gives you a terminal
there. What you type then runs on the compute node, until you leave it.

## Starting an interactive job

On the cluster, ask Slurm for one core, 1 GB of memory and 30 minutes,
with a terminal:

```bash title="Cluster"
srun --partition=cpu-xeonv3 --cpus-per-task=1 --mem=1G --time=00:30:00 --pty bash
```

`srun` starts a job and runs a command in it, here `bash`. `--pty`
connects it to your terminal. The other options are those of the
`#SBATCH` lines in
[Your first job](first-job.md#what-the-job-asks-for). If no node has room
yet, `srun` waits until one does.

**Check:** `hostname` now prints the name of a compute node, such as
`t002.sc.intern.uni-leipzig.de`, and not `login01`.

## Trying things out

In this terminal you work as on the login node, but with the core and
the memory that you asked for. For example, switch on R and start it:

```bash title="Cluster"
module load R/4.5.2-gfbf-2025b
R
```

R starts and waits for your commands. `q()` leaves it again.

An interactive job ends when you leave it, when it reaches its time
limit, or when the connection to the cluster breaks. So use it for tests
of a few minutes, and a job script for everything that runs longer.

## Leaving the interactive job

Type `exit`. Slurm ends the job and frees its core for others.

**Check:** `hostname` prints `login01.sc.intern.uni-leipzig.de` again.

## Further reading

- [Workload Manager Slurm](https://www.sc.uni-leipzig.de/05_Instructions/Slurm/)
  in the SC documentation, with a section on interactive jobs.
- [Scheduler fundamentals](https://hpc-carpentry.github.io/hpc-intro/13-scheduler.html),
  a workshop lesson by HPC Carpentry, which ends with interactive jobs.
- [srun](https://slurm.schedmd.com/srun.html) in the Slurm documentation.
