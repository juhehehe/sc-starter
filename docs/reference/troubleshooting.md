# Troubleshooting

This page lists the messages you may see, what they mean and what to do.
Find yours in the table.

`YOUR_LOGIN` stands for your university login, `JOB_ID` for the number of
a job, `RUN` for the number of a run, `FOLDER_NAME` for the name of your
project folder and `FILE` for the name of a file.

| What you see | When | Go to |
|---|---|---|
| `Cannot reach the cluster`, or the test of the setup says `not reachable` | connecting | [The cluster is not reachable](#the-cluster-is-not-reachable) |
| SSH asks for a password, or says `Permission denied` | connecting | [The cluster does not accept your key](#the-cluster-does-not-accept-your-key) |
| `Could not chdir to home directory` | logging in | [Your account is not ready yet](#your-account-is-not-ready-yet) |
| `Could not resolve hostname sc-login` | connecting | [SSH does not know sc-login](#ssh-does-not-know-sc-login) |
| `ssh does not know sc-export yet` | connecting | [SSH does not know the server yet](#ssh-does-not-know-the-server-yet) |
| `REMOTE HOST IDENTIFICATION HAS CHANGED` | connecting | ["REMOTE HOST IDENTIFICATION HAS CHANGED"](#remote-host-identification-has-changed) |
| a warning about `post-quantum key exchange` | connecting | [A warning about post-quantum key exchange](#a-warning-about-post-quantum-key-exchange) |
| `There is no job.slurm in this folder`, `No job was submitted from this folder yet`, `This folder has no job script` | any sc-starter command | [The terminal is in the wrong folder](#the-terminal-is-in-the-wrong-folder) |
| `runs.txt, line …` with `is empty`, `is a comment`, `ends with \` or `has a hidden line break` | submitting | [A line of runs.txt is not a run](#a-line-of-runstxt-is-not-a-run) |
| `setup.slurm (job …) has not finished yet` | submitting | [The setup job is still running](#the-setup-job-is-still-running) |
| `The cluster has a newer copy` | submitting or pushing | ["The cluster has a newer copy"](#the-cluster-has-a-newer-copy) |
| `Batch job submission failed` | submitting | ["Batch job submission failed"](#batch-job-submission-failed) |
| `The lockfile at uv.lock needs to be updated` | the setup job | [The lock file does not match](#the-lock-file-does-not-match) |
| `PENDING (Priority)` or `PENDING (Resources)` | waiting | [The job waits](#the-job-waits) |
| `FAILED` with exit code `127` | running | [A command was not found](#a-command-was-not-found) |
| `ModuleNotFoundError` or `there is no package called` | running | [A package is missing on the cluster](#a-package-is-missing-on-the-cluster) |
| `TIMEOUT` | running | [The run reached its time limit](#the-run-reached-its-time-limit) |
| `OUT_OF_MEMORY`, `Killed` or `oom_kill` | running | [The run needed more memory](#the-run-needed-more-memory) |
| `Disk quota exceeded`, or `The output file … is empty` | pushing or running | [Your home directory is full](#your-home-directory-is-full) |
| `unable to start device PNG` | running R | [R cannot draw PNG files](#r-cannot-draw-png-files) |
| `This job has a GPU, but PyTorch cannot use it` | running Python on a GPU | [Python: "This job has a GPU, but PyTorch cannot use it"](#python-this-job-has-a-gpu-but-pytorch-cannot-use-it) |
| `Cannot find the requested files in the disk cache` | running Python with a model | [The model was not downloaded](#the-model-was-not-downloaded) |
| `Nothing to pull yet` | pulling | [There is nothing to pull yet](#there-is-nothing-to-pull-yet) |

## Connecting to the cluster

When SSH fails, sc-starter adds a second line that begins with
`ssh said:` and quotes the message of SSH itself.

### The cluster is not reachable

```text title="Output"
sc-starter: Cannot reach the cluster. Is the VPN on? On the university network it works without.
```

Or the test in [step 2 of the setup](../basics/setup.md#2-connect-to-the-university-network)
says `not reachable`, or `False` on Windows. The cluster answers only
from inside the university network, and your computer is outside it.

To fix it:

1. Connect the VPN, as in [Connect the VPN](../basics/setup.md#connect-the-vpn).
   Only one device can use your VPN account at a time, so disconnect your
   phone first.
2. On Linux, stop Docker if it runs, and try again. Its networks can
   cover addresses of the university network.

### The cluster does not accept your key

SSH asks for a password:

```text title="Output"
YOUR_LOGIN@login01.sc.uni-leipzig.de's password:
```

Or it refuses at once:

```text title="Output"
YOUR_LOGIN@login01.sc.uni-leipzig.de: Permission denied (publickey,gssapi-keyex,gssapi-with-mic,password).
```

Or sc-starter says:

```text title="Output"
sc-starter: The cluster did not accept your key. Is it loaded in the SSH agent (step 3) and uploaded to the portal (step 4)? See the setup guide, docs/basics/setup.md.
ssh said: YOUR_LOGIN@login01.sc.uni-leipzig.de: Permission denied (publickey,gssapi-keyex,gssapi-with-mic,password).
```

The cluster did not get a key that it knows. Do not type your password.
Press Ctrl+C and go through these points in order:

1. Check that the SSH agent has your key. `ssh-add -l` lists the keys it
   holds. If it prints `The agent has no identities.`, give it the key
   again:
    - On Linux, where the agent forgets the key at every restart, log in
      once by hand with `ssh sc-login` and type your passphrase.
    - On macOS, type `ssh-add --apple-load-keychain`.
    - On Windows, type `ssh-add "$HOME\.ssh\id_ed25519_sc"`. If that says
      `Error connecting to agent`, the agent is switched off. Turn it on
      as in [Turn on the SSH agent](../basics/setup.md#turn-on-the-ssh-agent).
2. Check that the portal has your public key. Compare the line in your
   file `id_ed25519_sc.pub` with the key in the SC portal, as in
   [step 4 of the setup](../basics/setup.md#4-upload-the-public-key).
3. On Windows, check which terminal you use. RStudio opens Git Bash when
   Git for Windows is installed. In Git Bash, sc-starter uses the SSH of
   Git, and that SSH cannot reach your key. Use PowerShell instead.
4. Check whether the cluster is in maintenance. SC may block logins
   then. The [SC status page](https://www.sc.uni-leipzig.de/00_Status/status/)
   says so.

### Your account is not ready yet

```text title="Output"
Could not chdir to home directory /home/sc.uni-leipzig.de/YOUR_LOGIN: No such file or directory
```

`sinfo -s` also shows only the line with the column names, and no
partitions. SC has approved your account, but the cluster has not
finished setting it up. Wait a few hours and log in again, as
[step 1 of the setup](../basics/setup.md#1-apply-for-access) describes.

### SSH does not know sc-login

```text title="Output"
ssh: Could not resolve hostname sc-login: Name or service not known
```

Or sc-starter says:

```text title="Output"
sc-starter: ssh does not know the name sc-login. Write the SSH settings from the setup guide, docs/basics/setup.md (step 5).
```

The short names `sc-login` and `sc-export` are missing from your SSH
settings. Write them as in
[step 5 of the setup](../basics/setup.md#5-write-the-ssh-settings).

### SSH does not know the server yet

```text title="Output"
sc-starter: ssh does not know sc-export yet. Log in once by hand with `ssh sc-export` and compare the fingerprint (the setup guide, docs/basics/setup.md, step 6).
```

SSH has not saved the fingerprint of this server yet, so it refuses to
connect without asking you. This happens when the first connection to
the export node was left out of the setup. Connect once by hand and
answer the question about the fingerprint, as in
[Connect to the export node once](../basics/setup.md#connect-to-the-export-node-once).

### "REMOTE HOST IDENTIFICATION HAS CHANGED"

```text title="Output"
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@    WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!     @
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
```

Later SSH says `Host key verification failed.` Or sc-starter says:

```text title="Output"
sc-starter: sc-login shows another key than the one ssh remembers. Usually SC has renewed it; read "REMOTE HOST IDENTIFICATION HAS CHANGED" in docs/reference/troubleshooting.md before you go on.
```

The server shows another fingerprint than the one your computer saved at
the first login. Usually SC has renewed the keys of its servers, for
example during maintenance. Rarely, someone pretends to be the server.

To fix it:

1. Compare the new fingerprint with the list on the SC page
   [SSH host keys](https://www.sc.uni-leipzig.de/03_System_access/SSH/).
   If it is not listed, do not connect, and write to SC.
2. If it is listed, make your computer forget the old fingerprint and log
   in again. Answer the question about the fingerprint as in
   [step 6 of the setup](../basics/setup.md#6-log-in-for-the-first-time):

    ```bash title="Your computer"
    ssh-keygen -R login01.sc.uni-leipzig.de
    ssh sc-login
    ```

    For the export node, do the same with `export01.sc.uni-leipzig.de` and
    `ssh sc-export true`.

### A warning about post-quantum key exchange

```text title="Output"
** WARNING: connection is not using a post-quantum key exchange algorithm.
** This session may be vulnerable to "store now, decrypt later" attacks.
** The server may need to be upgraded. See https://openssh.com/pq.html
```

The SSH on your computer is newer than the one on the cluster. The
warning concerns the server, and SC has to update it. Everything works,
so you need to do nothing.

## Submitting and copying

### The terminal is in the wrong folder

Depending on the command, sc-starter says one of these:

```text title="Output"
sc-starter: There is no job.slurm in this folder.
```

```text title="Output"
sc-starter: No job was submitted from this folder yet.
```

```text title="Output"
sc-starter: This folder has no job script (*.slurm), so it is not a project. Go to your project folder first, with `cd`.
```

sc-starter works with the folder that the terminal is in. Move into the
folder of your project with `cd`, as
[Working in the terminal](../basics/terminal.md#opening-a-terminal-in-a-folder)
describes, and try again.

`sc-starter pull` in a folder that was never submitted says
`There is no ~/sc-projects/FOLDER_NAME on the cluster`. If sc-starter
says that the folder name cannot be used on the cluster, the name holds
a character other than letters, digits, dots, hyphens and underscores,
such as a space. Rename the folder.

### A line of runs.txt is not a run

```text title="Output"
sc-starter: runs.txt, line 4 is empty. Every line is one run, so remove empty lines.
```

Line N of `runs.txt` is run N, so every line has to be one complete
command. sc-starter checks this before it submits anything, and names the
line it does not accept:

| The message says | What to do |
|---|---|
| `is empty` | remove the empty line, also at the end of the file |
| `is a comment` | remove the line that starts with `#`, and keep notes elsewhere |
| `ends with \` | write the whole command on one line |
| `has a hidden line break` | delete the line and type it again; text copied from another program can hold invisible characters |

### The setup job is still running

```text title="Output"
sc-starter: setup.slurm (job 28404223) has not finished yet. Submit job.slurm once `sc-starter status` shows it COMPLETED.
```

The packages are still being installed, and a run that started now would
not find them. Wait until `sc-starter status` shows the setup job as
`COMPLETED`, then submit again. If it shows `FAILED`, `sc-starter log`
shows why.

### "The cluster has a newer copy"

```text title="Output"
sc-starter: The cluster has a newer copy of these files than this folder:
  checkpoint.pickle
Nothing was uploaded, so that none is overwritten. Read "The cluster has a newer copy" in docs/reference/troubleshooting.md.
```

sc-starter compares each file with its copy in
`~/sc-projects/FOLDER_NAME` on the cluster. The copy there has changed
since it was uploaded. A job may have written it, such as a checkpoint,
or you changed it on the cluster. Or this folder is an older copy of the
project, from another computer or a backup.

Decide for each file which copy to keep:

- To keep the copy on the cluster, delete the one in your folder. If you
  want it on your computer as well, copy it with its time first:
  `scp -p sc-export:sc-projects/FOLDER_NAME/FILE FILE`.
- To send your copy, give it a new time: `touch FILE` on Linux and
  macOS, or `(Get-Item FILE).LastWriteTime = Get-Date` in PowerShell.

Then push or submit again.

### "Batch job submission failed"

```text title="Output"
sc-starter: The command on sc-login failed (exit code 1).
sbatch: error: Batch job submission failed: Requested time limit is invalid (missing or exceeds some limit)
```

Slurm refused the job because of an `#SBATCH` line in the job script. It
checks the limits when you submit, so a job that asks for too much never
waits in the queue. The end of the message names the cause:

| End of the message | The line to fix |
|---|---|
| `Requested time limit is invalid` | `--time` is longer than 2 days |
| `invalid partition specified` | `--partition` has a typo |
| `Requested node configuration is not available` | the job asks for more cores, memory or GPUs than a computer of that partition has |

Compare the line with [The cluster at a glance](cluster-at-a-glance.md), change it
and submit again. If your account is new and `ssh sc-login sinfo -s`
shows no partitions, your account is not ready yet, as described in
[Your account is not ready yet](#your-account-is-not-ready-yet).

### The lock file does not match

The setup job of a Python project ends as `FAILED`, and `sc-starter log`
shows:

```text title="Output"
error: The lockfile at `uv.lock` needs to be updated, but `--locked` was provided.

hint: To update the lockfile, run `uv lock`.
```

You changed `pyproject.toml`, but `uv.lock` still lists the packages of
before. The setup job installs only what the lock file lists, and stops
when it does not match. On your computer, in the project folder, type
`uv lock`, or `uv sync`, which also installs the packages there. Then
submit the setup job again.

## The job waits

`sc-starter status` shows runs as `PENDING (Priority)` or
`PENDING (Resources)`, for example:

```text title="Output"
Job 28514701: 2 PENDING, 1 RUNNING

run  state               exit  node  elapsed  command
1    RUNNING                   t010  0:41     python run.py 5
2    PENDING (Priority)              0:00     python run.py 10
3    PENDING (Priority)              0:00     python run.py 15
```

That is normal. `Priority` means that other jobs
are ahead of yours. `Resources` means that no node has enough free
cores, memory or GPUs right now. GPUs are in demand and often have a
queue.

Wait, and the runs start on their own. Jobs that ask for less start
sooner, because Slurm can fit them into gaps.
[Choosing time and memory](../slurm/time-and-memory.md) shows how
to check what a run really needs, so that you can lower `--time`,
`--mem` and `--cpus-per-task`.

## A run fails

`sc-starter status` shows a run as `FAILED`, `TIMEOUT`, `OUT_OF_MEMORY`
or `CANCELLED`, and writes the numbers of these runs into `failed.txt`.
`sc-starter log RUN` shows what the run printed, which usually names the
cause.

After a fix, and once no run of the job waits or runs any more, start
only the failed runs again. `submit` uploads your fix first:

```bash title="Your computer"
sc-starter submit --lines failed.txt
```

Fix lines of `runs.txt` in place. Run numbers are line numbers, so adding
or removing a line would shift the runs below it. Submit a job without
`runs.txt`, such as a setup job or a single GPU job, again as a whole,
with `sc-starter submit setup.slurm` or `sc-starter submit`.

### A command was not found

```text title="Output"
run  state          exit   node  elapsed   command
1    FAILED         127:0  t003  00:00:00  pyhton --version
```

`sc-starter log 1` shows:

```text title="Output"
Run 1 on t003: pyhton --version
bash: line 1: pyhton: command not found
```

The command in that line of `runs.txt` does not exist, here `pyhton`
instead of `python`. The exit code `127` always means that a command was
not found. Correct the line, then submit the failed runs again.

### A package is missing on the cluster

A Python run stops with a message such as:

```text title="Output"
ModuleNotFoundError: No module named 'tomotopy'
```

An R run stops with a message such as:

```text title="Output"
Error in library(stm) : there is no package called ‘stm’
```

The package is on your computer but not in the project's environment on
the cluster. Usually the setup job has not run since you added the
package, or it failed.

To fix it:

1. Check that the package is in the lock file: `uv.lock` for Python,
   `renv.lock` for R. If not, add it with `uv add` or record it with
   `renv::snapshot()`, as [Packages: uv and renv](../project/packages.md) explains.
2. Run the setup job again with `sc-starter submit setup.slurm`, and wait
   until it shows `COMPLETED`.
3. For R, check that the lines of `runs.txt` start with `Rscript` and not
   with `Rscript --vanilla`, which skips the project's packages.

### The run reached its time limit

For a run with `--time=00:02:00`:

```text title="Output"
run  state          exit   node  elapsed   command
2    TIMEOUT        0:0    t003  00:02:15  sleep 600
```

`sc-starter log 2` ends with a line from Slurm:

```text title="Output"
Run 2 on t003: sleep 600
[2026-10-20T13:24:42.004] error: *** JOB 28408618 ON t003 CANCELLED AT 2026-10-20T13:24:42 DUE TO TIME LIMIT ***
```

The run needed longer than `--time` in `job.slurm`, and Slurm stopped
it. The exit code `0:0` does not mean success here. The state `TIMEOUT`
counts.

Raise `--time`. The cluster allows at most 2 days, except in the
[long partitions](cluster-at-a-glance.md#limits). If a run needs longer, split it
into several runs. Or let it save its progress and continue, as
[Runs longer than the time limit](../../examples/python/python-long-run/README.md)
shows.

### The run needed more memory

For a run with `--mem=200M` that needed 1 GB:

```text title="Output"
run  state          exit   node  elapsed   command
3    OUT_OF_MEMORY  0:125  t003  00:00:00  python3 -c "x = b'1' * 10**9"
```

`sc-starter log 3` shows:

```text title="Output"
Run 3 on t003: python3 -c "x = b'1' * 10**9"
/var/spool/slurmd/job28408616/slurm_script: line 13: 71798 Killed                  bash -c "$run"
[2026-10-20T13:22:27.166] error: Detected 1 oom_kill event in StepId=28408616.batch. Some of the step tasks have been OOM Killed.
```

The run needed more memory than `--mem` in `job.slurm`, and Slurm stopped
it. `Killed` and `oom_kill` in the log both mean that it ran out of
memory. Raise `--mem`, and check afterwards what the run really used, as
[Choosing time and memory](../slurm/time-and-memory.md) shows.

### Your home directory is full

`sc-starter push` stops with lines that end in `Disk quota exceeded`, or
runs fail with an empty or cut-off log. `sc-starter log` then says:

```text title="Output"
The output file python-topic-model-28514701_3.out is empty. If the run failed, your home directory may be full: `ssh sc-export sc_quotas` shows it.
```

Your home directory on the cluster holds 100 GB, including all projects
and the shared stores of packages and models. `ssh sc-export sc_quotas`
shows how full it is.
[Keep your account tidy](keep-your-account-tidy.md) shows what takes up space and
how to remove it.

### R cannot draw PNG files

```text title="Output"
Error in .External2(C_X11, paste0("png::", filename), g$width, g$height,  :
  unable to start device PNG
Calls: png
In addition: Warning message:
In png(sprintf("results/grid-%.1f.png", threshold), width = 480,  :
  unable to open connection to X11 display ''
Execution halted
```

By default, R draws PNG files through a screen, and the computers of the
cluster have none. Put `options(bitmapType = "cairo")` at the top of the
script, or write `png(..., type = "cairo")`.

### Python: "This job has a GPU, but PyTorch cannot use it"

```text title="Output"
This job has a GPU, but PyTorch cannot use it. See README.md.
```

The scripts of the GPU code-alongs stop with this message when the job
has a GPU but PyTorch cannot reach it, so that the GPU does not sit
idle.
Usually a version of PyTorch without GPU support was installed. Compare
your `pyproject.toml` with the one of
[Text embeddings on a GPU](../../examples/python/python-embeddings/README.md),
then run `sc-starter submit setup.slurm` again.

### The model was not downloaded

```text title="Output"
Cannot find the requested files in the disk cache and outgoing traffic has been disabled.
```

The GPU jobs of the code-alongs load their language model from the
folder in which the setup job saved it, and never download it
themselves. So the setup job has not downloaded the model. Perhaps it
failed, or you changed `MODEL` in `run.py` since.
Look at its log with `sc-starter log --job JOB_ID`, using the job ID of
the setup job, and run `sc-starter submit setup.slurm` again.

## Bringing results back

### There is nothing to pull yet

```text title="Output"
sc-starter: Nothing to pull yet: ~/sc-projects/FOLDER_NAME has no results/ folder and no output files.
```

No run has started yet, so there is nothing to bring back.
`sc-starter status` shows whether the runs are still waiting.

## Getting help

- The [SC documentation](https://www.sc.uni-leipzig.de) answers most
  questions about the cluster.
- SC support helps with your account, the cluster and jobs. Use the form
  [Request support](https://portal.sc.uni-leipzig.de/request-support) in
  the SC portal, or write to <sc-request@uni-leipzig.de>, the address the
  login node greets you with.
- The service desk of the URZ, the university's computing centre, helps
  with the VPN and your university login: <servicedesk@uni-leipzig.de>,
  phone +49 341 97-33333.
- For problems with sc-starter or this guide, open an
  [issue on GitHub](https://github.com/juhehehe/sc-starter/issues).

When you ask for help, say what you typed, and paste the whole message,
the job ID and the output of `sc-starter --version`. Never send your
private key or its passphrase. Nobody needs them to help you.
