# Lite Hold'em AI

`lite-holdem-ai` is a Python package for experimenting with agents in a simplified 20-card heads-up Texas Hold'em-style poker game.

The project includes a playable game engine, environment wrapper, baseline agents, equity-based agents, cached equity agents, bucketed CFR, external-sampling MCCFR, repeated tournament evaluation, CSV export, and diagnostic summaries for comparing poker agents.

This package is intended as a bridge between small imperfect-information games like Leduc poker and larger poker AI projects.

---

## Features

* 20-card Lite Hold'em deck
* Heads-up two-player poker
* Private cards and public board cards
* Multiple betting streets
* Fixed-limit style action set:

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
* External-sampling MCCFR trainer
* CFR/MCCFR playing agent
* Pluggable infoset abstraction builders
* Repeated tournament evaluation with confidence intervals
* Match runner
* Tournament runner
* Payoff matrix generation
* CSV export for tournament and repeated tournament results
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
├── cache/                      # generated, ignored by Git
│   └── equity_cache.sqlite
│
├── checkpoints/                # generated, ignored by Git
│   ├── lite_holdem_cfr_*.pkl
│   └── lite_holdem_mccfr_*.pkl
│
├── examples/
│   ├── README.md
│   ├── abstraction_experiment_tournament.py
│   ├── baseline_tournament.py
│   ├── benchmark_training.py
│   ├── bucket_equity_tournament.py
│   ├── build_equity_cache.py
│   ├── cached_equity_tournament.py
│   ├── cfr_scaling_tournament.py
│   ├── cfr_tournament.py
│   ├── cfr_vs_random.py
│   ├── equity_tournament.py
│   ├── equity_vs_random.py
│   ├── heuristic_vs_aggressive.py
│   ├── heuristic_vs_random.py
│   ├── mccfr_repeated_tournament.py
│   ├── mccfr_scaling_tournament.py
│   ├── random_vs_random.py
│   ├── repeated_tournament.py
│   ├── train_cfr.py
│   └── train_mccfr.py
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
└── results/                    # generated, ignored by Git
```

Generated files in `cache/`, `checkpoints/`, and `results/` should not be committed.

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
* external-sampling MCCFR trainer
* repeated tournament evaluation
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

## Running examples

Run examples from the project root:

```powershell
py examples\baseline_tournament.py
```

The examples folder includes scripts for:

* basic head-to-head matches
* baseline tournaments
* exact equity and bucket equity tournaments
* cached equity tournaments
* CFR training and evaluation
* MCCFR training and evaluation
* repeated tournament evaluation
* abstraction experiments
* training speed benchmarks

See `examples/README.md` for the full examples list.

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

## Running equity tournaments

To compare the exact equity-based agent against the baseline agents:

```powershell
py examples\equity_tournament.py
```

To compare the bucketed equity agent:

```powershell
py examples\bucket_equity_tournament.py
```

To compare cached and non-cached equity agents:

```powershell
py examples\cached_equity_tournament.py
```

The cached agents use the SQLite cache instead of calculating equity during gameplay.

---

## Training CFR

This project includes a bucketed CFR trainer using an equity-bucket information set abstraction.

The original CFR infoset key contains:

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

## Training external-sampling MCCFR

This project also includes an external-sampling MCCFR trainer.

External-sampling MCCFR is faster than the full CFR trainer because:

* the traversing player explores all legal actions
* opponent actions are sampled
* initial deals are sampled
* bucket/equity lookups can be memoised in memory

To train an MCCFR checkpoint:

```powershell
py examples\train_mccfr.py
```

The MCCFR trainer uses the same infoset abstraction as the CFR agent, so the resulting checkpoint can be played by the same `CFRAgent`.

The recommended training setup uses:

* `CachedEquityBucketProvider`
* `MemoizedBucketProvider`
* an `InfosetKeyBuilder`
* `MCCFRTrainer`

The memoised bucket provider avoids repeated SQLite lookups during training and gives a significant training speedup.

---

## CFR/MCCFR infoset abstraction

The project now supports pluggable infoset key builders. This allows different abstractions to be trained and evaluated without rewriting the CFR/MCCFR trainer.

Abstractions tested so far include:

| Abstraction | Description |
|---|---|
| Equity bucket | Coarse hand-equity bucket. |
| Pot bucket | Adds coarse pot-size context. |
| Street-aware equity bucket | Uses different equity thresholds on preflop, flop, turn, and river. |
| Street-aware pot bucket | Combines street-aware equity thresholds with pot-size context. |
| No-history variant | Removes exact current-street action history from the key. |
| 7-bucket variant | Tests finer street-aware equity resolution. |

The strongest confirmed abstraction family so far is the street-aware pot-bucket family.

A representative strong infoset key is:

```text
player
street
street-aware equity bucket
pot bucket
position
facing-bet flag
raises this round
```

The abstraction experiments suggest:

* Street-aware equity thresholds are a major improvement over global equity buckets.
* Adding pot bucket improves the street-aware abstraction.
* Exact street action history appears to be mostly redundant once `facing_bet`, `raises_this_round`, `position`, `pot_bucket`, and street-aware equity are included.
* Increasing from 5 to 7 street-aware equity buckets is viable, but has not clearly outperformed the simpler 5-bucket version in focused evaluation.

---

## Evaluating CFR and MCCFR

To run CFR against a random agent:

```powershell
py examples\cfr_vs_random.py
```

To run a tournament including CFR:

```powershell
py examples\cfr_tournament.py
```

To compare CFR scaling:

```powershell
py examples\cfr_scaling_tournament.py
```

To compare MCCFR scaling:

```powershell
py examples\mccfr_scaling_tournament.py
```

To run repeated MCCFR evaluation:

```powershell
py examples\mccfr_repeated_tournament.py
```

To compare abstraction variants:

```powershell
py examples\abstraction_experiment_tournament.py
```

Typical agents in the CFR/MCCFR tournaments:

* Heuristic
* Cached Equity
* Cached Bucket
* CFR
* MCCFR
* MCCFR abstraction variants

CFR and MCCFR checkpoints are trained using the same shared infoset builder that the CFR playing agent uses. This ensures that the key used during training matches the key used during play.

---

## Repeated tournament evaluation

Single tournaments can be noisy. The preferred evaluation method is now repeated tournament evaluation.

`RepeatedTournamentRunner` runs multiple independent tournaments and aggregates the payoff tables. It reports:

* mean score
* standard deviation
* standard error
* 95% confidence interval

Example ranking format:

```text
Rankings:
1. Street Aware 500k: 0.0734 ± 0.0188 (n=20)
2. 7 Bucket 500k:     0.0307 ± 0.0201 (n=20)
3. CachedBucket:     -0.1042 ± 0.0241 (n=20)
```

This is the preferred way to compare CFR/MCCFR checkpoints and abstraction variants.

Repeated tournament results can be exported:

```python
result.to_csv("results/repeated_abstraction_benchmark.csv")
```

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

Uses average strategies learned by `CFRTrainer` or `MCCFRTrainer`.

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

Shared abstraction layer for CFR/MCCFR training and CFR playing.

The current strongest abstractions use street-aware equity buckets and pot buckets.

### CachedEquityBucketProvider

Gets equity buckets from the SQLite equity cache.

### MemoizedBucketProvider

Wraps another bucket provider and caches bucket/equity lookups in memory.

This is useful for CFR and MCCFR training because infoset generation calls the bucket provider very frequently.

### CFRTrainer

Trains a bucketed CFR strategy using sampled deals and the shared infoset abstraction.

### MCCFRTrainer

Trains a bucketed strategy using external-sampling MCCFR.

### CFRAgent

Plays from trained CFR/MCCFR nodes using average strategy.

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

### RepeatedTournamentRunner

Runs multiple tournaments and aggregates the results.

```python
runner = RepeatedTournamentRunner(
    agent_factory=make_agents,
    env_factory=lambda: LiteHoldemEnv(),
)

