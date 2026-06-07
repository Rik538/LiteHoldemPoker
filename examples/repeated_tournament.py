# -*- coding: utf-8 -*-
"""
Created on Sun Jun  7 21:19:45 2026

@author: Richard
"""

from lite_holdem_ai import RepeatedTournamentRunner,LiteHoldemEnv
from lite_holdem_ai.agents import AggressiveAgent,HeuristicAgent,PassiveAgent,RandomAgent
from pathlib import Path


def make_agents(seed):
    return [
        RandomAgent(seed = seed,name="Random"),
        PassiveAgent(seed = seed,name="Passive"),
        AggressiveAgent(seed = seed,name="Aggressive"),
        HeuristicAgent(seed = seed,name="Heuristic"),
    ]

def main():
   
    runner = RepeatedTournamentRunner(
        agent_factory=make_agents,
        env_factory=lambda: LiteHoldemEnv(),
    )

    result = runner.run(
        hands_per_seat=1000,
        include_self_play=False,
        number_tournaments = 10
    )

    result.print_mean_table()
    print()
    result.print_rankings()
    
    Path("results").mkdir(exist_ok=True)
    result.to_csv("results/repeated_baseline_tournament.csv")


if __name__ == "__main__":
    main()
    