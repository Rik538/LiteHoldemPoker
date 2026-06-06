# -*- coding: utf-8 -*-
"""
Created on Sun May 31 14:31:22 2026

@author: Richard
"""

from lite_holdem_ai import TournamentRunner,LiteHoldemEnv
from lite_holdem_ai.agents import   BucketEquityAgent,EquityAgent,AggressiveAgent,HeuristicAgent, \
                                    PassiveAgent,RandomAgent,CachedBucketEquityAgent,\
                                    CachedEquityAgent
from pathlib import Path

def main():
    agents = [
        RandomAgent(seed=1, name="Random"),
        PassiveAgent(name="Passive"),
        AggressiveAgent(name="Aggressive"),
        HeuristicAgent(name="Heuristic"),
        EquityAgent(name="Equity"),
        BucketEquityAgent(name="Bucket Equity"),
        CachedBucketEquityAgent(name = "Cached Bucket Equity"),
        CachedEquityAgent(name = "Cached Equity")
    ]


    runner = TournamentRunner(
        agents=agents,
        env_factory=lambda: LiteHoldemEnv(),
    )

    result = runner.run(
        hands_per_seat=1000,
        include_self_play=False,
    )

    result.print_payoff_table()
    print()
    result.print_rankings()
    
    Path("results").mkdir(exist_ok=True)
    result.to_csv("results/cached_equity_tournament.csv")


if __name__ == "__main__":
    main()
    
    