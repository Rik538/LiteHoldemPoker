# -*- coding: utf-8 -*-
"""
Run a tournament including a trained CFR agent.
"""

from pathlib import Path

from lite_holdem_ai import (
    LiteHoldemEnv,
    TournamentRunner,
)

from lite_holdem_ai.agents import (
    AggressiveAgent,
    CachedBucketEquityAgent,
    CachedEquityAgent,
    HeuristicAgent,
    PassiveAgent,
    RandomAgent,
)

from lite_holdem_ai.cfr.agent import CFRAgent
from lite_holdem_ai.cfr.infoset import (
    CachedEquityBucketProvider,
    EquityBucketInfosetKeyBuilder,
)
from lite_holdem_ai.cfr.trainer import CFRTrainer
from lite_holdem_ai.equity.cache import EquityCache


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

        agents = [
            RandomAgent(seed=1, name="Random"),
            PassiveAgent(name="Passive"),
            AggressiveAgent(name="Aggressive"),
            HeuristicAgent(name="Heuristic"),
            CachedEquityAgent(name="CachedEquity", cache_path=cache_path),
            CachedBucketEquityAgent(name="CachedBucket", cache_path=cache_path),
            cfr_agent,
        ]

        runner = TournamentRunner(
            agents=agents,
            env_factory=lambda: LiteHoldemEnv(),
        )

        result = runner.run(
            hands_per_seat=500,
            include_self_play=False,
        )

        result.print_payoff_table()
        print()
        result.print_rankings()

        Path("results").mkdir(exist_ok=True)
        result.to_csv("results/cfr_tournament.csv")

        print()
        print(f"CFR missing nodes: {cfr_agent.missing_nodes}")

        # Close cached agents' database connections.
        for agent in agents:
            if hasattr(agent, "close"):
                agent.close()


if __name__ == "__main__":
    main()