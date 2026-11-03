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
