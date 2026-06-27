# Lite Hold'em AI

`lite-holdem-ai` is a Python package for experimenting with agents in a simplified 20-card heads-up Texas Hold'em-style poker game.

The project includes a playable game engine, environment wrapper, baseline agents, equity-based agents, cached equity agents, bucketed CFR, external-sampling MCCFR, repeated tournament evaluation, infoset abstraction experiments, MCCFR training-method experiments, CSV export, and diagnostic summaries for comparing poker agents.

This package is intended as a bridge between small imperfect-information games like Leduc poker and larger poker AI projects.

---

## Features

- 20-card Lite Hold'em deck
- Heads-up two-player poker
- Private cards and public board cards
- Multiple betting streets
- Fixed action set: `FOLD`, `CHECK_CALL`, `BET_RAISE`
- Hand evaluator
- Game state and environment wrapper
- Baseline agents: `RandomAgent`, `PassiveAgent`, `AggressiveAgent`, `HeuristicAgent`
- Equity agents: `EquityAgent`, `BucketEquityAgent`
- Cached equity agents: `CachedEquityAgent`, `CachedBucketEquityAgent`
- SQLite equity cache and full equity cache builder
- Bucketed CFR trainer
- External-sampling MCCFR trainer
- Delayed average-strategy MCCFR support
- Multi-seed MCCFR training and checkpoint-selection experiments
- Seed-averaged checkpoint experiments
- CFR/MCCFR playing agent
- Pluggable infoset key builders
- Match, tournament, and repeated tournament evaluation
- Payoff matrix generation and CSV export
- Agent style diagnostics
- Pytest test suite

---

## Project structure

```text
LiteHoldemPoker/
├── pyproject.toml
├── README.md
├── .gitignore
├── cache/
├── checkpoints/
├── examples/
│   ├── README.md
│   ├── build_equity_cache.py
│   ├── train_cfr.py
│   ├── train_mccfr.py
│   ├── train_delayed_mccfr.py
│   ├── train_multiseed_mccfr.py
│   ├── multiseed_mccfr_tournament.py
│   ├── abstraction_experiment_tournament.py
│   └── ...
├── src/
│   └── lite_holdem_ai/
│       ├── agents/
│       ├── cfr/
│       ├── equity/
│       ├── evaluation/
│       └── game/
├── tests/
└── results/
```

Generated folders such as `cache/`, `checkpoints/`, and `results/` are intentionally ignored by Git.

---

## Installation

From the project root, install the package in editable mode:

```powershell
py -m pip install -e ".[dev]"
```

---

## Running tests

```powershell
py -m pytest
```

The normal test suite is designed to be fast. It does not rebuild the full SQLite equity cache or run the slow exhaustive cache completeness check unless explicitly enabled.

The tests cover the game engine, agents, equity cache, CFR/MCCFR training, infoset builders, match evaluation, tournament evaluation, repeated tournament evaluation, CSV export, and checkpoint loading.

---

## Full equity cache validation

The full equity cache contains every legal combination of private cards and public board cards for preflop, flop, turn, and river.

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

## Running tournaments

Baseline agents:

```powershell
py examples\baseline_tournament.py
```

Equity agents:

```powershell
py examples\equity_tournament.py
py examples\bucket_equity_tournament.py
py examples\cached_equity_tournament.py
```

CFR/MCCFR checkpoints:

```powershell
py examples\cfr_tournament.py
py examples\mccfr_scaling_tournament.py
```

Each table entry is the average payoff for the row agent against the column agent.

---

## Repeated tournament evaluation

Single tournament results can be noisy. The preferred way to compare stronger agents is repeated tournament evaluation.

The repeated tournament runner performs multiple independent tournament runs and reports:

```text
mean score
standard deviation
standard error
95% confidence interval
```

Example ranking format:

```text
Rankings:
1. No History 1M:              0.0726 ± 0.0206 (n=20)
2. Average Seed 1 to 5 500k:   0.0260 ± 0.0214 (n=20)
3. No History 500k:            0.0215 ± 0.0226 (n=20)
```

Repeated evaluation is used for comparing CFR/MCCFR checkpoints, abstraction variants, and training-method variants.

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

To train a CFR checkpoint:

```powershell
py examples\train_cfr.py
```

Checkpoints are written to `checkpoints/` and ignored by Git by default.

---

## Training external-sampling MCCFR

External-sampling MCCFR is faster than the full CFR trainer because:

