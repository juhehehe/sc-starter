# Code-alongs

Seven small research projects from the social sciences, in Python and R.
In each one you build the project yourself, from an empty folder to the
results. You plan it, write the code part by part, test it on your
computer, measure what a run needs, write the job scripts, and run it on
the cluster with sc-starter. The finished files of each project are
next to its page.

You need a computer that is set up for the cluster, as described in
[Set up your computer](../docs/basics/setup.md), and
[sc-starter](../docs/sc-starter/install.md). If you are new to the cluster, start
with the first one. When one or two have worked,
[Bring your own project](../docs/sc-starter/bring-your-own-project.md) takes a project of
your own to the cluster.

| Code-along | What you build | What it shows about the cluster | Time |
|---|---|---|---|
| [Topic model in Python](python/python-topic-model/README.md) | topic models of 5,000 political blog posts, one run for each number of topics | many runs side by side, Python packages with uv, a setup job | 45 min |
| [Topic model in R](r/r-topic-model/README.md) | the same in R, with the package stm | R packages with renv, RStudio, ready-made packages for the cluster | 60 min |
| [Segregation model in R](r/r-segregation/README.md) | Schelling's model of a town, for eight wishes and five seeds | 40 runs from two arguments, seeds, pictures without a screen | 45 min |
| [Text embeddings on a GPU](python/python-embeddings/README.md) | embeddings of 8,000 parliamentary questions, searched and grouped | booking a GPU, a model downloaded by the setup job, GPU against CPU | 60 min |
| [Text classifier on a GPU](python/python-classifier/README.md) | a language model that learns which ministry a question goes to | training on a GPU, testing on a sample on your computer | 60 min |
| [BERTopic on a GPU](python/python-bertopic/README.md) | the topics of the same questions | a job that needs a GPU and CPU cores | 60 min |
| [Runs longer than the time limit](python/python-long-run/README.md) | a simulation of opinions among three million people | the time limit, saving progress and continuing in the next job | 45 min |