result = runner.run(
    hands_per_seat=5000,
    include_self_play=False,
    number_tournaments=20,
)

result.print_mean_table()
result.print_rankings()
```

`agent_factory(seed)` should create fresh agents for each repeated tournament run. This avoids reusing stale agent state, open cache connections, or random number generators.

### CSV export

Tournament and repeated tournament results can be exported:

```python
result.to_csv("results/tournament.csv")
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
* external-sampling MCCFR trainer
* CFR/MCCFR playing agent
* pluggable infoset key builders
* repeated tournament evaluation
* match evaluation
* tournament evaluation
* diagnostic summaries
* CSV export
* test suite
* example scripts
* abstraction experiment scripts

Current experimental findings:

* Street-aware equity abstraction is the strongest improvement found so far.
* Street-aware pot-bucket MCCFR agents outperform earlier global-equity-bucket and pot-bucket-only variants.
* The no-history variant appears competitive, suggesting exact street action history is not essential in the current abstraction.
* The 7-bucket variant is viable but has not clearly beaten the simpler 5-bucket street-aware abstraction.
* Repeated tournament evaluation is now used for more reliable comparisons.

Future improvements could include:

* delayed average-strategy accumulation
* multi-seed MCCFR training
* checkpoint selection across training stages
* strategy averaging across compatible checkpoints
* approximate best-response / exploitability estimates
* action-frequency diagnostics by street and equity bucket
* configurable abstraction settings
* command-line interface
* short-deck or 52-card limit Hold'em version
* learning-based agents
* neural equity approximation

---

## Development notes

Before committing:

```powershell
py -m pytest
git status
```

Generated files should remain untracked:

```text
cache/
checkpoints/
results/
*.sqlite
*.sqlite3
*.db
*.pkl
```

Suggested commit for this branch:

```powershell
git add README.md examples\README.md
git commit -m "Update documentation for MCCFR abstraction experiments"
```

A sensible next branch is training-method improvement, for example:

```powershell
git checkout main
git pull
git checkout -b feature/mccfr-training-methods
```

---

## Notes

This is not full no-limit Texas Hold'em. It is a simplified 20-card heads-up fixed-action poker environment designed for experimentation and agent evaluation.

The project is intended as a stepping stone toward larger poker AI systems.
