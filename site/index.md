---
hide: [navigation, toc]
---

<div class="home-hero" markdown>

# Using the SC cluster with Python and R

This guide shows you how to run your Python and R code on the cluster of
Scientific Computing (SC) at Leipzig University. The cluster helps with
analyses that are too large or too slow for your own computer. You need
no experience with clusters to begin, only an account at the university
and some Python or R.

</div>

## Four steps through this guide

<div class="grid cards stations" markdown>

1.  **Set up your computer**

    Get access to the cluster and connect to it for the first time.

    **Time:** 60 min

    [Set up your computer](docs/basics/setup.md)

2.  **Learn the basics**

    How work on a cluster goes, how a job script tells the cluster what to
    run, and the tools for each step: the terminal, uv or renv for your
    packages, and Git.

    **Time:** 60 min

    [Basics](docs/basics/README.md) · [Slurm](docs/slurm/README.md) ·
    [Your project on the cluster](docs/project/README.md)

3.  **Build your first project**

    Build a small research project from an empty folder, test it on your
    computer and run it on the cluster.

    **Time:** 45 min

    [Code-alongs](examples/README.md)

4.  **Bring your own project**

    Prepare a project that already runs on your computer for the cluster.

    [Bring your own project](docs/sc-starter/bring-your-own-project.md)

</div>

## What sc-starter does

sc-starter is a small program that runs on your computer. You type its
commands in a terminal opened in the folder of your project. sc-starter
then takes care of the steps on the cluster for you.
It copies your project there, asks the cluster to run it and brings the
results back to the same folder:

```bash title="Your computer"
sc-starter submit    # copy the project to the cluster and start it
sc-starter status    # see how each run is doing
sc-starter pull      # bring the results back
```

Your scripts stay ordinary Python or R scripts. A short file in the
project, the job script, tells the cluster how much time, memory and
computing power each run needs.
[Working with sc-starter](docs/sc-starter/working-with-sc-starter.md) explains each step,
and the [command reference](docs/sc-starter/commands.md) lists every option.

## Code-alongs from the social sciences

Seven small research projects, in Python and R. In each one you build the
project yourself, from an empty folder: you write the code, test it on
your computer, write the job scripts and run it on the cluster. They
cover many runs side by side, R packages, GPUs and runs longer than the
time limit.

[See all code-alongs](examples/README.md)

## Help

<div class="grid cards" markdown>

-   **Something went wrong**

    The messages you may see, what they mean and what to do.
    [Troubleshooting](docs/reference/troubleshooting.md)

-   **A word is unclear**

    The technical terms used in this guide, explained.
    [Glossary](docs/reference/glossary.md)

-   **Your account or the cluster itself**

    sc-starter is not run by the SC team. For questions about your account
    or the cluster, contact
    [SC support](https://portal.sc.uni-leipzig.de/request-support).

</div>
