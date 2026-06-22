# -*- coding: utf-8 -*-
"""
Repeated tournament for multi-seed MCCFR checkpoints.

This example compares several MCCFR checkpoints trained with the same
settings but different RNG seeds.

Run from project root:

    py examples\\multiseed_mccfr_tournament.py
"""

from pathlib import Path

from lite_holdem_ai import (
    CachedBucketEquityAgent,
    LiteHoldemEnv,
)
from lite_holdem_ai.cfr.agent import CFRAgent
from lite_holdem_ai.cfr.infoset import (
    CachedEquityBucketProvider,
    MemoizedBucketProvider,
    StreetAwarePotBucketNoHistoryInfosetKeyBuilder,
)
from lite_holdem_ai.cfr.mccfr_trainer import MCCFRTrainer
from lite_holdem_ai.equity.cache import EquityCache
from lite_holdem_ai.evaluation.repeated import RepeatedTournamentRunner


CACHE_PATH = Path("cache") / "equity_cache.sqlite"
CHECKPOINT_DIR = Path("checkpoints")

# Existing strong baseline.
NO_HISTORY_500K_PATH = CHECKPOINT_DIR / "lite_holdem_no_history_500k.pkl"

# These should match the filenames created by your multiseed trainer.
MULTISEED_CHECKPOINTS = {
    "Seed 1 100k": CHECKPOINT_DIR / "lite_holdem_nohist_100k_seed1.pkl",
    "Seed 2 100k": CHECKPOINT_DIR / "lite_holdem_nohist_100k_seed2.pkl",
    "Seed 3 100k": CHECKPOINT_DIR / "lite_holdem_nohist_100k_seed3.pkl",
    "Seed 4 100k": CHECKPOINT_DIR / "lite_holdem_nohist_100k_seed4.pkl",
    "Seed 5 100k": CHECKPOINT_DIR / "lite_holdem_nohist_100k_seed5.pkl",
}


def make_infoset_builder(cache_path):
    equity_cache = EquityCache(cache_path)

    raw_bucket_provider = CachedEquityBucketProvider(equity_cache)
    bucket_provider = MemoizedBucketProvider(raw_bucket_provider)

    infoset_builder = StreetAwarePotBucketNoHistoryInfosetKeyBuilder(
        bucket_provider
    )

    return infoset_builder, equity_cache


def load_mccfr_agent(
    *,
    checkpoint_path,
    cache_path,
    name,
    seed,
):
    infoset_builder, equity_cache = make_infoset_builder(cache_path)

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

    # Allows the repeated runner to close the DB connection if your CFRAgent
    # close() method checks for self.equity_cache.
    agent.equity_cache = equity_cache

    return agent


def make_agents(seed):
    agents = [
        CachedBucketEquityAgent(
            name="CachedBucket",
            cache_path=CACHE_PATH,
        ),
        load_mccfr_agent(
            checkpoint_path=NO_HISTORY_500K_PATH,
            cache_path=CACHE_PATH,
            name="No History 500k",
            seed=seed + 100,
        ),
    ]

    for offset, (name, checkpoint_path) in enumerate(
        MULTISEED_CHECKPOINTS.items(),
        start=1,
    ):
        agents.append(
            load_mccfr_agent(
                checkpoint_path=checkpoint_path,
                cache_path=CACHE_PATH,
                name=name,
                seed=seed + (offset * 10),
            )
        )

    return agents


def validate_required_files():
    required_files = [
        CACHE_PATH,
        NO_HISTORY_500K_PATH,
        *MULTISEED_CHECKPOINTS.values(),
    ]

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
    result.to_csv("results/multiseed_mccfr_tournament.csv")


if __name__ == "__main__":
    main()

