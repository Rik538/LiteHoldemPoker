# -*- coding: utf-8 -*-
"""
Repeated benchmark for cached equity agents and MCCFR abstraction variants.

Created on Sun Jun  7 21:19:45 2026

@author: Richard
"""

from pathlib import Path

from lite_holdem_ai import (
    CachedBucketEquityAgent,
    CachedEquityAgent,
    LiteHoldemEnv,
)
from lite_holdem_ai.cfr.agent import CFRAgent
from lite_holdem_ai.cfr.infoset import (
    CachedEquityBucketProvider,
    EquityBucketInfosetKeyBuilder,
    EquityPotBucketInfosetKeyBuilder,
    MemoizedBucketProvider,
)
from lite_holdem_ai.cfr.mccfr_trainer import MCCFRTrainer
from lite_holdem_ai.equity.cache import EquityCache
from lite_holdem_ai.evaluation.repeated import RepeatedTournamentRunner


CACHE_PATH = Path("cache") / "equity_cache.sqlite"

CHECKPOINTS = {
    "MCCFR 10k": Path("checkpoints") / "lite_holdem_optimised_mccfr_10k.pkl",
    "MCCFR 100k": Path("checkpoints") / "lite_holdem_optimised_mccfr_100k.pkl",
    "MCCFR 500k": Path("checkpoints") / "lite_holdem_mccfr_500k.pkl",
    "Pot Bucket 100k": Path("checkpoints") / "lite_holdem_pb_100k.pkl",
    "Pot Bucket 500k": Path("checkpoints") / "lite_holdem_pb_500k.pkl",
}

STANDARD_INFOSET_BUILDER = EquityBucketInfosetKeyBuilder
POT_BUCKET_INFOSET_BUILDER = EquityPotBucketInfosetKeyBuilder


def make_infoset_builder(cache_path, infoset_builder_cls):
    """Create an infoset builder and keep its equity cache available for closing."""
    equity_cache = EquityCache(cache_path)
    raw_bucket_provider = CachedEquityBucketProvider(equity_cache)
    bucket_provider = MemoizedBucketProvider(raw_bucket_provider)

    infoset_builder = infoset_builder_cls(bucket_provider)

    return infoset_builder, equity_cache


def load_mccfr_agent(
    *,
    checkpoint_path,
    cache_path,
    name,
    seed,
    infoset_builder_cls,
):
    """Load a CFR-style agent from a checkpoint using the correct infoset abstraction."""
    infoset_builder, equity_cache = make_infoset_builder(
        cache_path=cache_path,
        infoset_builder_cls=infoset_builder_cls,
    )

    trainer = MCCFRTrainer(
        infoset_builder=infoset_builder,
        env_factory=lambda: LiteHoldemEnv(),
    )
    trainer.load_checkpoint(checkpoint_path)

    agent = CFRAgent(
        nodes=trainer.nodes,
        infoset_builder=infoset_builder,
        name=name,
        seed=seed,
    )

    # Allows RepeatedTournamentRunner to close the database connection
    # if CFRAgent.close() checks for self.equity_cache.
    agent.equity_cache = equity_cache

    return agent


def make_agents(seed):
    """Create fresh agents for each repeated tournament run."""
    return [
        CachedEquityAgent(
            name="CachedEquity",
            cache_path=CACHE_PATH,
        ),
        CachedBucketEquityAgent(
            name="CachedBucket",
            cache_path=CACHE_PATH,
        ),
        load_mccfr_agent(
            checkpoint_path=CHECKPOINTS["MCCFR 10k"],
            cache_path=CACHE_PATH,
            name="MCCFR 10k",
            seed=seed + 10,
            infoset_builder_cls=STANDARD_INFOSET_BUILDER,
        ),
        load_mccfr_agent(
            checkpoint_path=CHECKPOINTS["MCCFR 100k"],
            cache_path=CACHE_PATH,
            name="MCCFR 100k",
            seed=seed + 20,
            infoset_builder_cls=STANDARD_INFOSET_BUILDER,
        ),
        load_mccfr_agent(
            checkpoint_path=CHECKPOINTS["MCCFR 500k"],
            cache_path=CACHE_PATH,
            name="MCCFR 500k",
            seed=seed + 30,
            infoset_builder_cls=STANDARD_INFOSET_BUILDER,
        ),
        load_mccfr_agent(
            checkpoint_path=CHECKPOINTS["Pot Bucket 100k"],
            cache_path=CACHE_PATH,
            name="Pot Bucket 100k",
            seed=seed + 40,
            infoset_builder_cls=POT_BUCKET_INFOSET_BUILDER,
        ),
        load_mccfr_agent(
            checkpoint_path=CHECKPOINTS["Pot Bucket 500k"],
            cache_path=CACHE_PATH,
            name="Pot Bucket 500k",
            seed=seed + 50,
            infoset_builder_cls=POT_BUCKET_INFOSET_BUILDER,
        ),
    ]


def validate_required_files():
    required_files = [CACHE_PATH, *CHECKPOINTS.values()]
    missing_files = [path for path in required_files if not path.exists()]

    if missing_files:
        raise FileNotFoundError(
            "Missing required cache/checkpoint files:\n"
            + "\n".join(str(path) for path in missing_files)
        )


def main():
    validate_required_files()

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
    print()
    result.print_rankings()

    Path("results").mkdir(exist_ok=True)
    result.to_csv("results/repeated_abstraction_benchmark.csv")


if __name__ == "__main__":
    main()

