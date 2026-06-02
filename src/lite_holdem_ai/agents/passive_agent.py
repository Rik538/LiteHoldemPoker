# -*- coding: utf-8 -*-
"""
Created on Thu Mar  5 14:41:01 2026

@author: Richard
"""

from lite_holdem_ai.game.actions import Action
from .base import Agent


        
class PassiveAgent(Agent):
    name = "Passive"

    def __init__(self, seed: int | None = None, name: str | None = None):
        self.name = name if name is not None else "Passive"

    def select_action(self, observation, legal_actions):
        if not legal_actions:
            raise ValueError("PassiveAgent received no legal actions")

        if Action.CHECK_CALL in legal_actions:
            return Action.CHECK_CALL
        else:
            return Action.FOLD
    
        
    
    
