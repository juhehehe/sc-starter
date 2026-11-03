# Git: your code on your computer and on the cluster

This page shows you how to record the history of your code with Git and
bring the code to the cluster with it. Every time you reach a state worth
keeping, you save it as a version, and you can always see what changed
and go back.

You do not need Git for this guide, because scp copies your project
folder without it. But Git is worth learning. It keeps the
history of your code, and it makes the code easy to share.

## The words Git uses

A folder whose history Git records is a *repository*. Each saved version
is a *commit*: a snapshot of the files, with a short message that says
what changed. A copy of the repository on a server is called a *remote*.
The best known service for remotes is GitHub, a website where you can
keep repositories for free.

Three commands move commits between computers. `git push` sends your new
commits from your computer to the remote. `git clone` downloads a complete
copy of a repository from the remote, once. `git pull` fetches the
commits that are new since then.

```mermaid
flowchart LR
    computer["Your computer"] -- "git push" --> remote["Remote"]
    remote -- "git clone, then git pull" --> cluster["Cluster"]
```

## Installing Git on your computer

Check whether Git is already installed:

```bash title="Your computer"
git --version
```

If it prints a version number, such as `git version 2.52.0`, Git is
there. If not, install it. On Windows, download Git for Windows from
[git-scm.com](https://git-scm.com/downloads). On macOS, the command above
offers to install the Apple command line tools, which include Git. On
Linux, install the package `git` with your package manager.

Tell Git your name and email address once. They appear in every commit:

```bash title="Your computer"
git config --global user.name "Your Name"
git config --global user.email "you@example.org"
```

In a public repository, anyone can read this email address. GitHub gives
you a private address for this purpose, which ends in
`@users.noreply.github.com`. You find it under Settings › Emails, as
described in [Setting your commit email address](https://docs.github.com/en/account-and-profile/setting-up-and-managing-your-personal-account-on-github/managing-email-preferences/setting-your-commit-email-address).

Git is already installed on the cluster.

## Choosing what goes into Git

Before you save the first version, decide which files Git should leave
out. List them in a file called `.gitignore` in the project folder, one
per line:

```text title=".gitignore"
.venv/
results/
*.out
data/
```

Leave out the packages in `.venv`, because uv installs them again from
the lock file. Leave out the results and the output files, because the
runs create them. Leave out data if they are large or if you may not
share them. A repository on GitHub can be public, and many data sets come
with a contract that limits where they may be stored.

Files that Git has already saved stay in the history even if you add
them to `.gitignore` later. This is why the `.gitignore` comes first.

Everything else goes into Git: your code, your job scripts, the list of
runs `runs.txt`, and the files that describe your packages. For Python
these are `pyproject.toml`, `uv.lock` and `.python-version`. For R they
are `renv.lock`, `.Rprofile`, `renv/activate.R` and `renv/settings.json`.
[Packages: uv and renv](packages.md) explains these files.

## Saving the first version

In the project folder on your computer, start a repository and save the
first version:

```bash title="Your computer"
git init
git add .
git commit -m "First version"
```

`git init` creates the repository, `git add .` marks all files in the
folder for the next commit, except those in `.gitignore`, and
`git commit` saves them with the message after `-m`.

## Sending the project to GitHub

You need a free account on GitHub, as described in
[Creating an account on GitHub](https://docs.github.com/en/get-started/start-your-journey/creating-an-account-on-github).
Create a new, empty repository there. GitHub then shows you the commands
that connect your computer to it. They look like this:

```bash title="Your computer"
git branch -M main
git remote add origin https://github.com/YOUR_NAME/my-project.git
git push -u origin main
```

The first command names the main line of your history `main`, as GitHub
expects. The second tells Git the address of the remote. The third sends
your commits there.

The first `git push` asks you to sign in to GitHub. On Windows, Git opens
a browser window for this. On macOS and Linux, GitHub does not accept
your password at this point. Follow GitHub's page
[Caching your GitHub credentials in Git](https://docs.github.com/en/get-started/git-basics/caching-your-github-credentials-in-git)
to set up the sign-in once.

## Downloading the project on the cluster

Log in to the cluster and download the repository, once:

```bash title="Your computer"
ssh sc-login
```

```bash title="Cluster"
git clone https://github.com/YOUR_NAME/my-project.git
cd my-project
```

The cluster now has a folder `my-project` with your code. The data are
not in it, because `.gitignore` left them out. Copy them separately, as
described in [Copying files to and from the cluster](copying-files.md).

## Keeping both copies in step

After each change, save it on your computer and send it to GitHub:

```bash title="Your computer"
git add .
git commit -m "Use 1,000 iterations"
git push
```

Before you submit the next job, fetch the change on the cluster:

```bash title="Cluster"
cd my-project
git pull
```

Make your changes on your computer. If you also change files on the
cluster, the two copies drift apart, and `git pull` may stop with a
message about a conflict.

## Private repositories

Anyone can download a public repository, so the commands above work as
they are. For a private repository, the cluster needs permission to read
it. A safe way is a deploy key: an SSH key on the cluster that GitHub
lets read this one repository and nothing else. GitHub explains how to
create one in [Managing deploy keys](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/managing-deploy-keys).
You then clone with the address that starts with `git@github.com:`
instead of `https://`.

## Git and sc-starter

sc-starter does not use Git. It copies your project folder as it is on
your computer, including changes you have not committed yet. It leaves the
folder `.git`, where Git keeps the history, on your computer, and Git
ignores the folder `.sc-starter`, where sc-starter keeps its notes. You
can keep your code in Git and still run it with sc-starter.

## Further reading

- [Version control with Git](https://swcarpentry.github.io/git-novice/),
  a beginner's course by Software Carpentry.
- [About Git](https://docs.github.com/en/get-started/using-git/about-git)
  in the GitHub documentation.
- [Pro Git](https://git-scm.com/book/en/v2), a free book on Git.
