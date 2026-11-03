# One run of the topic model: fit stm with K topics on the political blogs.
#
# Usage: Rscript run.R <K>
# Writes results/k-<K>.csv with two quality measures and
# results/k-<K>-topics.txt with the most telling words of each topic.

library(stm)

# The number of topics, from the command line: Rscript run.R 10 gives 10.
k <- as.integer(commandArgs(trailingOnly = TRUE)[1])
if (is.na(k)) {
  stop("Usage: Rscript run.R <number of topics>")
}

# 5,000 posts from six US political blogs in 2008, shipped with stm and
# already prepared as documents and vocabulary; `rating` says whether a blog
# is liberal or conservative.
data(poliblog5k, package = "stm")

started <- Sys.time()
# Spectral initialisation gives the same result on the same machine, so the
# runs differ only in K. At most 75 rounds, as in the stm vignette, so that
# each run takes minutes; a real analysis would let it converge.
model <- stm(
  poliblog5k.docs,
  poliblog5k.voc,
  K = k,
  prevalence = ~rating,
  data = poliblog5k.meta,
  init.type = "Spectral",
  max.em.its = 75,
  verbose = FALSE
)
minutes <- as.numeric(difftime(Sys.time(), started, units = "mins"))

# The two measures and the time, as one row of results/k-<K>.csv.
dir.create("results", showWarnings = FALSE)
quality <- data.frame(
  k = k,
  coherence = mean(semanticCoherence(model, poliblog5k.docs)),
  exclusivity = mean(exclusivity(model)),
  minutes = round(minutes, 2),
  # So that combine.R can tell results of an earlier job apart.
  job = Sys.getenv("SLURM_ARRAY_JOB_ID")
)
write.csv(quality, sprintf("results/k-%02d.csv", k), row.names = FALSE)

# FREX words: frequent in the topic and rare in the others.
words <- labelTopics(model, n = 7)$frex
topics <- sprintf(
  "Topic %2d: %s",
  seq_len(k),
  apply(words, 1, paste, collapse = ", ")
)
writeLines(topics, sprintf("results/k-%02d-topics.txt", k))
cat(sprintf("K = %d done in %.1f minutes\n", k, minutes))
