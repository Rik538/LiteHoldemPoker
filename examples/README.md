# Examples

This folder contains runnable examples for training, benchmarking, and evaluating Lite Hold'em agents.

Run examples from the project root:

```powershell
py examples\<example_name>.py
```

Some examples require generated files such as the SQLite equity cache or trained CFR/MCCFR checkpoints. These files are intentionally not tracked by Git.

## Basic match examples

| Example                      | Purpose                                                |
| ---------------------------- | ------------------------------------------------------ |
| `random_vs_random.py`        | Sanity-checks the environment using two random agents. |
| `heuristic_vs_random.py`     | Tests the heuristic agent against a random baseline.   |
| `heuristic_vs_aggressive.py` | Compares two simple rule-based agents.                 |
| `equity_vs_random.py`        | Tests the exact equity agent against random play.      |
| `cfr_vs_random.py`           | Tests a trained CFR agent against random play.         |

## Tournament examples

| Example                                | Purpose                                                                                 |
| -------------------------------------- | --------------------------------------------------------------------------------------- |
| `baseline_tournament.py`               | Runs a tournament between the basic agents: Random, Passive, Aggressive, and Heuristic. |
| `equity_tournament.py`                 | Evaluates the exact equity agent against baseline agents.                               |
| `bucket_equity_tournament.py`          | Evaluates the bucketed equity agent.                                                    |
| `cached_equity_tournament.py`          | Evaluates SQLite-backed cached equity agents.                                           |
| `cfr_tournament.py`                    | Runs a tournament including a trained CFR agent.                                        |
| `cfr_scaling_tournament.py`            | Compares CFR agents trained for different iteration counts.                             |
| `mccfr_scaling_tournament.py`          | Compares MCCFR agents trained for different iteration counts.                           |
| `mccfr_repeated_tournament.py`         | Runs repeated tournament evaluation for MCCFR agents.                                   |
| `repeated_tournament.py`               | Demonstrates repeated tournament evaluation and confidence intervals.                   |
| `abstraction_experiment_tournament.py` | Compares different infoset abstraction variants.                                        |

## Training examples

| Example                 | Purpose                                                               |
| ----------------------- | --------------------------------------------------------------------- |
| `train_cfr.py`          | Trains a bucketed CFR agent.                                          |
| `train_mccfr.py`        | Trains an external-sampling MCCFR agent.                              |
| `benchmark_training.py` | Benchmarks training speed for different MCCFR/infoset configurations. |

## Equity cache examples

| Example                 | Purpose                                                                           |
| ----------------------- | --------------------------------------------------------------------------------- |
| `build_equity_cache.py` | Builds the SQLite equity cache used by cached equity agents and CFR abstractions. |

The full equity cache can be large and should remain untracked. The expected ignored folders are:

```text
cache/
checkpoints/
results/
```

## Repeated tournament evaluation

Repeated tournaments are used to reduce variance. Instead of trusting a single tournament result, the repeated runner executes multiple tournaments and reports:

```text
mean score
standard deviation
standard error
95% confidence interval
```

Example output:

```text
Rankings:
1. Agent A: 0.1234 ± 0.0188 (n=20)
2. Agent B: 0.0421 ± 0.0201 (n=20)
```

This is now the preferred evaluation method for comparing CFR/MCCFR checkpoints and abstraction variants.

## Current abstraction experiments

Several MCCFR infoset abstractions have been tested:

| Abstraction                | Description                                                         |
| -------------------------- | ------------------------------------------------------------------- |
| Equity bucket              | Uses coarse hand-equity buckets.                                    |
| Pot bucket                 | Adds a coarse pot-size bucket.                                      |
| Street-aware equity bucket | Uses different equity thresholds on preflop, flop, turn, and river. |
| Street-aware pot bucket    | Combines street-aware equity buckets with pot-size context.         |
| No-history variant         | Removes exact street action history from the infoset key.           |
| 7-bucket variant           | Tests finer street-aware equity resolution.                         |

The strongest confirmed abstraction so far is the street-aware pot-bucket family. The 7-bucket variant is viable but has not clearly outperformed the simpler 5-bucket street-aware version.

## Typical workflow

```powershell
py examples\build_equity_cache.py
py examples\train_mccfr.py
py examples\abstraction_experiment_tournament.py
```

Before committing example changes:

```powershell
py -m pytest
git status
git add .
git commit -m "Update examples documentation for abstraction experiments"
git push
```
