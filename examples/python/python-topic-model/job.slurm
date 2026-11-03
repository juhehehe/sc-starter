#!/bin/bash
# One run per line of runs.txt; run N is line N, here one number of topics.
# Submit from your computer with `sc-starter submit`, after running
# `sc-starter submit setup.slurm` once.

#SBATCH --job-name=python-topic-model  # name in the queue and in the output files
#SBATCH --partition=cpu-xeonv3         # standard CPU partition; sinfo -s lists them all
#SBATCH --cpus-per-task=1              # one core, so that the same seed gives the same model
#SBATCH --mem=1G                       # 1 GB of memory per run
#SBATCH --time=00:10:00                # Slurm stops a run after 10 minutes
#SBATCH --output=%x-%A_%a.out          # job name, job ID, run number
#SBATCH --mail-type=END,FAIL           # email when the whole array has ended or failed

# uv, which setup.slurm installed for your account.
export PATH="$HOME/.local/bin:$PATH"

# This run's line of runs.txt, for example "python run.py 10".
run=$(sed -n "${SLURM_ARRAY_TASK_ID}p" runs.txt)
# No such line, as when runs.txt got shorter: end the run as FAILED.
[ -n "$run" ] || { echo "runs.txt has no line $SLURM_ARRAY_TASK_ID"; exit 1; }
echo "Run $SLURM_ARRAY_TASK_ID on $(hostname -s): $run"
# Run it with the project's Python and packages, which setup.slurm put
# into .venv. --no-sync uses them as they are and installs nothing.
uv run --no-sync bash -c "$run"
