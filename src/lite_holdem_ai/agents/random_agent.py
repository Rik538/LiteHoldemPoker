# -*- coding: utf-8 -*-
"""
Created on Thu Mar  5 14:41:01 2026

@author: Richard
"""

import random

from .base import Agent


class RandomAgent(Agent):
    name = "Random"

    def __init__(self, seed: int | None = None, name: str | None = None):
        self.rng = random.Random(seed)
        self.name = name if name is not None else "Random"

    def select_action(self, observation, legal_actions):
        if not legal_actions:
            raise ValueError("RandomAgent received no legal actions")

        return self.rng.choice(legal_actions)
    
    
    
    
    