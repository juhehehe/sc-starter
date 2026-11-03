# The cluster at a glance

This page lists the values of the SC cluster that this guide uses. They
were checked on 20 October 2026 with `sinfo` and `scontrol` on the
cluster and against the [SC documentation](https://www.sc.uni-leipzig.de),
and they can change. `sinfo -s` on the login node shows the partitions as
they are today.

## Machines

| Short name | Host | What for |
|---|---|---|
| `sc-login` | `login01.sc.uni-leipzig.de` | starting jobs and looking at them, never computing |
| `sc-export` | `export01.sc.uni-leipzig.de` | moving files to and from the cluster |
| — | `portal.sc.uni-leipzig.de` | your account, your SSH key, support requests |
| — | `lab.sc.uni-leipzig.de` | Jupyter in the browser |
| — | `rstudio.sc.uni-leipzig.de` | RStudio in the browser |
| — | `www.sc.uni-leipzig.de` | the SC documentation |

The names `sc-login` and `sc-export` come from the SSH settings that the
[setup guide](../basics/setup.md#5-write-the-ssh-settings) writes in step 5.

These are the fingerprints of the servers' keys, the same as on the SC
page [SSH host keys](https://www.sc.uni-leipzig.de/03_System_access/SSH/):

| Host | Type | Fingerprint |
|---|---|---|
| login01 | ED25519 | `SHA256:3saqgn+bVpG3PyG7mtwM2nPQY0NfK9auNCxLCWb85wQ` |
| login01 | ECDSA | `SHA256:IOSVuQ/ip4FiXKZicXAYChm0KiibigU10KHzTREbhrs` |
| login01 | RSA | `SHA256:02tNZqOPx+eqt7kIZbJaw2Vz6vaK7sj8iBbwm5yNyj8` |
| export01 | ED25519 | `SHA256:5lwMCnUQYG50VHNRKULsTdcF1tHGm+FZ8duSEJTppNA` |
| export01 | ECDSA | `SHA256:xYK3VypMR/nMYJFLi6yvrHtKearKMSxzlznxYacZe68` |
| export01 | RSA | `SHA256:GqM5sPXxQ0RNoTkqwVO+m11ATEYaK4pmKsBBYX2qY7A` |

## Partitions

The table shows the computers of each partition and their sizes as
`sinfo` reports them. The SC page
[Hardware](https://www.sc.uni-leipzig.de/02_Resources/Hardware/)
describes them in more detail.

| Partition | Machines | Cores per machine | Memory per machine | GPUs per machine | Memory per core, at most |
|---|---|---|---|---|---|
| `cpu-xeonv3` (default) | 80, `t001` to `t080` | 16 or more | 125 GB | — | 12.5 GB |
| `cpu-zen3` | 32, `paul01` to `paul32` | 128 | 500 GB | — | 93.75 GB |
| `cpu-zen1` | 10, `polaris01` to `polaris10` | 32 | 248 GB | — | 15.6 GB |
| `cpu-bigmem` | 1, `sirius01` | 128 | 5.9 TB | — | 93.75 GB |
| `gpu-a30` | 12, `paula01` to `paula12` | 128 | 981 GB | 8 × A30, 24 GB each | 15.3 GB |
| `gpu-l40s` | 4, `firehorse01` to `firehorse04` | 144 | 376 GB | 4 × L40S | 31.25 GB |
| `gpu-v100` | 6, `clara` | 32 | 500 GB | 4 × V100, 32 GB each | 31.25 GB |
| `gpu-rtx2080ti` | 18, `clara` | 32 | 500 GB | 8 × RTX 2080 Ti, 11 GB each | 31.25 GB |

The code-alongs use `cpu-xeonv3` and `gpu-a30`. The SC documentation
still uses older names for the same computers, such as `paul`, `paula`,
`clara`, `polaris`, `sirius` and `t3000`. `sinfo` lists both kinds of
name.

## GPUs

A job script books a GPU with `#SBATCH --gpus=TYPE:COUNT`, for example
`--gpus=a30:1`. The types are `a30`, `l40s`, `v100` and `rtx2080ti`.

PyTorch from PyPI brings CUDA 13, which needs GPU driver 580 or newer
and does not support the V100, as a
[notice of PyTorch](https://dev-discuss.pytorch.org/t/notice-cuda-12-6-wheels-will-no-longer-be-published-from-pytorch-2-15-drops-maxwell-pascal-volta/3432)
explains. The A30 and L40S have driver 580.178.04, so the GPU
code-alongs book an A30.

## Limits

Slurm treats each run as a job of its own. So these limits, and the wait
as `PENDING`, apply to every run: to each line of `runs.txt`, or to the
single run of a job without it.

| Limit | Value |
|---|---|
| time of a run | at most 2 days (`--time=2-00:00:00`); 1 hour if the job script sets no `--time` |
| memory of a run | 1 GB per booked core if the job script sets no `--mem`; the most per core is in the table of partitions |
| runs of a job | at most 99,999 (`MaxArraySize=100000`) |
| end at the time limit | Slurm sends the program the signal `TERM` and ends it 30 seconds later (`KillWait`) |

A job that asks for more than its partition allows is refused by
`sbatch` at once and never waits (`EnforcePartLimits=ANY`).

Each core comes with a share of memory, as the table of partitions
shows. A job that asks for more memory than its cores come with also gets
more cores, as the SC page
[Slurm](https://www.sc.uni-leipzig.de/05_Instructions/Slurm/) explains.

Longer jobs run in the partitions whose names end in `-long`, such as
`cpu-zen3-long` with 10 days or `cpu-zen1-long` with 42 days. They are
open only to groups that SC lets in, and `sinfo -a -s` lists them.
Without access, `sbatch` stops with
`User's group not permitted to use this partition`. Ask SC support for
access.

## Modules

This guide uses two modules:

| Module | Used by |
|---|---|
| `R/4.5.2-gfbf-2025b` | `first-jobs/hello-r.slurm`, the R code-alongs |
| `Python/3.12.3-GCCcore-13.3.0` | `first-jobs/hello-python.slurm`, the code-along on long runs |

`module spider R` on the login node lists all versions of R, and the SC
[software catalogue](https://portal.sc.uni-leipzig.de/software-catalog)
lists all software. The Python code-alongs with packages install their
own Python with uv instead.
