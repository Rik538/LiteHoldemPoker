"""
leduc_ai

A small framework for Lite Texas Holdem poker agents, CFR training, and evaluation.
"""

__version__ = "0.4.0"

from lite_holdem_ai.game.environment import LiteHoldemEnv
from lite_holdem_ai.evaluation.match import MatchRunner
from lite_holdem_ai.evaluation.tournament import TournamentRunner


__all__ = [
    "LiteHoldemEnv",
    "MatchRunner",
    "TournamentRunner",
    
]


