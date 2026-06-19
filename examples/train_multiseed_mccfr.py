# -*- coding: utf-8 -*-
"""
Created on Fri Jun 19 16:40:57 2026

@author: Richard
"""

from pathlib import Path

from lite_holdem_ai import LiteHoldemEnv
from lite_holdem_ai.cfr.infoset import (
    CachedEquityBucketProvider,
    MemoizedBucketProvider,
    StreetAwarePotBucketNoHistoryInfosetKeyBuilder,
)
from lite_holdem_ai.cfr.mccfr_trainer import MCCFRTrainer
from lite_holdem_ai.equity.cache import EquityCache
from lite_holdem_ai.cfr.multiseed_mccfr_trainer import MultiseedMCCFRTrainer


CACHE_PATH = Path("cache") / "equity_cache.sqlite"


def make_trainer(seed):
    equity_cache = EquityCache(CACHE_PATH)

    raw_provider = CachedEquityBucketProvider(equity_cache)
    bucket_provider = MemoizedBucketProvider(raw_provider)

    infoset_builder = StreetAwarePotBucketNoHistoryInfosetKeyBuilder(
        bucket_provider
    )

    trainer = MCCFRTrainer(
        infoset_builder=infoset_builder,
        env_factory=lambda: LiteHoldemEnv(),
        seed=seed,
    )

    # Optional, if you want the wrapper to close the DB connection.
    trainer.equity_cache = equity_cache

    return trainer

def main():
    multiseed_trainer = MultiseedMCCFRTrainer(
        trainer_factory=make_trainer,
        seed=123,
    )

    results = multiseed_trainer.train(
        iterations=100_000,
        path=Path("checkpoints") / "lite_holdem_nohist_100k.pkl",
        save_every=10_000,
        print_every=1_000,
        update_both_players=True,
        average_starting_iteration=0,
        seeds=[1, 2, 3, 4, 5],
    )

    print()
    print("Summary:")

    for result in results:
        print(
            f"seed={result.seed} | "
            f"checkpoint={result.checkpoint_path} | "
            f"iterations={result.iterations_trained} | "
            f"infosets={result.infosets}"
        )


if __name__ == "__main__":
    main()