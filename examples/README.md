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

## `random_vs_random.py`

Runs a simple random-vs-random match.

Useful as a quick smoke test that the game engine, environment, agents, and match runner are working.

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

## `heuristic_vs_passive.py`

Runs a detailed match between the heuristic agent and passive agent.

This is useful for checking whether the heuristic agent is over-betting, over-calling, or losing value against a calling-heavy opponent.

```powershell
py examples\heuristic_vs_passive.py
```

---

## Recommended order

For a quick check:

```powershell
py examples\random_vs_random.py
```

For a full baseline benchmark:

```powershell
py examples\baseline_tournament.py
```

For detailed diagnostics:

```powershell
py examples\heuristic_vs_aggressive.py
```

---

## Development note

After changing package code, run the test suite from the project root:

```powershell
py -m pytest
```
