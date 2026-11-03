#!/bin/bash
# A first job: on which node does it run, and with how many cores?

#SBATCH --job-name=hello
#SBATCH --partition=cpu-xeonv3
#SBATCH --cpus-per-task=1
#SBATCH --mem=1G
#SBATCH --time=00:05:00
#SBATCH --output=%x-%j.out
#SBATCH --mail-type=END,FAIL

echo "Job:   $SLURM_JOB_ID"
echo "Node:  $(hostname)"
echo "CPUs:  $SLURM_CPUS_PER_TASK"
echo "Time:  $(date)"
