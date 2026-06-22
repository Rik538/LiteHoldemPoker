# Examples

This folder contains runnable examples for training, benchmarking, and evaluating Lite Hold'em agents.

Run examples from the project root:

```powershell
py examples\<example_name>.py
```

Some examples require generated files such as the SQLite equity cache or trained CFR/MCCFR checkpoints. These files are intentionally not tracked by Git.

Generated folders:

```text
cache/
checkpoints/
results/
```

---

## Basic match examples

| Example | Purpose |
|---|---|
| `random_vs_random.py` | Sanity-checks the environment using two random agents. |
| `heuristic_vs_random.py` | Tests the heuristic agent against a random baseline. |
| `heuristic_vs_aggressive.py` | Compares two simple rule-based agents. |
| `equity_vs_random.py` | Tests the exact equity agent against random play. |
| `cfr_vs_random.py` | Tests a trained CFR agent against random play. |

---

## Tournament examples

| Example | Purpose |
|---|---|
| `baseline_tournament.py` | Runs a tournament between Random, Passive, Aggressive, and Heuristic agents. |
| `equity_tournament.py` | Evaluates the exact equity agent against baseline agents. |
| `bucket_equity_tournament.py` | Evaluates the bucketed equity agent. |
| `cached_equity_tournament.py` | Evaluates SQLite-backed cached equity agents. |
| `cfr_tournament.py` | Runs a tournament including a trained CFR agent. |
| `cfr_scaling_tournament.py` | Compares CFR agents trained for different iteration counts. |
| `mccfr_scaling_tournament.py` | Compares MCCFR agents trained for different iteration counts. |
| `mccfr_repeated_tournament.py` | Runs repeated tournament evaluation for MCCFR agents. |
| `repeated_tournament.py` | Demonstrates repeated tournament evaluation and confidence intervals. |
| `abstraction_experiment_tournament.py` | Compares different infoset abstraction variants. |
| `multiseed_mccfr_tournament.py` | Evaluates MCCFR checkpoints trained with different RNG seeds. |

---

## Training examples

| Example | Purpose |
|---|---|
| `train_cfr.py` | Trains a bucketed CFR agent. |
| `train_mccfr.py` | Trains an external-sampling MCCFR agent. |
| `train_delayed_mccfr.py` | Trains MCCFR with delayed average-strategy accumulation. |
| `train_multiseed_mccfr.py` | Trains several MCCFR checkpoints with different RNG seeds. |
| `benchmark_training.py` | Benchmarks training speed for different MCCFR/infoset configurations. |

---

## Equity cache examples

| Example | Purpose |
|---|---|
| `build_equity_cache.py` | Builds the SQLite equity cache used by cached equity agents and CFR abstractions. |

The full equity cache can be large and should remain untracked.

---

## Recommended setup order

A typical fresh setup is:

```powershell
py -m pip install -e ".[dev]"
py -m pytest
py examples\build_equity_cache.py
```

After the cache exists, cached equity agents and CFR/MCCFR infoset builders can use it.

---

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

This is the preferred evaluation method for comparing CFR/MCCFR checkpoints, abstraction variants, and training-method variants.

---

## Abstraction experiment examples

The abstraction experiment scripts compare MCCFR agents trained with different infoset key builders.

Abstractions tested so far include:

| Abstraction | Description |
|---|---|
| Equity bucket | Uses coarse hand-equity buckets. |
| Pot bucket | Adds a coarse pot-size bucket. |
| Street-aware equity bucket | Uses different equity thresholds on preflop, flop, turn, and river. |
| Street-aware pot bucket | Combines street-aware equity buckets with pot-size context. |
| No-history variant | Removes exact current-street action history. |
| 7-bucket variant | Tests finer street-aware equity resolution. |

Current findings:

- Street-aware equity thresholds gave the largest abstraction improvement.
- Pot bucket improved the street-aware abstraction.
- Removing street history did not clearly hurt performance.
- The 7-bucket variant was viable but did not clearly beat the simpler 5-bucket street-aware version.

---

## Delayed MCCFR example

`train_delayed_mccfr.py` trains MCCFR while delaying average-strategy accumulation.

This changes when `strategy_sum` starts accumulating, while keeping regret updates active from the start.

Example:

```python
trainer.train(
    iterations=100_000,
    path="checkpoints/lite_holdem_nohist_100k_avg75k.pkl",
    average_starting_iteration=75_000,
)
```

Recent repeated evaluation showed delayed averaging may give small improvements at 100k iterations, but longer training remained stronger.

---

## Multi-seed MCCFR examples

`train_multiseed_mccfr.py` trains several independent MCCFR checkpoints using the same settings but different RNG seeds.

Example output checkpoints:

```text
lite_holdem_nohist_500k_seed1.pkl
lite_holdem_nohist_500k_seed2.pkl
lite_holdem_nohist_500k_seed3.pkl
lite_holdem_nohist_500k_seed4.pkl
lite_holdem_nohist_500k_seed5.pkl
```

`multiseed_mccfr_tournament.py` evaluates those checkpoints against each other, a cached bucket baseline, and existing longer-training checkpoints.

The goal is to measure seed variance and determine whether best-of-N checkpoint selection can match or beat longer single-seed training.

Current findings:

- 500k seed checkpoints varied noticeably in strength.
- Best-of-5 500k selection produced a checkpoint competitive with a 1M checkpoint.
- Seed averaging was viable but did not outperform the strongest 1M single-run checkpoint.

---

## Seed-averaged checkpoint examples

Seed-averaged checkpoints are created by loading compatible checkpoints, summing their `strategy_sum` values, and saving a new combined checkpoint.

Compatible checkpoints must use the same infoset builder and game settings.

The resulting checkpoint can be evaluated with the normal `CFRAgent` and repeated tournament runner.

---

## Typical workflows

### Baseline tournament

```powershell
py examples\baseline_tournament.py
```

### Build cache and run cached equity tournament

```powershell
py examples\build_equity_cache.py
py examples\cached_equity_tournament.py
```

### Train and evaluate MCCFR

```powershell
py examples\train_mccfr.py
py examples\mccfr_repeated_tournament.py
```

### Train delayed MCCFR

```powershell
py examples\train_delayed_mccfr.py
```

### Train and evaluate multiple seeds

```powershell
py examples\train_multiseed_mccfr.py
py examples\multiseed_mccfr_tournament.py
```

### Compare abstractions

```powershell
py examples\abstraction_experiment_tournament.py
```

---

## Before committing example changes

```powershell
py -m pytest
git status
git add README.md examples\README.md
git commit -m "Update documentation for MCCFR multiseed experiments"
git push
```
