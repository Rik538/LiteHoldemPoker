# -*- coding: utf-8 -*-
"""
Train a linear-average MCCFR checkpoint.

This is the same external-sampling MCCFR trainer as normal, but with
average_weighting="linear", so later average-strategy updates count more
than earlier ones.

Run from project root:

    py examples\\train_mccfr_linear_average.py
"""

from pathlib import Path

from lite_holdem_ai.cfr.infoset import (
    CachedEquityBucketProvider,
    MemoizedBucketProvider,
    StreetAwarePotBucketNoHistoryInfosetKeyBuilder,
)
from lite_holdem_ai.cfr.mccfr_trainer import MCCFRTrainer
from lite_holdem_ai.equity.cache import EquityCache
from lite_holdem_ai.game.environment import LiteHoldemEnv


# ---------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------

ITERATIONS = 500_000
SEED = 1

AVERAGE_WEIGHTING = "linear"
AVERAGE_STARTING_ITERATION = 250_000

PRINT_EVERY = 10_000
SAVE_EVERY = 50_000

CACHE_PATH = Path("cache") / "equity_cache.sqlite"

CHECKPOINT_DIR = Path("checkpoints")
CHECKPOINT_PATH = (
    CHECKPOINT_DIR
    / "mccfr_no_history_linear_250k_start_500k.pkl"
)


# ---------------------------------------------------------------------
# Factories
# ---------------------------------------------------------------------

def make_env():
    return LiteHoldemEnv()


def make_infoset_builder():
    equity_cache = EquityCache(CACHE_PATH)

    bucket_provider = CachedEquityBucketProvider(equity_cache)
    bucket_provider = MemoizedBucketProvider(bucket_provider)

    return StreetAwarePotBucketNoHistoryInfosetKeyBuilder(
        bucket_provider=bucket_provider,
    )


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------

def main():
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)

    infoset_builder = make_infoset_builder()

    trainer = MCCFRTrainer(
        infoset_builder=infoset_builder,
        env_factory=make_env,
        seed=SEED,
        average_weighting=AVERAGE_WEIGHTING,
        
    )

    print("=" * 70)
    print("Training linear-average MCCFR")
    print("-" * 70)
    print(f"Iterations:                 {ITERATIONS}")
    print(f"Seed:                       {SEED}")
    print(f"Average weighting:          {AVERAGE_WEIGHTING}")
    print(f"Average starting iteration: {AVERAGE_STARTING_ITERATION}")
    print(f"Infoset builder:            {infoset_builder.name}")
    print(f"Cache path:                 {CACHE_PATH}")
    print(f"Checkpoint path:            {CHECKPOINT_PATH}")
    print("=" * 70)

    trainer.train(
        iterations=ITERATIONS,
        path=CHECKPOINT_PATH,
        load_checkpoint=False,
        save_every=SAVE_EVERY,
        print_every=PRINT_EVERY,
        update_both_players=True,
        average_starting_iteration=AVERAGE_STARTING_ITERATION,
    )

    print("=" * 70)
    print("Training complete")
    print(f"Iterations trained: {trainer.iterations_trained}")
    print(f"Infosets:           {len(trainer.nodes)}")
    print(f"Saved to:           {CHECKPOINT_PATH}")
    print("=" * 70)


if __name__ == "__main__":
    main()