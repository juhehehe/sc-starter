# On your computer, after `sc-starter pull`: put all runs side by side.
#
# Usage: Rscript combine.R
# Reads results/k-*.csv, names missing runs, prints the table and draws
# results/choose-k.png: coherence against exclusivity, one point per K.
# Needs only base R, so it works without installing the project's packages.

# Every result file that the runs wrote, read into one table.
files <- list.files("results", pattern = "^k-[0-9]+\\.csv$", full.names = TRUE)
if (length(files) == 0) {
  stop("No results yet. Run `sc-starter pull` first.")
}
quality <- do.call(rbind, lapply(files, read.csv))
quality <- quality[order(quality$k), ]

# warn = FALSE: RStudio may save runs.txt without a line break at the end.
planned <- as.integer(
  sub("^Rscript run.R ", "", readLines("runs.txt", warn = FALSE))
)

# Nothing on the cluster is deleted, so results/ may still hold runs that
# an earlier runs.txt asked for.
old <- !quality$k %in% planned
if (any(old)) {
  message(
    "Left out results of runs not in runs.txt: K = ",
    toString(quality$k[old]),
    "."
  )
  quality <- quality[!old, ]
}
if (nrow(quality) == 0) {
  stop("No results for the runs in runs.txt yet. Run `sc-starter pull` first.")
}

# A run that fails in a later job leaves its earlier result in place.
jobs <- table(quality$job)
cat(
  "Runs per job: ",
  paste(jobs, "from job", names(jobs), collapse = ", "),
  "\n",
  sep = ""
)

missing <- setdiff(planned, quality$k)
if (length(missing) > 0) {
  message(
    "No results for K = ",
    toString(missing),
    ". `sc-starter status` shows why."
  )
}

# One line per run, without the column job.
print(quality[names(quality) != "job"], row.names = FALSE)

# The figure: coherence against exclusivity, one point per run.
png("results/choose-k.png", width = 800, height = 560)
# Room around the points for their labels.
padding <- function(x) range(x) + c(-0.1, 0.1) * diff(range(x))
plot(
  quality$coherence,
  quality$exclusivity,
  type = "b",
  pch = 19,
  xlim = padding(quality$coherence),
  ylim = padding(quality$exclusivity),
  xlab = "Semantic coherence (higher: the words of a topic appear together)",
  ylab = "Exclusivity (higher: the words belong to one topic only)",
  main = "Political blogs 2008: one point per number of topics"
)
# Labels alternate below and above, so that close points stay readable.
text(
  quality$coherence,
  quality$exclusivity,
  paste("K =", quality$k),
  pos = rep(c(1, 3), length.out = nrow(quality))
)
invisible(dev.off())
cat("Wrote results/choose-k.png\n")
