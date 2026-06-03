# Lite Hold'em AI

`lite-holdem-ai` is a Python package for experimenting with agents in a simplified 20-card heads-up Texas Hold'em-style poker game.

The project includes a playable game engine, environment wrapper, baseline agents, equity-based agents, match evaluation, tournament evaluation, CSV export, and diagnostic summaries for comparing agent behaviour.

This package is intended as a bridge between small imperfect-information games like Leduc poker and larger poker AI projects.

---

## Features

* 20-card Lite Hold'em deck
* Heads-up two-player poker
* Private cards and public board cards
* Multiple betting streets
* Fixed action set:

  * `FOLD`
  * `CHECK_CALL`
  * `BET_RAISE`
* Hand evaluator
* Game state and environment wrapper
* Baseline agents:

  * `RandomAgent`
  * `PassiveAgent`
  * `AggressiveAgent`
  * `HeuristicAgent`
* Equity-based agents:

  * `EquityAgent`
  * `BucketEquityAgent`
* Match runner
* Tournament runner
* Payoff matrix generation
* CSV export for tournament results
* Agent style diagnostics:

  * VPIP-style rate
  * aggression rate
  * fold/call/raise response when facing a bet
  * showdown rate
  * fold rate
  * terminal street counts
  * action counts by street
  * action counts by agent
* Pytest test suite

---

## Project structure

```text
LiteHoldemPoker/
├── pyproject.toml
├── README.md
├── .gitignore
│
├── examples/
│   ├── README.md
│   ├── baseline_tournament.py
│   ├── equity_tournament.py
│   ├── bucket_equity_tournament.py
│   ├── equity_vs_random.py
│   ├── random_vs_random.py
│   └── heuristic_vs_aggressive.py
│
├── src/
│   └── lite_holdem_ai/
│       ├── __init__.py
│       ├── data/
│       ├── game/
│       ├── agents/
│       └── evaluation/
│
├── tests/
└── results/
```

---

## Installation

From the project root, install the package in editable mode:

```powershell
py -m pip install -e ".[dev]"
```

Editable mode means changes inside `src/lite_holdem_ai/` are picked up immediately without reinstalling the package.

---

## Running tests

Run the full test suite:

```powershell
py -m pytest
```

The tests cover:

* package imports
* actions
* deck behaviour
* hand evaluation
* game state transitions
* environment behaviour
* baseline agents
* heuristic agent behaviour
* equity agent behaviour
* bucket equity agent behaviour
* match running
* tournament running
* tournament CSV export

---

## Quick example: random vs random

```python
from lite_holdem_ai import LiteHoldemEnv, MatchRunner, RandomAgent


runner = MatchRunner(
    env_factory=lambda: LiteHoldemEnv(),
    agents=[
        RandomAgent(seed=1, name="Random A"),
        RandomAgent(seed=2, name="Random B"),
    ],
)

result = runner.play_many(hands_per_seat=1000, swap_seats=True)
result.print_summary()
```

---

## Running a baseline tournament

To compare the baseline agents:

```powershell
py examples\baseline_tournament.py
```

This runs a tournament between:

* Random
* Passive
* Aggressive
* Heuristic

The output includes a payoff matrix and agent rankings.

Each table entry is the average payoff for the row agent against the column agent.

---

## Running an equity tournament

To compare the equity-based agent against the baseline agents:

```powershell
py examples\equity_tournament.py
```

This usually includes:

* Random
* Passive
* Aggressive
* Heuristic
* Equity

The `EquityAgent` estimates exact equity from the current private cards and public board. Preflop equity is loaded from a cached lookup table.

---

## Running a bucket equity tournament

To compare the bucketed equity agent against all current agents:

```powershell
py examples\bucket_equity_tournament.py
```

This usually includes:

* Random
* Passive
* Aggressive
* Heuristic
* Equity
* Bucket Equity

The `BucketEquityAgent` uses the same equity calculation as `EquityAgent`, but maps equity into coarse buckets before choosing an action:

```text
0 = trash
1 = weak
2 = medium
3 = strong
4 = premium
```

This makes it easier to compare smooth equity-based decisions against simpler rule-based equity bands.

---

## Running a detailed match

For a detailed head-to-head summary:

```powershell
py examples\heuristic_vs_aggressive.py
```

This prints diagnostics such as:

* total payoff
* average payoff
* standard error
* 95% confidence interval
* fold/showdown rates
* terminal street counts
* average pot sizes
* agent aggression rates
* action counts by street
* action counts by agent

---

## Agents

### RandomAgent

Selects randomly from legal actions.

### PassiveAgent

Prefers checking and calling.

### AggressiveAgent

Prefers betting and raising when available.

### HeuristicAgent

Uses a rough hand-strength score based on:

* private card quality
* pairs/trips/quads
* straights
* flushes
* full houses
* private-card involvement
* draw potential
* pot odds

The heuristic is not exact equity. It is a fast rule-based baseline.

### EquityAgent

Calculates exact hand equity against all possible opponent hands and future boards.

For preflop decisions, it uses a cached lookup table. For flop, turn, and river decisions, it enumerates remaining possibilities directly.

### BucketEquityAgent

Reuses the equity calculation from `EquityAgent`, then converts equity into a discrete bucket before acting.

This gives a simpler and more interpretable strategy than continuous equity thresholds.

---

## Evaluation tools

### MatchRunner

Runs head-to-head matches between two agents.

```python
from lite_holdem_ai import LiteHoldemEnv, MatchRunner


runner = MatchRunner(
    env_factory=lambda: LiteHoldemEnv(),
    agents=[agent_a, agent_b],
)

result = runner.play_many(hands_per_seat=1000, swap_seats=True)
result.print_summary()
```

### TournamentRunner

Runs pairwise matches between multiple agents and produces a payoff table.

```python
result = tournament_runner.run(
    hands_per_seat=1000,
    include_self_play=False,
)

result.print_payoff_table()
result.print_rankings()
```

### CSV export

Tournament results can be exported:

```python
result.to_csv("results/bucket_equity_tournament.csv")
```

---

## Current status

Implemented:

* 20-card Lite Hold'em game engine
* hand evaluator
* environment wrapper
* baseline agents
* exact equity agent
* bucketed equity agent
* match evaluation
* tournament evaluation
* diagnostic summaries
* CSV export
* test suite
* example scripts

Future improvements could include:

* stronger heuristic tuning
* configurable equity thresholds
* command-line interface
* 52-card Hold'em version
* learning-based agents
* CFR with abstraction
* neural equity approximation

---

## Notes

This is not full no-limit Texas Hold'em. It is a simplified 20-card heads-up fixed-action poker environment designed for experimentation and agent evaluation.

The project is intended as a stepping stone toward larger poker AI systems.
