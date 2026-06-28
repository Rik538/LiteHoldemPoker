# -*- coding: utf-8 -*-
"""
Train a small bucketed CFR strategy for Lite Hold'em.

This uses the shared EquityBucketInfosetKeyBuilder and the SQLite equity cache.
"""

from pathlib import Path

from lite_holdem_ai.cfr.infoset import (
    CachedEquityBucketProvider,
    StreetAwarePotBucketNoHistoryInfosetKeyBuilder,
    MemoizedBucketProvider,
)
from lite_holdem_ai.cfr.mccfr_trainer import MCCFRTrainer
from lite_holdem_ai.equity.cache import EquityCache
from lite_holdem_ai.game.environment import LiteHoldemEnv


def main():
    cache_path = Path("cache") / "equity_cache.sqlite"
    checkpoint_path = Path("checkpoints") / "rfd_lite_holdem_nohist_1M.pkl"

    checkpoint_path.parent.mkdir(exist_ok=True)

    if not cache_path.exists():
        raise FileNotFoundError(
            f"Equity cache not found at {cache_path}. "
            "Run py examples\\build_equity_cache.py first."
        )

    with EquityCache(cache_path) as equity_cache:
        raw_bucket_provider = CachedEquityBucketProvider(equity_cache)
        bucket_provider = MemoizedBucketProvider(raw_bucket_provider)
        infoset_builder = StreetAwarePotBucketNoHistoryInfosetKeyBuilder(bucket_provider)

        trainer = MCCFRTrainer(
            infoset_builder=infoset_builder,
            env_factory=lambda: LiteHoldemEnv(),
        )

        trainer.train(
            iterations=1_000_000,
            path=checkpoint_path,
            save_every=50_000,
            print_every=1_000,
            update_both_players=True,
        )

        trainer.save_checkpoint(checkpoint_path)

        print()
        print("Training complete.")
        print(f"Iterations trained: {trainer.iterations_trained}")
        print(f"Infosets: {len(trainer.nodes)}")
        print(f"Saved checkpoint to: {checkpoint_path}")

        print()
        print("Sample strategies:")
        trainer.print_strategies(limit=10)


if __name__ == "__main__":
    main()