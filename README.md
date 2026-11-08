# Lite Hold'em AI

`lite-holdem-ai` began as a Python package for experimenting with agents in a simplified 20-card, heads-up Texas Hold'em-style poker game. It now includes an independently implemented **Rust game engine, equity system, MCCFR trainer, CFR agent, and tournament framework**, along with a bridge that lets Rust and Python agents play each other in the same game.

The Python package includes a playable environment, baseline and equity agents, cached equity, bucketed CFR, external-sampling MCCFR, pluggable information-set abstractions, training experiments, repeated tournaments, CSV export, and diagnostics. The Rust crate focuses on performance, correctness testing, and cross-language interoperability.

**Project milestone:** a Rust-trained CFR agent and a Python-trained CFR agent successfully completed a 100,000-hand head-to-head tournament, refereed entirely by the Rust engine. The project is considered feature-complete for its original goal; further research is optional.

This is an experimental, simplified poker AI project, not a full Texas Hold'em solver.

---

## Features

- 20-card Lite Hold'em deck
- Heads-up two-player poker
- Private cards and public board cards
- Multiple betting streets
- Python fixed action set: `FOLD`, `CHECK_CALL`, `BET_RAISE`
- Rust action variants: `Fold`, `Check`, `Call`, `Bet`, `Raise` (equivalent choices, distinguished by betting context)
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
- Native Rust engine, exact equity calculations, and in-memory equity lookup
- Rust external-sampling MCCFR trainer with checkpoint save/load
- Rust CFR and cached-equity playing agents
- Rust single-hand, multi-hand, and seat-swapped tournament runners
- Persistent Python subprocess bridge (JSON Lines over stdin/stdout)
- Rust CFR vs Python CFR cross-language game and tournament examples

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
│       ├── bridge/
│       │   └── agent_bridge.py
│       ├── cfr/
│       ├── equity/
│       ├── evaluation/
│       └── game/
├── rust/
│   └── holdem_core/
│       ├── Cargo.toml
│       ├── src/
│       │   ├── state.rs
│       │   ├── observed_state.rs
│       │   ├── agents/
│       │   ├── bridge/
│       │   │   ├── observation.rs
│       │   │   └── python_agent.rs
│       │   ├── cfr/
│       │   ├── runners/
│       │   └── ...
│       └── examples/
│           ├── benchmark_rust_vs_python.rs
│           └── benchmark_rust_vs_python_tournament.rs
├── tests/
└── results/
```

Generated folders such as `cache/`, `checkpoints/`, and `results/` are intentionally ignored by Git. Checkpoint files and equity databases must be generated or supplied locally; they are not included in a normal source checkout.

---

## Installation

Requirements: Python with `pip`, plus a Rust toolchain (`cargo` and `rustc`) for the Rust crate. The commands below use a Linux/Fedora-style shell.

From the repository root, install the Python package in editable mode:

```bash
python -m pip install -e ".[dev]"
```

Build the Rust implementation:

```bash
cd rust/holdem_core
cargo build --release
```

On Windows PowerShell, `py -m pip install -e ".[dev]"` is the equivalent Python installation command. Use the interpreter/environment that contains your Python project dependencies when launching the bridge.

---

## Running tests

From the repository root, run the Python tests:

```bash
python -m pytest
```

Then run the Rust tests from the crate directory:

```bash
cd rust/holdem_core
cargo test
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

```bash
RUN_FULL_CACHE_TESTS=1 python -m pytest tests/test_cache_completeness.py
```

---

## Building the equity cache

```bash
python examples/build_equity_cache.py
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

```bash
python examples/baseline_tournament.py
```

Equity agents:

```bash
python examples/equity_tournament.py
python examples/bucket_equity_tournament.py
python examples/cached_equity_tournament.py
```

CFR/MCCFR checkpoints:

```bash
python examples/cfr_tournament.py
python examples/mccfr_scaling_tournament.py
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

```bash
python examples/train_cfr.py
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

```bash
python examples/train_mccfr.py
```

Delayed-averaging MCCFR training:

```bash
python examples/train_delayed_mccfr.py
```

Multi-seed MCCFR training:

```bash
python examples/train_multiseed_mccfr.py
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
| Board texture bucket | Compactly captures paired boards, flush pressure, and straight pressure for the newer cross-language abstraction. |

In the earlier Python-only abstraction experiments, the preferred compact family was:

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

The later Python/Rust cross-language implementation uses an **eight-field no-history abstraction**, also including board texture:

```python
(
    player,
    street,
    street_aware_equity_bucket,
    pot_bucket,
    texture_bucket,
    position,
    facing_bet,
    raises_this_round,
)
```

