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

Runs a tournament including both equity-based agents.

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

This is the main benchmark for comparing the continuous equity strategy against the bucketed equity strategy.

The result is also exported to:

```text
results/bucket_equity_tournament.csv
```

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

For equity-agent benchmarking:

```powershell
py examples\equity_tournament.py
```

For bucket-equity benchmarking:

```powershell
py examples\bucket_equity_tournament.py
```

---

## Development note

After changing package code, run the full test suite from the project root:

```powershell
py -m pytest
```

Generated CSV files are written to the `results/` folder.
