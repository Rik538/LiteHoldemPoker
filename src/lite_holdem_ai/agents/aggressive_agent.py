# -*- coding: utf-8 -*-
"""
Created on Thu Mar  5 14:41:01 2026

@author: Richard
"""



from lite_holdem_ai.game.actions import Action
from .base import Agent


class AggressiveAgent(Agent):
    name = "Aggressive"

    def __init__(self, seed: int | None = None, name: str | None = None):
        self.name = name if name is not None else "Aggressive"

    def select_action(self, observation, legal_actions):
        if not legal_actions:
            raise ValueError("AggressiveAgent received no legal actions")

        if Action.BET_RAISE in legal_actions:
            return Action.BET_RAISE
        elif Action.CHECK_CALL in legal_actions:
            return Action.CHECK_CALL
        else:
            return Action.FOLD
    
        
    
    
