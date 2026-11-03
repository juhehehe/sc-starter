#!/bin/bash
# One long simulation in pieces. One job, so there is no runs.txt. Submit
# from your computer with `sc-starter submit`; when the job stops at its time
# limit, submit it again, until `sc-starter status` shows COMPLETED.
# Only the standard library of Python, so there is no setup.slurm.

#SBATCH --job-name=python-long-run  # name in the queue and in the output files
#SBATCH --partition=cpu-xeonv3      # standard CPU partition; sinfo -s lists them all
#SBATCH --cpus-per-task=1           # the simulation uses one core
#SBATCH --mem=1G                    # 1 GB of memory
#SBATCH --time=00:02:00             # on purpose shorter than the simulation needs
#SBATCH --output=%x-%j.out          # job name and job ID, one file per job
#SBATCH --dependency=singleton      # wait while another job of this name runs: one save, one job

# Python from the cluster's module system.
module load Python/3.12.3-GCCcore-13.3.0

python run.py
