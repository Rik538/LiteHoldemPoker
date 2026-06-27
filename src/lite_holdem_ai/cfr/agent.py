# -*- coding: utf-8 -*-
"""
Created on Sun Jun  7 13:04:03 2026

@author: Richard
"""


import random

from lite_holdem_ai.agents.base import Agent
from lite_holdem_ai.cfr.sampling import sample_strategy_action



class CFRAgent(Agent):
    name = "CFR"

    def __init__(self, nodes, infoset_builder,seed: int | None = None, name: str | None = None):
        self.name = name if name is not None else "CFR"
        self.nodes = nodes
        self.rng = random.Random(seed)
        self.missing_nodes = 0
        self.infoset_builder = infoset_builder

    def select_action(self, observation, legal_actions):
        if not legal_actions:
            raise ValueError("CFRAgent received no legal actions")

        info_key = self.infoset_builder.from_observation(observation)
        node = self.nodes.get(info_key)

        if node is None:
            self.missing_nodes += 1
            return self.rng.choice(legal_actions)

        avg_strategy = node.average_strategy(legal_actions)

        return self.sample_action(avg_strategy, legal_actions)

    def sample_action(self, strategy, legal_actions):
        return sample_strategy_action(self.rng, legal_actions, strategy)