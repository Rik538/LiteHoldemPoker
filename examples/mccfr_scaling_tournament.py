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
    CachedBucketEquityAgent,
    CachedEquityAgent,
    HeuristicAgent,
)

from lite_holdem_ai.cfr.agent import CFRAgent
from lite_holdem_ai.cfr.infoset import (
    CachedEquityBucketProvider,
    EquityBucketInfosetKeyBuilder,
)
from lite_holdem_ai.cfr.trainer import CFRTrainer
from lite_holdem_ai.cfr.mccfr_trainer import MCCFRTrainer
from lite_holdem_ai.equity.cache import EquityCache


def main():
    cache_path = Path("cache") / "equity_cache.sqlite"
    checkpoint_paths = [Path("checkpoints") / "lite_holdem_cfr_10k.pkl",
                        Path("checkpoints") / "lite_holdem_mccfr_1k.pkl",
                        Path("checkpoints") / "lite_holdem_mccfr_10k.pkl",
                        Path("checkpoints") / "lite_holdem_mccfr_100k.pkl",
                        Path("checkpoints") / "lite_holdem_optimised_mccfr_10k.pkl",
                        ]
    
    for checkpoint_path in checkpoint_paths:
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
        trainer.load_checkpoint(checkpoint_paths[0])

        cfr_agent10k = CFRAgent(
            nodes=trainer.nodes,
            infoset_builder=infoset_builder,
            name=f"CFR {trainer.iterations_trained}",
            seed=1,
        )
        
        
        trainer = MCCFRTrainer(
            infoset_builder=infoset_builder,
            env_factory=lambda: LiteHoldemEnv(),
        )
        
        trainer.load_checkpoint(checkpoint_paths[1])

        mccfr_agent1k = CFRAgent(
            nodes=trainer.nodes,
            infoset_builder=infoset_builder,
            name=f"MCCFR {trainer.iterations_trained}",
            seed=1,
        )
        
        trainer.load_checkpoint(checkpoint_paths[2])

        mccfr_agent10k = CFRAgent(
            nodes=trainer.nodes,
            infoset_builder=infoset_builder,
            name=f"MCCFR {trainer.iterations_trained}",
            seed=1,
        )
        
        trainer.load_checkpoint(checkpoint_paths[3])

        mccfr_agent100k = CFRAgent(
            nodes=trainer.nodes,
            infoset_builder=infoset_builder,
            name=f"MCCFR {trainer.iterations_trained}",
            seed=1,
        )
        
        trainer.load_checkpoint(checkpoint_paths[4])

        mccfr_opt_agent10k = CFRAgent(
            nodes=trainer.nodes,
            infoset_builder=infoset_builder,
            name=f"Optimised MCCFR {trainer.iterations_trained}",
            seed=1,
        )

        agents = [
            HeuristicAgent(name="Heuristic"),
            CachedEquityAgent(name="CachedEquity", cache_path=cache_path),
            CachedBucketEquityAgent(name="CachedBucket", cache_path=cache_path),
            cfr_agent10k,
            mccfr_agent1k,
            mccfr_agent10k,
            mccfr_agent100k,
            mccfr_opt_agent10k,
        ]

        runner = TournamentRunner(
            agents=agents,
            env_factory=lambda: LiteHoldemEnv(),
        )

        result = runner.run(
            hands_per_seat=5000,
            include_self_play=False,
        )

        result.print_payoff_table()
        print()
        result.print_rankings()

        Path("results").mkdir(exist_ok=True)
        result.to_csv("results/cfr_scaling_tournament.csv")

        print()
        print(f"{cfr_agent10k.name} missing nodes: {cfr_agent10k.missing_nodes}")
        print(f"{mccfr_agent1k.name} missing nodes: {mccfr_agent1k.missing_nodes}")
        print(f"{mccfr_agent10k.name} missing nodes: {mccfr_agent10k.missing_nodes}")
        print(f"{mccfr_agent100k.name} missing nodes: {mccfr_agent100k.missing_nodes}")
        print(f"{mccfr_opt_agent10k.name} missing nodes: {mccfr_opt_agent10k.missing_nodes}")

        # Close cached agents' database connections.
        for agent in agents:
            if hasattr(agent, "close"):
                agent.close()


if __name__ == "__main__":
    main()