- the traversing player explores all legal actions
- opponent actions are sampled
- initial deals are sampled
- bucket lookups can be memoised in memory

Normal MCCFR training:

```powershell
py examples\train_mccfr.py
```

Delayed-averaging MCCFR training:

```powershell
py examples\train_delayed_mccfr.py
```

Multi-seed MCCFR training:

```powershell
py examples\train_multiseed_mccfr.py
```

The MCCFR trainer uses the same infoset abstraction as the CFR playing agent, so trained checkpoints can be played by `CFRAgent`.

The recommended fast setup uses:

- `CachedEquityBucketProvider`
- `MemoizedBucketProvider`
- a chosen `InfosetKeyBuilder`
- `MCCFRTrainer`

---

## Delayed average-strategy experiments

The MCCFR trainer supports delaying average-strategy accumulation while still updating regrets from the first iteration.

```text
regret updates: always from iteration 1
utility diagnostics: always from iteration 1
average strategy accumulation: optionally delayed
```

This is controlled by:

```python
trainer.train(
    iterations=100_000,
    average_start_iteration=75_000,
)
```

Experimental finding:

- Delayed averaging showed small possible gains at 100k iterations.
- The effect was noisy and cutoff-sensitive.
- Longer 500k/1M training remained stronger than delayed 100k training.
- Delayed averaging is useful as an experimental option, but is not currently the default.

---

## Multi-seed training and checkpoint selection

MCCFR training is stochastic. Different seeds can produce different strategies even when the abstraction, iteration count, and training settings are the same.

Multi-seed training means training several independent checkpoints:

```text
NoHistory seed 1 500k
NoHistory seed 2 500k
NoHistory seed 3 500k
NoHistory seed 4 500k
NoHistory seed 5 500k
```

Then repeated tournament evaluation is used to select the strongest checkpoint.

Experimental findings:

- Seed variance exists at both 100k and 500k iterations.
- Best-of-5 seed selection produced a 500k checkpoint competitive with a 1M checkpoint.
- The margins were small relative to evaluation variance, but seed selection was more promising than delayed averaging.

---

## Seed-averaged checkpoints

Compatible checkpoints can be combined by summing their `strategy_sum` arrays into a new checkpoint.

Compatibility requires the same:

- infoset builder
- action mapping
- game rules
- bet sizes
- raise cap

For playing, the important field is `strategy_sum`, because `CFRAgent` uses the node average strategy.

Experimental findings:

- Averaging five 500k seed checkpoints produced a small improvement over the original 500k checkpoint and selected Seed 5 checkpoint in one benchmark.
- The averaged checkpoint did not outperform the 1M checkpoint.
- Averaging only three seeds was weaker, suggesting seed averaging is sensitive to which checkpoints are included.
- For the current Lite Hold'em abstraction, longer single-run training remains the strongest tested option, while seed averaging is useful as a robustness tool.

---

## Infoset abstraction

The project uses pluggable infoset key builders so different abstractions can be compared without rewriting CFR/MCCFR training code.

The main abstraction features tested so far include:

| Feature | Purpose |
|---|---|
| Equity bucket | Groups hands by equity. |
| Street-aware equity bucket | Uses different equity thresholds for preflop, flop, turn, and river. |
| Pot bucket | Adds coarse pot-size context. |
| Position | Distinguishes button/non-button decisions. |
| Facing bet | Records whether the player is currently facing a bet. |
| Raises this round | Records betting pressure. |
| Street history | Encodes exact current-street action sequence. |
| No-history variant | Removes exact street history when redundant. |
| 7-bucket variant | Tests finer street-aware equity resolution. |

The strongest confirmed abstraction family so far is:

```python
(
    player,
    street,
    street_aware_equity_bucket,
    pot_bucket,
    position,
    facing_bet,
    raises_this_round,
)
```

The no-history street-aware pot-bucket variant is currently the preferred abstraction for training-method experiments because it is compact, stable, and competitive.

---

## Abstraction experiment findings

Current experimental findings:

- Street-aware equity thresholds were a major improvement over global equity buckets.
- Adding pot bucket improved the street-aware abstraction.
- Removing street history did not clearly hurt performance, suggesting exact street action history is mostly redundant once facing bet, raises this round, position, pot bucket, and street-aware equity are included.
- Increasing from 5 to 7 street-aware equity buckets was viable, but did not clearly outperform the simpler 5-bucket street-aware version.
- The strongest agents currently come from the street-aware pot-bucket and no-history street-aware pot-bucket MCCFR families.

