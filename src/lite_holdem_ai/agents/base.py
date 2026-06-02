# -*- coding: utf-8 -*-
"""
Created on Thu Mar  5 14:38:04 2026

@author: Richard
"""

from abc import ABC, abstractmethod

class Agent(ABC):
    name: str = "Agent"

    @abstractmethod
    def select_action(self, observation, legal_actions):
        raise NotImplementedError
        
        
        