#!/bin/bash
# One run per line of runs.txt; run N is line N, here one number of topics.
# Submit from your computer with `sc-starter submit`, after running
# `sc-starter submit setup.slurm` once.

#SBATCH --job-name=r-topic-model  # name in the queue and in the output files
#SBATCH --partition=cpu-xeonv3    # standard CPU partition; sinfo -s lists them all
#SBATCH --cpus-per-task=1         # stm uses one core
#SBATCH --mem=2G                  # 2 GB of memory per run
#SBATCH --time=00:10:00           # Slurm stops a run after 10 minutes
#SBATCH --output=%x-%A_%a.out     # job name, job ID, run number
#SBATCH --mail-type=END,FAIL      # email when the whole array has ended or failed

# The same R that setup.slurm installed the packages for.
module load R/4.5.2-gfbf-2025b
# As in the SC documentation; avoids locale warnings from R.
export LC_ALL=C.UTF-8

# This run's line of runs.txt, for example "Rscript run.R 10". Rscript
# without --vanilla, so that it reads .Rprofile and uses the project's
# packages from renv/library.
run=$(sed -n "${SLURM_ARRAY_TASK_ID}p" runs.txt)
# No such line, as when runs.txt got shorter: end the run as FAILED.
[ -n "$run" ] || { echo "runs.txt has no line $SLURM_ARRAY_TASK_ID"; exit 1; }
echo "Run $SLURM_ARRAY_TASK_ID on $(hostname -s): $run"
bash -c "$run"
