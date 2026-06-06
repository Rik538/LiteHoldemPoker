# -*- coding: utf-8 -*-
"""
Created on Sun May 31 13:44:03 2026

@author: Richard
"""


from lite_holdem_ai import MatchRunner,LiteHoldemEnv 
from lite_holdem_ai.agents import RandomAgent



def main():
  
    runner = MatchRunner(
        env_factory=lambda: LiteHoldemEnv(),
        agents=[
                RandomAgent(seed=1, name="Random A"),
                RandomAgent(seed = 1,name="Random B")
                
            ],
    )

    result = runner.play_many(hands_per_seat=1000, swap_seats=True)
    result.print_summary()


if __name__ == "__main__":
    main()