These findings are based on repeated tournament evaluation rather than single-run results.

---

## Agents

### RandomAgent

Selects randomly from legal actions.

### PassiveAgent

Prefers checking and calling.

### AggressiveAgent

Prefers betting and raising when available.

### HeuristicAgent

Uses a rough hand-strength score based on private-card quality, made hands, draw potential, and pot odds.

### EquityAgent

Calculates exact hand equity against all possible opponent hands and future boards.

### BucketEquityAgent

Reuses exact equity calculation, then converts equity into a discrete bucket before acting.

### CachedEquityAgent

Looks up exact equity from the SQLite cache instead of calculating it during gameplay.

### CachedBucketEquityAgent

Looks up both equity and bucket values from the SQLite cache.

### CFRAgent

Uses average strategies learned by `CFRTrainer` or `MCCFRTrainer`.

The CFR agent uses the same infoset key builder as the trainer, so trained strategies and runtime decisions remain aligned.

---

## CFR tools

### CFRNode

Stores cumulative regrets and cumulative strategy sums for the fixed action set:

- `FOLD`
- `CHECK_CALL`
- `BET_RAISE`

### InfosetKeyBuilder

Shared abstraction layer for CFR training and CFR playing.

### CachedEquityBucketProvider

Gets equity buckets or equity values from the SQLite equity cache.

### MemoizedBucketProvider

Wraps another bucket provider and caches equity/bucket lookups in memory.

### CFRTrainer

Trains a bucketed CFR strategy using sampled deals and the shared infoset abstraction.

### MCCFRTrainer

Trains a bucketed strategy using external-sampling MCCFR.

### MultiseedMCCFRTrainer

Runs several independent MCCFR training runs with different seeds and saves each checkpoint separately.

### CFRAgent

Plays from trained CFR/MCCFR nodes using average strategy.

---

## Evaluation tools

### MatchRunner

Runs head-to-head matches between two agents.

### TournamentRunner

Runs pairwise matches between multiple agents and produces a payoff table.

### RepeatedTournamentRunner

Runs repeated pairwise tournaments and reports confidence intervals.

```python
result = repeated_runner.run(
    hands_per_seat=5000,
    include_self_play=False,
    number_tournaments=20,
)

result.print_mean_table()
result.print_rankings()
```

### CSV export

Tournament and repeated tournament results can be exported:

```python
result.to_csv("results/mccfr_tournament.csv")
```

---

## Current status

Implemented:

- 20-card Lite Hold'em game engine
- hand evaluator
- environment wrapper
- baseline agents
- exact equity agent
- bucketed equity agent
- SQLite equity cache
- full equity cache builder
- cached equity agents
- bucketed CFR trainer
- external-sampling MCCFR trainer
- delayed average-strategy support
- multi-seed MCCFR training support
- seed-averaged checkpoint experiments
- CFR/MCCFR playing agent
- pluggable infoset abstractions
- repeated tournament evaluation
- match and tournament evaluation
- diagnostic summaries
- CSV export
- test suite
- example scripts

Current research findings:

- Street-aware equity bucketing was the largest abstraction improvement.
- Pot bucket added useful betting-context information.
- No-history street-aware pot bucket is a compact and competitive abstraction.
- 7-bucket hand-strength abstraction was viable but not clearly better than the 5-bucket version.
- Delayed average-strategy accumulation showed small possible gains at 100k iterations, but longer training remained stronger.
- Multi-seed selection was useful and produced a 500k seed competitive with 1M training.
- Seed averaging was viable but did not beat the strongest 1M single-run checkpoint.

---

## Next development direction

The current training-method branch has tested delayed averaging, multi-seed selection, and seed-averaged checkpoints.

Potential next experiments:

1. Checkpoint selection across training stages.
2. Approximate best-response / exploitability evaluation.
3. Action-frequency diagnostics by street and equity bucket.
4. Focused evaluation against stronger selected checkpoints.
5. Porting the framework toward short-deck or full-deck limit Hold'em.

The next likely experiment is checkpoint selection across training stages, because the final checkpoint is not guaranteed to be the strongest policy.

---

## Notes

This is not full no-limit Texas Hold'em. It is a simplified 20-card heads-up fixed-action poker environment designed for experimentation and agent evaluation.

The project is intended as a stepping stone toward larger poker AI systems.
