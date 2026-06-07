# Examples

This folder contains runnable examples for the `lite_holdem_ai` package.

Run all examples from the project root:

```powershell
py examples\<script_name>.py
```

---

## `random_vs_random.py`

Runs a simple random-vs-random match.

Useful as a smoke test that the game engine, environment, agents, and match runner are working.

```powershell
py examples\random_vs_random.py
```

---

## `baseline_tournament.py`

Runs a tournament between the baseline agents:

* Random
* Passive
* Aggressive
* Heuristic

It prints a payoff matrix and rankings.

```powershell
py examples\baseline_tournament.py
```

---

## `equity_vs_random.py`

Runs a detailed match between the exact equity agent and a random agent.

```powershell
py examples\equity_vs_random.py
```

Useful as a quick check that the equity agent is working and making sensible decisions.

---

## `equity_tournament.py`

Runs a tournament including the exact equity agent.

Typical agents:

* Random
* Passive
* Aggressive
* Heuristic
* Equity

```powershell
py examples\equity_tournament.py
```

Use this to check whether `EquityAgent` improves over the rule-based baselines.

---

## `bucket_equity_tournament.py`

Runs a tournament including both exact equity-based agents.

Typical agents:

* Random
* Passive
* Aggressive
* Heuristic
* Equity
* Bucket Equity

```powershell
py examples\bucket_equity_tournament.py
```

This compares continuous equity-threshold decisions against bucketed equity decisions.

---

## `build_equity_cache.py`

Builds the SQLite equity cache used by the cached agents.

```powershell
py examples\build_equity_cache.py
```

The cache is written to:

```text
cache/equity_cache.sqlite
```

The full cache contains all legal private/public card combinations for:

* preflop
* flop
* turn
* river

The full build can take a long time, but only needs to be run when rebuilding the cache.

---

## `cached_equity_tournament.py`

Runs a tournament including the cached equity agents.

Typical agents:

* Random
* Passive
* Aggressive
* Heuristic
* Equity
* Bucket Equity
* Cached Equity
* Cached Bucket Equity

```powershell
py examples\cached_equity_tournament.py
```

This compares the original exact-calculation equity agents against the SQLite cached equity agents.

The result is usually exported to:

```text
results/cached_equity_tournament.csv
```

---

## `train_cfr.py`

Trains a small bucketed CFR checkpoint.

```powershell
py examples\train_cfr.py
```

This uses:

* SQLite equity cache
* `CachedEquityBucketProvider`
* `EquityBucketInfosetKeyBuilder`
* `CFRTrainer`

The checkpoint is usually written to:

```text
checkpoints/lite_holdem_cfr_1k.pkl
```

Checkpoints are generated files and are ignored by Git by default.

---

## `cfr_vs_random.py`

Runs a trained CFR agent against a random agent.

```powershell
py examples\cfr_vs_random.py
```

Run `train_cfr.py` first so that the CFR checkpoint exists.

This example is useful for confirming that:

* the checkpoint loads correctly
* the CFR agent uses the same infoset builder as the trainer
* missing nodes are tracked
* CFR can play through the match runner

---

## `cfr_tournament.py`

Runs a tournament including a trained CFR agent.

Typical agents:

* Random
* Passive
* Aggressive
* Heuristic
* Cached Equity
* Cached Bucket
* CFR

```powershell
py examples\cfr_tournament.py
```

This is the main CFR benchmark example.

It prints:

* payoff matrix
* rankings
* CFR missing-node count

The result is usually exported to:

```text
results/cfr_tournament.csv
```

---

## `train_mccfr.py`

Trains an external-sampling MCCFR checkpoint.

```powershell
py examples\train_mccfr.py
```

This uses:

* SQLite equity cache
* `CachedEquityBucketProvider`
* `MemoizedBucketProvider`
* `EquityBucketInfosetKeyBuilder`
* `MCCFRTrainer`

The memoised bucket provider reduces repeated SQLite lookups during training.

The checkpoint is usually written to:

```text
checkpoints/lite_holdem_mccfr_*.pkl
```

Checkpoints are generated files and are ignored by Git by default.

---

## `mccfr_tournament.py`

Runs a tournament including trained MCCFR agents.

Typical agents:

* Heuristic
* Cached Equity
* Cached Bucket
* CFR
* MCCFR

```powershell
py examples\mccfr_tournament.py
```

This is the main external-sampling MCCFR benchmark example.

It prints:

* payoff matrix
* rankings
* missing-node counts for CFR/MCCFR agents

The result is usually exported to:

```text
results/mccfr_tournament.csv
```

---

## `heuristic_vs_aggressive.py`

Runs a detailed match between the heuristic agent and aggressive agent.

This is useful for inspecting agent behaviour using the full diagnostic summary.

```powershell
py examples\heuristic_vs_aggressive.py
```

---

## Recommended order

For a quick engine check:

```powershell
py examples\random_vs_random.py
```

For a baseline benchmark:

```powershell
py examples\baseline_tournament.py
```

For exact equity-agent benchmarking:

```powershell
py examples\equity_tournament.py
```

For cached equity benchmarking:

```powershell
py examples\cached_equity_tournament.py
```

For CFR:

```powershell
py examples\train_cfr.py
py examples\cfr_vs_random.py
py examples\cfr_tournament.py
```

For MCCFR:

```powershell
py examples\train_mccfr.py
py examples\mccfr_tournament.py
```

---

## Full cache validation

After building the full cache, you can run the slow cache completeness test:

```powershell
$env:RUN_FULL_CACHE_TESTS="1"
py -m pytest tests\test_cache_completeness.py
Remove-Item Env:\RUN_FULL_CACHE_TESTS
```

This checks that every possible legal private/public card combination exists in the SQLite cache.

---

## Development note

After changing package code, run the normal test suite from the project root:

```powershell
py -m pytest
```

Generated CSV files are written to the `results/` folder.

Generated SQLite cache files are written to the `cache/` folder.

Generated CFR/MCCFR checkpoints are written to the `checkpoints/` folder.
