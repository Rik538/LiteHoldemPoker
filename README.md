# Lite Hold'em AI

`lite-holdem-ai` is a Python package for experimenting with agents in a simplified 20-card heads-up Texas Hold'em-style poker game.

The project includes a playable game engine, environment wrapper, baseline agents, equity-based agents, cached equity agents, bucketed CFR training, match evaluation, tournament evaluation, CSV export, and diagnostic summaries for comparing poker agents.

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
* Exact equity agents:

  * `EquityAgent`
  * `BucketEquityAgent`
* Cached equity agents:

  * `CachedEquityAgent`
  * `CachedBucketEquityAgent`
* SQLite equity cache
* Full equity cache builder
* Bucketed CFR trainer
* CFR playing agent
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
├── cache/
│   └── equity_cache.sqlite
│
├── checkpoints/
│   └── lite_holdem_cfr_*.pkl
│
├── examples/
│   ├── README.md
│   ├── baseline_tournament.py
│   ├── equity_tournament.py
│   ├── bucket_equity_tournament.py
│   ├── cached_equity_tournament.py
│   ├── build_equity_cache.py
│   ├── train_cfr.py
│   ├── cfr_vs_random.py
│   ├── cfr_tournament.py
│   ├── equity_vs_random.py
│   ├── random_vs_random.py
│   └── heuristic_vs_aggressive.py
│
├── src/
│   └── lite_holdem_ai/
│       ├── __init__.py
│       ├── agents/
│       ├── cfr/
│       ├── data/
│       ├── equity/
│       ├── evaluation/
│       └── game/
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

Run the normal test suite:

```powershell
py -m pytest
```

The normal test suite is designed to be fast. It does not rebuild the full SQLite equity cache or run the slow exhaustive cache completeness check unless explicitly enabled.

The tests cover:

* package imports
* actions
* deck behaviour
* hand evaluation
* game state transitions
* environment behaviour
* baseline agents
* heuristic agent behaviour
* exact equity agents
* bucket equity agents
* SQLite equity cache behaviour
* equity cache builder behaviour
* cached equity agents
* CFR infoset key building
* CFR nodes
* CFR trainer
* CFR agent
* match running
* tournament running
* CSV export

---

## Full equity cache validation

The full equity cache contains every legal combination of:

* private cards
* public board cards
* board sizes: preflop, flop, turn, river

For a 20-card deck, the full cache contains:

```text
Preflop:      190
Flop:     155,040
Turn:     581,400
River:  1,627,920
Total:  2,364,550
```

The full cache completeness test is intentionally slow and should be run manually:

```powershell
$env:RUN_FULL_CACHE_TESTS="1"
py -m pytest tests\test_cache_completeness.py
Remove-Item Env:\RUN_FULL_CACHE_TESTS
```

---

## Building the equity cache

To build the SQLite equity cache:

```powershell
py examples\build_equity_cache.py
```

The cache is written to:

```text
cache/equity_cache.sqlite
```

The cache is generated data and is ignored by Git by default.

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

Each table entry is the average payoff for the row agent against the column agent.

---

## Running an equity tournament

To compare the exact equity-based agent against the baseline agents:

```powershell
py examples\equity_tournament.py
```

This usually includes:

* Random
* Passive
* Aggressive
* Heuristic
* Equity

The `EquityAgent` calculates exact equity from the current private cards and public board. This is useful as a reference implementation, but it is slower than cached lookup.

---

## Running a bucket equity tournament

To compare the bucketed equity agent:

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

The `BucketEquityAgent` uses exact equity, then maps equity into coarse buckets before choosing an action:

```text
0 = trash
1 = weak
2 = medium
3 = strong
4 = premium
```

---

## Running a cached equity tournament

To compare cached and non-cached equity agents:

```powershell
py examples\cached_equity_tournament.py
```

This usually includes:

* Random
* Passive
* Aggressive
* Heuristic
* Equity
* Bucket Equity
* Cached Equity
* Cached Bucket Equity

The cached agents use the SQLite cache instead of calculating equity during gameplay.

---

## Training CFR

This project includes a bucketed CFR trainer using an equity-bucket information set abstraction.

The current CFR infoset key contains:

```text
player
street
equity bucket
position
facing-bet flag
raises this round
street betting history
```

To train a small CFR checkpoint:

```powershell
py examples\train_cfr.py
```

The checkpoint is written to:

```text
checkpoints/lite_holdem_cfr_1k.pkl
```

Checkpoints are generated data and are ignored by Git by default.

---

## Evaluating CFR

To run CFR against a random agent:

```powershell
py examples\cfr_vs_random.py
```

To run a tournament including CFR:

```powershell
py examples\cfr_tournament.py
```

Typical agents in the CFR tournament:

* Random
* Passive
* Aggressive
* Heuristic
* Cached Equity
* Cached Bucket
* CFR

CFR checkpoints are trained using the same shared infoset builder that the CFR playing agent uses. This ensures that the key used during training matches the key used during play.

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

This is useful as a reference implementation, but it can be slower than cached lookup.

### BucketEquityAgent

Reuses exact equity calculation, then converts equity into a discrete bucket before acting.

This gives a simpler and more interpretable strategy than continuous equity thresholds.

### CachedEquityAgent

Looks up exact equity from the SQLite cache instead of calculating it during gameplay.

This is the preferred fast equity-based agent once the full cache has been built.

### CachedBucketEquityAgent

Looks up both equity and bucket values from the SQLite cache.

This is the preferred fast bucketed equity agent once the full cache has been built.

### CFRAgent

Uses average strategies learned by `CFRTrainer`.

The CFR agent uses the same infoset key builder as the trainer, so trained strategies and runtime decisions remain aligned.

---

## Equity cache tools

### EquityCache

SQLite-backed storage for equity results.

Each record stores:

* private card key
* public board key
* board size
* equity
* bucket
* wins
* losses
* splits
* total scenarios

### EquityCacheBuilder

Builds exact equity records for:

* preflop
* flop
* turn
* river

The full build is expensive but only needs to be done once.

---

## CFR tools

### CFRNode

Stores cumulative regrets and cumulative strategy sums for the fixed action set:

* `FOLD`
* `CHECK_CALL`
* `BET_RAISE`

### InfosetKeyBuilder

Shared abstraction layer for CFR training and CFR playing.

The current implementation is `EquityBucketInfosetKeyBuilder`.

### CFRTrainer

Trains a bucketed CFR strategy using sampled deals and the shared infoset abstraction.

### CFRAgent

Plays from trained CFR nodes using average strategy.

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
result.to_csv("results/cfr_tournament.csv")
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
* SQLite equity cache
* full equity cache builder
* cached equity agent
* cached bucket equity agent
* bucketed CFR trainer
* CFR playing agent
* match evaluation
* tournament evaluation
* diagnostic summaries
* CSV export
* test suite
* example scripts

Future improvements could include:

* external-sampling MCCFR
* stronger CFR abstraction
* pot-size bucket features
* best-response / exploitability estimates
* configurable equity thresholds
* command-line interface
* 52-card Hold'em version
* learning-based agents
* neural equity approximation

---

## Notes

This is not full no-limit Texas Hold'em. It is a simplified 20-card heads-up fixed-action poker environment designed for experimentation and agent evaluation.

The project is intended as a stepping stone toward larger poker AI systems.
