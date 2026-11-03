# Copying files to and from the cluster

This page explains `scp` and `rsync`, which copy data and other files to
and from the cluster. Git is best for code, as described in
[Git: your code on your computer and on the cluster](git.md).

Copies with `scp` and `rsync` go through the export node, which this
guide calls `sc-export`.

```mermaid
flowchart LR
    accTitle: The way of a copy
    accDescr: scp and rsync copy files between your computer and the export node, in both directions. On the cluster, the files are in your home directory.
    computer["Your computer"] <-->|"scp, rsync"| export["Export node"]
    export <--> home[("Home directory")]
```

## Copying with scp

[Your first job](../slurm/first-job.md#submitting-the-job) copies a folder with
scp. scp comes with Linux, macOS and Windows. You give it what to copy
and where to put it. A place on the cluster starts
with `sc-export:`. A path after it that does not start with `/` begins in
your home directory there.

scp does not create missing folders on the cluster, so create the target
folder first, with `mkdir -p` over SSH:

```bash title="Your computer"
ssh sc-export mkdir -p my-project/data
```

Then copy a file from your computer to the cluster:

```bash title="Your computer"
scp survey.csv sc-export:my-project/data/
```

To copy a whole folder, add `-r`:

```bash title="Your computer"
scp -r data sc-export:my-project/
```

To copy from the cluster to your computer, swap the two. The dot at the end
means "into the current folder":

```bash title="Your computer"
scp -r sc-export:my-project/results .
```

scp copies every file each time, even if it has not changed.

## Copying with rsync

*rsync* copies only the files that are new or have changed, which saves a
lot of time for large folders. It can also leave folders out. It comes
with Linux and macOS, but not with Windows. On Windows, use scp.

```bash title="Your computer"
rsync -av --exclude .venv my-project sc-export:
```

This copies the folder `my-project` into your home directory on the
cluster, without the folder `.venv`. `-a` keeps the folder structure and
the dates of the files, and `-v` lists what is copied. Run the same
command again after a change, and rsync copies only what is new.

## Large data

Your home directory on the cluster holds 100 GB in total. For larger
data, SC offers workspaces: folders with up to 5 TB that you create for 30
days at a time and can extend a few times. When a workspace expires, SC
deletes it and everything in it. The
[Workspaces](https://www.sc.uni-leipzig.de/04_Data_Management/Workspaces/)
page of the SC documentation explains how to create and extend one.

Large data are best copied once, into a folder outside your projects. So
that your script finds them both on your computer and on the cluster, let
it take the path of the data folder as an argument, for example
`python run.py /path/to/data 10`. Write the path of the cluster's copy
into the lines of `runs.txt`.

Before you copy data to the cluster, check that you may. Survey and
register data often come with a contract that says where they may be
stored and analysed. The
[SC usage policy](https://www.sc.uni-leipzig.de/00_Misc/policies/User%20policy.en/)
sets the rules for the cluster.

## No backups

The cluster does not make backups of your files. Keep the originals of
your code and data on your computer or on university storage, and copy
your results back after each job. Delete what you no longer need on the
cluster, so that your home directory does not fill up.
[Keep your account tidy](../reference/keep-your-account-tidy.md) explains how to see what takes
up space.

## Further reading

- [File systems and file transfer](https://www.sc.uni-leipzig.de/04_Data_Management/File_transfer/)
  in the SC documentation.
- [Transferring files with remote computers](https://hpc-carpentry.github.io/hpc-intro/16-transferring-files.html),
  a workshop lesson by HPC Carpentry.
