# -*- coding: utf-8 -*-
"""
Created on Sun Jun  7 21:19:45 2026

@author: Richard
"""

from pathlib import Path

from lite_holdem_ai import (
    CachedBucketEquityAgent,
    CachedEquityAgent,
    HeuristicAgent,
    LiteHoldemEnv,
)
from lite_holdem_ai.cfr.agent import CFRAgent
from lite_holdem_ai.cfr.infoset import (
    CachedEquityBucketProvider,
    EquityBucketInfosetKeyBuilder,
    MemoizedBucketProvider,
)
from lite_holdem_ai.cfr.mccfr_trainer import MCCFRTrainer
from lite_holdem_ai.cfr.trainer import CFRTrainer
from lite_holdem_ai.equity.cache import EquityCache
from lite_holdem_ai.evaluation.repeated import RepeatedTournamentRunner


CACHE_PATH = Path("cache") / "equity_cache.sqlite"

CFR_10K_PATH = Path("checkpoints") / "lite_holdem_cfr_10k.pkl"
MCCFR_10K_PATH = Path("checkpoints") / "lite_holdem_optimised_mccfr_10k.pkl"
MCCFR_100K_PATH = Path("checkpoints") / "lite_holdem_optimised_mccfr_100k.pkl"
MCCFR_500K_PATH = Path("checkpoints") / "lite_holdem_mccfr_500k.pkl"


def make_infoset_builder(cache_path):
    equity_cache = EquityCache(cache_path)

    raw_bucket_provider = CachedEquityBucketProvider(equity_cache)
    bucket_provider = MemoizedBucketProvider(raw_bucket_provider)
    infoset_builder = EquityBucketInfosetKeyBuilder(bucket_provider)

    return infoset_builder, equity_cache


def load_cfr_agent(
    checkpoint_path,
    cache_path,
    name,
    seed,
    trainer_cls,
):
    infoset_builder, equity_cache = make_infoset_builder(cache_path)

    trainer = trainer_cls(
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

    # Let the repeated runner close the DB connection via agent.close()
    # if you add close() support to CFRAgent.
    agent.equity_cache = equity_cache

    return agent


def make_agents(seed):
    return [
        HeuristicAgent(name="Heuristic"),
        CachedEquityAgent(
            name="CachedEquity",
            cache_path=CACHE_PATH,
        ),
        CachedBucketEquityAgent(
            name="CachedBucket",
            cache_path=CACHE_PATH,
        ),
        load_cfr_agent(
            checkpoint_path=CFR_10K_PATH,
            cache_path=CACHE_PATH,
            name="CFR 10k",
            seed=seed + 10,
            trainer_cls=CFRTrainer,
        ),
        load_cfr_agent(
            checkpoint_path=MCCFR_10K_PATH,
            cache_path=CACHE_PATH,
            name="MCCFR 10k",
            seed=seed + 20,
            trainer_cls=MCCFRTrainer,
        ),
        load_cfr_agent(
            checkpoint_path=MCCFR_100K_PATH,
            cache_path=CACHE_PATH,
            name="MCCFR 100k",
            seed=seed + 30,
            trainer_cls=MCCFRTrainer,
        ),
        load_cfr_agent(
            checkpoint_path=MCCFR_500K_PATH,
            cache_path=CACHE_PATH,
            name="MCCFR 500k",
            seed=seed + 40,
            trainer_cls=MCCFRTrainer,
        ),
    ]


def main():
    missing_files = [
        path for path in [
            CACHE_PATH,
            CFR_10K_PATH,
            MCCFR_10K_PATH,
            MCCFR_100K_PATH,
            MCCFR_500K_PATH,
        ]
        if not path.exists()
    ]

    if missing_files:
        raise FileNotFoundError(
            "Missing required cache/checkpoint files:\n"
            + "\n".join(str(path) for path in missing_files)
        )

    runner = RepeatedTournamentRunner(
        agent_factory=make_agents,
        env_factory=lambda: LiteHoldemEnv(),
    )

    result = runner.run(
        hands_per_seat=2000,
        include_self_play=False,
        number_tournaments=10,
    )

    result.print_mean_table()
    print()
    result.print_rankings()

    Path("results").mkdir(exist_ok=True)
    result.to_csv("results/repeated_cfr_mccfr_benchmark.csv")


if __name__ == "__main__":
    main()