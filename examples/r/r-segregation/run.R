# One run of Schelling's segregation model.
#
# Usage: Rscript run.R <threshold> <seed>
#   threshold: the share of like neighbours each person wants, 0 to 1
#   seed: the random number seed, so that a run can be repeated exactly
# Writes results/run-<threshold>-<seed>.csv and, for seed 1, a picture of
# the grid at the end, results/grid-<threshold>.png. Needs only base R.

# The wish and the seed, from the command line: Rscript run.R 0.3 2.
args <- commandArgs(trailingOnly = TRUE)
threshold <- as.numeric(args[1])
seed <- as.integer(args[2])
if (length(args) != 2 || is.na(threshold) || is.na(seed)) {
  stop("Usage: Rscript run.R <threshold> <seed>")
}

size <- 50 # the town is a grid of size x size places
vacant <- 0.1 # share of empty places
max_rounds <- 200 # stop here if people are still moving

# Shift a matrix by dr rows and dc columns; places shifted in are 0.
shift <- function(m, dr, dc) {
  out <- matrix(0, nrow(m), ncol(m))
  rows <- max(1, 1 + dr):min(nrow(m), nrow(m) + dr)
  cols <- max(1, 1 + dc):min(ncol(m), ncol(m) + dc)
  out[rows, cols] <- m[rows - dr, cols - dc]
  out
}

# For every place, how many of its 8 neighbours belong to `group`.
neighbours <- function(grid, group) {
  member <- (grid == group) * 1
  count <- 0
  for (dr in -1:1) {
    for (dc in -1:1) {
      if (dr != 0 || dc != 0) count <- count + shift(member, dr, dc)
    }
  }
  count
}

# For every person, the share of like people among their neighbours;
# NA for empty places. Someone without neighbours counts as content.
like_share <- function(grid) {
  group_1 <- neighbours(grid, 1)
  group_2 <- neighbours(grid, 2)
  same <- ifelse(grid == 1, group_1, group_2)
  share <- ifelse(group_1 + group_2 > 0, same / (group_1 + group_2), 1)
  share[grid == 0] <- NA
  share
}

set.seed(seed)
# 0 is an empty place; 1 and 2 are the two groups, equally large, placed
# at random.
people <- round(size^2 * (1 - vacant))
places <- c(rep(1:2, length.out = people), rep(0, size^2 - people))
grid <- matrix(sample(places), size, size)
like_start <- mean(like_share(grid), na.rm = TRUE)

# Let unhappy people move, round by round, until all are content.
rounds <- 0
repeat {
  share <- like_share(grid)
  unhappy <- which(!is.na(share) & share < threshold)
  if (length(unhappy) == 0 || rounds == max_rounds) {
    break
  }
  # Every unhappy person moves to a random empty place at once; the places
  # they leave are free in the next round.
  empty <- which(grid == 0)
  movers <- unhappy[sample.int(length(unhappy))]
  moves <- min(length(movers), length(empty))
  targets <- empty[sample.int(length(empty), moves)]
  movers <- movers[seq_along(targets)]
  grid[targets] <- grid[movers]
  grid[movers] <- 0
  rounds <- rounds + 1
}

# The result of this run, as one row of results/run-<threshold>-<seed>.csv.
result <- data.frame(
  threshold = threshold,
  seed = seed,
  rounds = rounds,
  settled = length(unhappy) == 0,
  like_start = round(like_start, 3),
  like_end = round(mean(share, na.rm = TRUE), 3),
  # So that combine.R can tell results of an earlier job apart.
  job = Sys.getenv("SLURM_ARRAY_JOB_ID")
)
dir.create("results", showWarnings = FALSE)
write.csv(
  result,
  sprintf("results/run-%s-%d.csv", format(threshold), seed),
  row.names = FALSE
)

if (seed == 1) {
  # type = "cairo": R on the cluster has no screen, and its default way of
  # drawing PNG files needs one.
  png(
    sprintf("results/grid-%s.png", format(threshold)),
    width = 480,
    height = 540,
    type = "cairo"
  )
  par(mar = c(4, 1, 3, 1))
  # Blue and orange pass the colour-blindness checks; empty places are light.
  image(
    grid,
    col = c("#ececea", "#2a78d6", "#eb6834"),
    breaks = c(-0.5, 0.5, 1.5, 2.5),
    axes = FALSE,
    asp = 1,
    main = sprintf(
      "Wants %d%% like neighbours: %d%% at the end",
      round(100 * threshold),
      round(100 * result$like_end)
    )
  )
  legend(
    "bottom",
    legend = c("Group 1", "Group 2", "Empty"),
    fill = c("#2a78d6", "#eb6834", "#ececea"),
    horiz = TRUE,
    bty = "n",
    inset = c(0, -0.1),
    xpd = TRUE
  )
  invisible(dev.off())
}

# One line for the output file of the run.
cat(sprintf(
  "Threshold %s, seed %d: %d rounds, like neighbours %.0f%% -> %.0f%%\n",
  format(threshold),
  seed,
  rounds,
  100 * result$like_start,
  100 * result$like_end
))
