# -*- coding: utf-8 -*-
"""
Evaluate a trained CFR agent against RandomAgent.
"""

from pathlib import Path

from lite_holdem_ai.agents.random_agent import RandomAgent
from lite_holdem_ai.cfr.agent import CFRAgent
from lite_holdem_ai.cfr.infoset import (
    CachedEquityBucketProvider,
    EquityBucketInfosetKeyBuilder,
)
from lite_holdem_ai.cfr.trainer import CFRTrainer
from lite_holdem_ai.equity.cache import EquityCache
from lite_holdem_ai.evaluation.match import MatchRunner
from lite_holdem_ai.game.environment import LiteHoldemEnv


def main():
    cache_path = Path("cache") / "equity_cache.sqlite"
    checkpoint_path = Path("checkpoints") / "lite_holdem_cfr_1k.pkl"

    if not cache_path.exists():
        raise FileNotFoundError(
            f"Equity cache not found at {cache_path}. "
            "Run py examples\\build_equity_cache.py first."
        )

    if not checkpoint_path.exists():
        raise FileNotFoundError(
            f"CFR checkpoint not found at {checkpoint_path}. "
            "Run py examples\\train_cfr.py first."
        )

    with EquityCache(cache_path) as equity_cache:
        bucket_provider = CachedEquityBucketProvider(equity_cache)
        infoset_builder = EquityBucketInfosetKeyBuilder(bucket_provider)

        trainer = CFRTrainer(
            infoset_builder=infoset_builder,
            env_factory=lambda: LiteHoldemEnv(),
        )
        trainer.load_checkpoint(checkpoint_path)

        cfr_agent = CFRAgent(
            nodes=trainer.nodes,
            infoset_builder=infoset_builder,
            name=f"CFR {trainer.iterations_trained}",
            seed=1,
        )

        random_agent = RandomAgent(seed=2, name="Random")

        runner = MatchRunner(
            env_factory=lambda: LiteHoldemEnv(),
            agents=[cfr_agent, random_agent],
        )

        result = runner.play_many(
            hands_per_seat=1000,
            swap_seats=True,
        )

        result.print_summary()

        print()
        print(f"CFR missing nodes: {cfr_agent.missing_nodes}")


if __name__ == "__main__":
    main()

