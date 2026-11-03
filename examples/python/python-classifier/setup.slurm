#!/bin/bash
# Install this project's Python and packages on the cluster, once, and
# download the model. Submit from your computer with
# `sc-starter submit setup.slurm`, before the first `sc-starter submit`.
# It runs on a CPU node: installing needs no GPU, and the GPU job that
# follows then needs no internet.

#SBATCH --job-name=python-classifier-setup  # name in the queue and in the output file
#SBATCH --partition=cpu-xeonv3              # standard CPU partition
#SBATCH --cpus-per-task=2                   # two cores for unpacking
#SBATCH --mem=4G                            # 4 GB of memory
#SBATCH --time=00:30:00                     # PyTorch is large; a few minutes the first time
#SBATCH --output=%x-%j.out                  # job name and job ID

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

# Exactly the versions in uv.lock, into .venv in this folder. --locked
# stops if uv.lock does not match pyproject.toml.
uv sync --locked

# Load the model named in run.py and its tokenizer once, which downloads
# them into the Hugging Face cache, ~/.cache/huggingface. The GPU job loads
# them from there.
.venv/bin/python -c 'from run import MODEL; from transformers import AutoModel, AutoTokenizer; AutoTokenizer.from_pretrained(MODEL); AutoModel.from_pretrained(MODEL); print("Model ready:", MODEL)'
