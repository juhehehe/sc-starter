#!/bin/bash
# Turn all questions into embeddings on one GPU, find similar ones, group
# them. One job, so there is no runs.txt. Submit from your computer with
# `sc-starter submit`, after running `sc-starter submit setup.slurm` once.

#SBATCH --job-name=python-embeddings  # name in the queue and in the output file
#SBATCH --partition=gpu-a30           # machines with A30 GPUs; sinfo -s lists them all
#SBATCH --gpus=a30:1                  # one GPU of type a30 (type:count)
#SBATCH --cpus-per-task=2             # the GPU embeds; two cores do the rest
#SBATCH --mem=4G                      # about twice what the script used on a computer
#SBATCH --time=00:10:00               # Slurm stops the job after 10 minutes
#SBATCH --output=%x-%j.out            # job name and job ID
#SBATCH --mail-type=END,FAIL          # email when the job has ended or failed

# uv, which setup.slurm installed for your account.
export PATH="$HOME/.local/bin:$PATH"

# Load the model from the cache that setup.slurm filled; never download
# during the job.
export HF_HUB_OFFLINE=1

# The project's Python and packages, which setup.slurm put into .venv.
# --no-sync uses them as they are and installs nothing.
uv run --no-sync python run.py
