# -*- coding: utf-8 -*-
"""
Train a small bucketed CFR strategy for Lite Hold'em.

This uses the shared EquityBucketInfosetKeyBuilder and the SQLite equity cache.
"""

from pathlib import Path

from lite_holdem_ai.cfr.infoset import (
    CachedEquityBucketProvider,
    EquityBucketInfosetKeyBuilder,
    MemoizedBucketProvider,
)
from lite_holdem_ai.cfr.mccfr_trainer import MCCFRTrainer
from lite_holdem_ai.equity.cache import EquityCache
from lite_holdem_ai.game.environment import LiteHoldemEnv

import time


def main():
    
    trainer_stats = {}
    
    
    cache_path = Path("cache") / "equity_cache.sqlite"
  

    if not cache_path.exists():
        raise FileNotFoundError(
            f"Equity cache not found at {cache_path}. "
            "Run py examples\\build_equity_cache.py first."
        )

    with EquityCache(cache_path) as equity_cache:
        bucket_provider = CachedEquityBucketProvider(equity_cache)
        infoset_builder = EquityBucketInfosetKeyBuilder(bucket_provider)

        trainer = MCCFRTrainer(
            infoset_builder=infoset_builder,
            env_factory=lambda: LiteHoldemEnv(),
        )
        
        start = time.perf_counter()

        trainer.train(
            iterations=1_000,
            path=None,
            save_every=None,
            print_every=1_000,
            update_both_players=True,
        )
        
        elapsedMCCFR = time.perf_counter() - start
        trainer_stats["Base MCCFR"] = elapsedMCCFR
        

        print()
        print("Training complete.")



            
    with EquityCache(cache_path) as equity_cache:
        raw_bucket_provider = CachedEquityBucketProvider(equity_cache)
        bucket_provider = MemoizedBucketProvider(raw_bucket_provider)
        infoset_builder = EquityBucketInfosetKeyBuilder(bucket_provider)

        trainer = MCCFRTrainer(
            infoset_builder=infoset_builder,
            env_factory=lambda: LiteHoldemEnv(),
        )
        
        start = time.perf_counter()

        trainer.train(
            iterations=1_000,
            path=None,
            save_every=None,
            print_every=1_000,
            update_both_players=True,
        )
        
        
        elapsedMCCFR = time.perf_counter() - start
        trainer_stats["Memoized MCCFR"] = elapsedMCCFR
        

        print()
        print("Training complete.")


    for trainer in trainer_stats.keys():
        
        elapsed = trainer_stats[trainer]
        print(f"Trainer: {trainer}")
        print(f"Elapsed: {elapsed:.2f}s")
        print(f"Iterations/sec: {1000 / elapsed:.2f}")
        
        

if __name__ == "__main__":
    main()