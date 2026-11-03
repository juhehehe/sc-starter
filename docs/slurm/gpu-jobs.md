# Asking for a GPU

This page shows how a job asks for a GPU, with a small job that shows the
GPU it got.

A job that needs a GPU names a partition with GPUs and the number and
type of GPUs:

```bash title="Part of a job script"
#SBATCH --partition=gpu-a30
#SBATCH --gpus=a30:1
```

`--gpus=a30:1` books one GPU of the type A30. Many people want GPUs, so
such jobs often wait longer than others. Book a GPU only when your code
uses it, as programs for language models do. The code-along
[Text embeddings on a GPU](../../examples/python/python-embeddings/README.md)
shows a complete GPU job.

## A job with a GPU

In the folder `first-jobs` on your computer, create a file called
`hello-gpu.slurm`:

```bash title="hello-gpu.slurm"
#!/bin/bash
# A first job: does the job get a GPU, and which one?
# On the cluster, in this folder: sbatch hello-gpu.slurm; once the job has
# ended, cat hello-gpu-*.out shows what it printed.

#SBATCH --job-name=hello-gpu      # name shown in the queue (squeue --me)
#SBATCH --partition=gpu-a30       # machines with A30 GPUs; sinfo -s lists them all
#SBATCH --gpus=a30:1              # one GPU of type a30 (type:count)
#SBATCH --cpus-per-task=1         # one CPU core
#SBATCH --mem=1G                  # 1 GB of memory
#SBATCH --time=00:05:00           # Slurm stops the job after 5 minutes
#SBATCH --output=%x-%j.out        # output file; %x becomes the job name, %j the job ID

# Which GPU did the job get, with which driver and how much memory?
nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv
echo "Node: $(hostname)"
```

`nvidia-smi` comes with the driver of the GPU and reports on it.
`--query-gpu` names what it reports, here the type of the GPU, the
version of its driver and its memory, and `--format=csv` prints them as
one line, separated by commas. The finished file is also in this
repository, as [first-jobs/hello-gpu.slurm](../../first-jobs/hello-gpu.slurm).

Copy it to the cluster and submit it. On your computer, in the folder that
contains `first-jobs`:

```bash title="Your computer"
scp first-jobs/hello-gpu.slurm sc-export:first-jobs/
ssh sc-login
```

```bash title="Cluster"
cd first-jobs
sbatch hello-gpu.slurm
```

The job may show `PD` in `squeue --me` for a while, because other jobs
are ahead of it or no GPU is free.

**Check:** when the job is gone from the list, `cat hello-gpu-*.out`
shows:

```text title="Output"
name, driver_version, memory.total [MiB]
NVIDIA A30, 580.178.04, 24576 MiB
Node: paula11.sc.intern.uni-leipzig.de
```

The first two lines come from the GPU itself: its type, its driver and
its memory. Type `exit` to leave the cluster.

## Cleaning up

The jobs of this section leave the folder `first-jobs` in your home
directory on the cluster. To remove it:

```bash title="Your computer"
ssh sc-export rm -r first-jobs
```
