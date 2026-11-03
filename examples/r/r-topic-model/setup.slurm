#!/bin/bash
# Install the R packages of this project on the cluster, once.
# Submit from your computer with `sc-starter submit setup.slurm`, before the
# first `sc-starter submit`. Compute nodes have internet; the login node is
# not for installing.

#SBATCH --job-name=r-topic-model-setup  # name in the queue and in the output file
#SBATCH --partition=cpu-xeonv3          # standard CPU partition
#SBATCH --cpus-per-task=2               # two cores, in case a package must be compiled
#SBATCH --mem=4G                        # 4 GB of memory
#SBATCH --time=00:30:00                 # usually a few minutes; more when compiling
#SBATCH --output=%x-%j.out              # job name and job ID

# Stop at the first command that fails, so that the job ends as FAILED
# rather than COMPLETED. It comes after the #SBATCH lines, since Slurm
# reads those only up to the first command.
set -e

# The R version the jobs will use.
module load R/4.5.2-gfbf-2025b
export LC_ALL=C.UTF-8
# Compile with both booked cores if a package comes as source code.
export MAKEFLAGS="-j${SLURM_CPUS_PER_TASK}"

# Starting R here runs .Rprofile, which fetches renv itself the first time.
# restore() then installs exactly the versions in renv.lock into
# renv/library, as ready-made packages for this Linux where available.
Rscript -e 'renv::restore(prompt = FALSE)'
