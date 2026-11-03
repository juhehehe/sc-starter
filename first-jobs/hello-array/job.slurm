#!/bin/bash
# Many runs of one job script: one run for each line of runs.txt.

#SBATCH --job-name=hello-array
#SBATCH --partition=cpu-xeonv3
#SBATCH --cpus-per-task=1
#SBATCH --mem=1G
#SBATCH --time=00:05:00
#SBATCH --output=%x-%A_%a.out

run=$(sed -n "${SLURM_ARRAY_TASK_ID}p" runs.txt)
[ -n "$run" ] || { echo "runs.txt has no line $SLURM_ARRAY_TASK_ID"; exit 1; }
echo "Run $SLURM_ARRAY_TASK_ID on $(hostname -s): $run"
bash -c "$run"
