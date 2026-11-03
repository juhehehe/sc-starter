#!/bin/bash
# Install this project's Python and packages on the cluster, once.
# Submit from your computer with `sc-starter submit setup.slurm`, before the
# first `sc-starter submit`. Compute nodes have internet; the login node is
# not for installing.

#SBATCH --job-name=python-topic-model-setup  # name in the queue and in the output file
#SBATCH --partition=cpu-xeonv3               # standard CPU partition
#SBATCH --cpus-per-task=1                    # downloading needs one core
#SBATCH --mem=2G                             # 2 GB of memory
#SBATCH --time=00:15:00                      # usually under a minute
#SBATCH --output=%x-%j.out                   # job name and job ID

# Stop at the first command that fails, so that the job ends as FAILED
# rather than COMPLETED. It comes after the #SBATCH lines, since Slurm
# reads those only up to the first command.
set -e

# uv installs Python and the packages. The first time, fetch uv itself
# into ~/.local/bin, the same place as on a Linux computer.
export PATH="$HOME/.local/bin:$PATH"
if ! command -v uv > /dev/null; then
  curl -LsSf https://astral.sh/uv/0.12.10/install.sh | env UV_NO_MODIFY_PATH=1 sh
fi

# Exactly the versions in uv.lock, into .venv in this folder; uv fetches
# Python 3.12 first if the cluster does not have it. --locked stops if
# uv.lock does not match pyproject.toml, instead of quietly changing it.
uv sync --locked