The texture bucket combines flags for a paired board, at least three cards of one suit, and at least three distinct ranks (a coarse straight-pressure signal in the five-rank deck). Training and playing must use the **same** key structure, bucket thresholds, action semantics, and card encoding. Earlier Python experiment results below describe their original configurations and should not be interpreted as direct comparisons with the later eight-field model.

---

## Abstraction experiment findings

Current experimental findings:

- Street-aware equity thresholds were a major improvement over global equity buckets.
- Adding pot bucket improved the street-aware abstraction.
- Removing street history did not clearly hurt performance, suggesting exact street action history is mostly redundant once facing bet, raises this round, position, pot bucket, and street-aware equity are included.
- Increasing from 5 to 7 street-aware equity buckets was viable, but did not clearly outperform the simpler 5-bucket street-aware version.
- The strongest agents currently come from the street-aware pot-bucket and no-history street-aware pot-bucket MCCFR families.

These earlier Python-only findings are based on repeated tournament evaluation rather than single-run results. They are historical experimental observations, not a claim that the same ranking holds for the later eight-field Rust/Python setup.

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

## Rust implementation

The Rust crate (`rust/holdem_core`) is an independent implementation of the same simplified game. Its primary objective was to reproduce the game and CFR workflow with compact data structures, fast evaluation, and a reliable route to playing against the original Python agents.

### Engine and agents

- 20-card deck with ranks ten through ace and four suits, shuffled using a seeded RNG.
- Heads-up betting, legal-action validation, street transitions, and terminal payoffs.
- Player-limited `ObservedState` observations, excluding the opponent's private cards.
- Exact equity evaluation with SQLite persistence and a separate in-memory lookup cache.
- External-sampling MCCFR with regret matching, averaged strategies, and checkpoint save/load.
- Native `CFRAgent` and `CachedBucketEquityAgent` implementations.
- Shared `MatchAgent` trait for native and Python-backed agents.
- Single-hand, multi-hand, and tournament runners, with reversed seats and button rotation.

Rust uses five distinct action variants (`Fold`, `Check`, `Call`, `Bet`, and `Raise`) where the Python engine uses three (`FOLD`, `CHECK_CALL`, and `BET_RAISE`). The bridge converts between them according to whether the player is facing a bet.

### Equity cache

The Rust equity database covers all **2,364,550** private-hand/board combinations listed earlier. The implementation uses card bitmasks as lookup keys; the in-memory cache avoids repeated SQLite queries during play and training.

These are **measured development benchmarks**, not guaranteed results on other systems:

| Operation | Python | Rust | Approximate improvement |
|---|---:|---:|---:|
| Seven-card hand evaluation | 105,000 hands/s | 1,420,000 hands/s | 13.5× |
| Exhaustive preflop equity calculation | 12.43 s | 0.337 s | 37× |
| Build full equity cache | 11.34 hours | 82.31 s | 496× |

Separately, **Rust cache lookups** measured approximately **104,339/s through SQLite** versus **4,247,000/s from the in-memory cache** (about **40.7× faster**). This is a comparison of two Rust cache access modes, not Python versus Rust. The cache file is generated data and is not distributed with the source.

### MCCFR training

The Rust trainer traverses all legal actions for the updating player and samples opponent actions, using the shared eight-field abstraction described above. Training checkpoints persist learned nodes and the number of completed iterations.

In a comparable, corrected-button benchmark using the same abstraction family:

| Training run | Throughput | Notes |
|---|---:|---|
| Python MCCFR, 100k iterations | ~275 iterations/s | Corrected seat/button rotation |
| Rust MCCFR, 1M iterations | ~16,117 iterations/s | 62.04 s, 1,780 infosets |

Rust delivered approximately **58× higher iteration throughput** in those recorded runs. The runs used different iteration counts and should be treated as a throughput comparison rather than proof of strategy parity. Rust `rs_1M.bin` and `rs_10M.bin` are example trained checkpoint names from development, not files committed to the repository.

---

## Rust vs Python agent interoperability

The project's final engineering milestone was enabling an independently trained native Rust CFR agent to play the original Python CFR agent **inside the same Rust game**.

```text
Rust GameState / tournament runner
        |
        +--> Rust CFRAgent (native)
        |
        +--> PythonAgentBridge (persistent subprocess)
                   |
                   | JSON Lines over stdin/stdout
                   v
             Python agent_bridge.py
                   |
                   v
             Python CFRAgent
                   |
                   v
             Action returned to Rust GameState
```

The Rust bridge serializes `ObservedState` into one JSON object per line. The Python process starts once, loads its CFR checkpoint and equity-cache-backed infoset builder once, converts the observation to Python card IDs and action types, then returns an action such as `{"action":"CALL"}`. Rust validates legality before applying it. Python's standard output is reserved for protocol messages; diagnostics should go to standard error.

