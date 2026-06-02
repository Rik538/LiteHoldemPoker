# Lite Hold'em AI

`lite-holdem-ai` is a Python package for experimenting with agents in a simplified 20-card heads-up Texas Hold'em-style poker game.

The project includes a playable game engine, environment wrapper, baseline agents, match evaluation, tournament evaluation, and diagnostic summaries for comparing agent behaviour.

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
* Match runner
* Tournament runner
* Payoff matrix generation
* Agent style diagnostics:

  * VPIP-style rate
  * aggression rate
  * fold/call/raise response when facing a bet
  * showdown rate
  * fold rate
  * terminal street counts
* CSV export for tournament results
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
│   ├── random_vs_random.py
│   ├── heuristic_vs_aggressive.py
│   └── heuristic_vs_passive.py
│
├── src/
│   └── lite_holdem_ai/
│       ├── __init__.py
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
* match running
* tournament running

---

## Quick example: random vs random

```python
from lite_holdem_ai.agents.random_agent import RandomAgent
from lite_holdem_ai.evaluation.match import MatchRunner
from lite_holdem_ai.game.environment import LiteHoldemEnv


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

Example format:

```text
                  Random     Passive  Aggressive   Heuristic
Random            0.0000     -0.2170     -6.9315     -4.9575
Passive           0.2170      0.0000      0.3420      0.2685
Aggressive        6.9315     -0.3420      0.0000     -0.8265
Heuristic         4.9575     -0.2685      0.8265      0.0000

Rankings:
1. Aggressive
2. Heuristic
3. Passive
4. Random
```

Each table entry is the average payoff for the row agent against the column agent.

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

---

## Evaluation tools

### MatchRunner

Runs head-to-head matches between two agents.

```python
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
result.to_csv("results/baseline_tournament.csv")
```

---

## Current status

Implemented:

* 20-card Lite Hold'em game engine
* hand evaluator
* environment wrapper
* baseline agents
* match evaluation
* tournament evaluation
* diagnostic summaries
* CSV export
* test suite
* example scripts

Future improvements could include:

* equity-based agent
* Monte Carlo rollout agent
* stronger heuristic tuning
* command-line interface
* 52-card Hold'em version
* learning-based agents

---

## Notes

This is not full no-limit Texas Hold'em. It is a simplified 20-card heads-up fixed-action poker environment designed for experimentation and agent evaluation.

The project is intended as a stepping stone toward larger poker AI systems.
