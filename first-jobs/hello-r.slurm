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