**Card encoding matters:** Python's integer card IDs use `rank * 4 + suit`, with suits `CLUBS=0`, `DIAMONDS=1`, `HEARTS=2`, `SPADES=3`. The JSON bridge converts two-character card strings such as `AH` and `KD` using that ordering. A mismatched mapping can corrupt equity and information-set lookups.

### Running a cross-language match

First install the Python package and build the Rust crate as shown above. Ensure that the Python CFR checkpoint and its Python equity cache are configured in `src/lite_holdem_ai/bridge/agent_bridge.py`, and that the Rust checkpoint and Rust equity-cache database exist.

**Local configuration:** the development Rust examples currently use fixed `PROJECT_ROOT`, `RUST_CHECKPOINT`, and `RUST_EQUITY_CACHE` constants. Adjust those paths in the example files for your checkout before running. The `python` executable used by `PythonAgentBridge` must resolve to the environment containing `lite_holdem_ai` and its dependencies.

From `rust/holdem_core`:

```bash
# One complete hand: Rust CFR vs Python CFR
cargo run --release --example benchmark_rust_vs_python

# Seat-swapped tournament: Rust CFR vs Python CFR
cargo run --release --example benchmark_rust_vs_python_tournament
```

For the tournament example, `HANDS_PER_SEATING = 5_000` produces 10,000 total hands; `HANDS_PER_SEATING = 50_000` produces 100,000. The runner swaps seats and records payoff averages, win/loss/draw counts, and an approximate 95% confidence interval.

### Final recorded cross-language tournament

The recorded **100,000-hand** Rust CFR vs Python CFR tournament (50,000 hands per seating, button rotated) produced:

| Metric | Result |
|---|---:|
| Rust CFR wins | 54,947 |
| Python CFR wins | 32,104 |
| Draws | 12,949 |
| Rust total payoff | +91,564 chips |
| Rust average payoff | +0.915640 chips/hand |
| Approximate 95% CI | +0.860179 to +0.971101 chips/hand |
| Rust as seat 0 | +0.923180 chips/hand |
| Rust as seat 1 | +0.908100 chips/hand |
| Elapsed | 15.30 s |
| Throughput | 6,534.95 hands/s |

**Interpretation:** this demonstrates successful high-throughput cross-language gameplay, **not** that Rust inherently learns better strategies than Python. An earlier Python training setup repeatedly created a fresh environment and may have trained only one button configuration. In that case, a Python checkpoint would have poor coverage of the opposite position and could fall back to an untrained action distribution. Different checkpoint training regimes and possible infoset coverage differences prevent a controlled playing-strength conclusion. No exploitability or exact strategy-parity guarantee is claimed.

---

## Current status

Implemented in Python and/or Rust:

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
- independently developed Rust game engine, CFR agent, and MCCFR trainer
- Rust binary checkpoints and high-performance in-memory equity cache
- Rust tournament runner with seat swaps and statistics
- Rust-to-Python JSON-lines agent bridge
- completed Rust CFR vs Python CFR single-hand and 100,000-hand matches

Earlier Python research findings:

- Street-aware equity bucketing was the largest abstraction improvement.
- Pot bucket added useful betting-context information.
- No-history street-aware pot bucket is a compact and competitive abstraction.
- 7-bucket hand-strength abstraction was viable but not clearly better than the 5-bucket version.
- Delayed average-strategy accumulation showed small possible gains at 100k iterations, but longer training remained stronger.
- Multi-seed selection was useful and produced a 500k seed competitive with 1M training.
- Seed averaging was viable but did not beat the strongest 1M single-run checkpoint.

---

## Project completion and possible future work

**The original project goal is complete:** a Rust-trained poker agent and a Python-trained poker agent can play one another, with Rust controlling the game and evaluating the outcome. The Python research framework and Rust performance rewrite remain useful as separate experimental implementations.

There is no planned next milestone. If the project is revisited, worthwhile follow-ups would include checking Python checkpoint infoset coverage, retraining with consistently rotating button positions, comparing strategies using paired deals and independent seeds, and exploring approximate exploitability. Those are **optional research improvements**, not prerequisites for considering the project finished.

---

## Notes

This is not full no-limit Texas Hold'em. It is a simplified 20-card heads-up fixed-action poker environment designed for experimentation and agent evaluation.

Benchmark figures are observations from development runs. Runtime, throughput, and strategy strength depend on the machine, checkpoint, agent configuration, game seed, and training setup. The project is intended as a learning platform and stepping stone toward larger imperfect-information and systems-programming projects.
