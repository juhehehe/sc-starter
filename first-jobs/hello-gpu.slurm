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
