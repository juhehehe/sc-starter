# Install sc-starter

This page shows you how to install sc-starter and check that it reaches
the cluster.

You can also work without sc-starter, as the pages of
[Slurm](../slurm/README.md) show, but the code-alongs in this guide use it.

**Time:** 10 min

## Before you start

Your computer reaches the cluster, as
[Set up your computer](../basics/setup.md) describes.

You install sc-starter with uv. Find out whether uv is already there:

```bash title="Your computer"
uv --version
```

If it prints `uv` and a version number, go on below. If the terminal does
not know the command, install uv first, as
[Packages: uv and renv](../project/packages.md#getting-the-package-manager) shows.

## Install

```bash title="Your computer"
uv tool install https://github.com/juhehehe/sc-starter/archive/refs/heads/main.zip
```

It ends with `Installed 1 executable: sc-starter`. If it also warns that
a folder `is not on your PATH`, run `uv tool update-shell` and open a new
terminal.

!!! check
    Test sc-starter and the connection:

    ```bash title="Your computer"
    sc-starter check
    ```

    ```text title="Output"
    sc-login: ok (login01)
    sc-export: ok (export01)
    Ready.
    ```

    sc-starter connected to both nodes.

[Commands](commands.md#installing-updating-and-removing-sc-starter) shows
how to update and remove sc-starter.
