# On your computer, after `sc-starter pull`: put all runs side by side.
#
# Usage: Rscript combine.R
# Reads results/run-*.csv, names missing runs, prints one line per
# threshold and draws results/segregation.png. Needs only base R.

# Every result file that the runs wrote, read into one table.
files <- list.files("results", pattern = "^run-.*\\.csv$", full.names = TRUE)
if (length(files) == 0) {
  stop("No results yet. Run `sc-starter pull` first.")
}
runs <- do.call(rbind, lapply(files, read.csv))

# runs.txt lines read "Rscript run.R 0.3 2": threshold, then seed.
# Compared as numbers, so that 0.35 and 0.3 stay apart and 0.30 is 0.3.
# warn = FALSE: an editor may save runs.txt without a line break at the end.
planned <- sub("^Rscript run.R ", "", readLines("runs.txt", warn = FALSE))
wanted <- read.table(text = planned, col.names = c("threshold", "seed"))
wanted <- paste(wanted$threshold, wanted$seed)
done <- paste(runs$threshold, runs$seed)

# Nothing on the cluster is deleted, so results/ may still hold runs that
# an earlier runs.txt asked for; they would change the means.
old <- !done %in% wanted
if (any(old)) {
  message(
    "Left out results of runs not in runs.txt: ",
    toString(done[old]),
    "."
  )
  runs <- runs[!old, ]
}
if (nrow(runs) == 0) {
  stop("No results for the runs in runs.txt yet. Run `sc-starter pull` first.")
}

# A run that fails in a later job leaves its earlier result in place.
jobs <- table(runs$job)
cat(
  "Runs per job: ",
  paste(jobs, "from job", names(jobs), collapse = ", "),
  "\n",
  sep = ""
)

missing <- planned[!wanted %in% done]
if (length(missing) > 0) {
  message(
    "No results for threshold and seed: ",
    toString(missing),
    ". `sc-starter status` shows why."
  )
}

# One line per threshold: mean over the seeds.
summary <- aggregate(
  cbind(like_start, like_end, rounds, settled) ~ threshold,
  data = runs,
  FUN = mean
)
names(summary)[names(summary) == "settled"] <- "share_settled"
print(round(summary, 2), row.names = FALSE)

# The figure: the share of like neighbours at the end against the wish.
png("results/segregation.png", width = 800, height = 560)
par(col.axis = "#5f5e5a", col.lab = "#2b2b29", fg = "#9a9992")
plot(
  summary$threshold,
  summary$like_end,
  type = "n",
  xlim = c(0, 1),
  ylim = c(0, 1),
  xlab = "Share of like neighbours each person wants",
  ylab = "Share of like neighbours at the end",
  main = "Schelling's town: mild wishes, strong segregation"
)
# What people ask for, and where the town starts.
abline(0, 1, lty = 2, col = "#9a9992")
start <- mean(runs$like_start)
abline(h = start, lty = 3, col = "#9a9992")
text(0.85, 0.82, "what people want", col = "#5f5e5a", pos = 4, cex = 0.9)
text(0.02, start, "at the start", col = "#5f5e5a", pos = 3, cex = 0.9)
# Each seed as a small point, the mean over seeds as the line.
points(runs$threshold, runs$like_end, pch = 16, cex = 0.7, col = "#86b6ef")
lines(summary$threshold, summary$like_end, lwd = 2, col = "#2a78d6")
points(
  summary$threshold,
  summary$like_end,
  pch = 19,
  cex = 1.4,
  col = "#2a78d6"
)
invisible(dev.off())
cat("Wrote results/segregation.png\n")
