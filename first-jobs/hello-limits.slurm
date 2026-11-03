#!/bin/bash
# A first job: what happens when a job asks for too little memory or time?
# On the cluster, in this folder: sbatch hello-limits.slurm; then again
# with less memory or time, as docs/slurm/time-and-memory.md shows.

#SBATCH --job-name=hello-limits   # name shown in the queue (squeue --me)
#SBATCH --partition=cpu-xeonv3    # which group of machines; sinfo -s lists them all
#SBATCH --cpus-per-task=1         # one CPU core
#SBATCH --mem=200M                # 200 MB of memory
#SBATCH --time=00:02:00           # Slurm stops the job after 2 minutes
#SBATCH --output=%x-%j.out        # output file; %x becomes the job name, %j the job ID

module load Python/3.12.3-GCCcore-13.3.0

# Fill about 100 MB of memory and keep it for a minute and a half.
python -c 'import time; block = b"x" * 100_000_000; time.sleep(90); print("Done")'
