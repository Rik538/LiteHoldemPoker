# Examples

This folder contains runnable examples for the `lite_holdem_ai` package.

Run all examples from the project root:

```powershell
py examples\<script_name>.py
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

This is the main v0.4.0 benchmark.

It compares the original exact-calculation equity agents against the SQLite cached equity agents.

The result is usually exported to:

```text
results/cached_equity_tournament.csv
```

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

## `equity_vs_random.py`

Runs a detailed match between the exact equity agent and a random agent.

```powershell
py examples\equity_vs_random.py
```

Useful as a quick check that the equity agent is working and making sensible decisions.

---

## `random_vs_random.py`

Runs a simple random-vs-random match.

Useful as a smoke test that the game engine, environment, agents, and match runner are working.

```powershell
py examples\random_vs_random.py
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

For bucket equity benchmarking:

```powershell
py examples\bucket_equity_tournament.py
```

For cached equity benchmarking:

```powershell
py examples\cached_equity_tournament.py
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
