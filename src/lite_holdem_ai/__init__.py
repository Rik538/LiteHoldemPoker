"""
leduc_ai

A small framework for Lite Texas Holdem poker agents, CFR training, and evaluation.
"""

__version__ = "0.2.0"

from lite_holdem_ai.game.environment import LiteHoldemEnv
from lite_holdem_ai.agents.random_agent import RandomAgent
from lite_holdem_ai.agents.passive_agent import PassiveAgent
from lite_holdem_ai.agents.aggressive_agent import AggressiveAgent
from lite_holdem_ai.agents.heuristic_agent import HeuristicAgent
from lite_holdem_ai.evaluation.match import MatchRunner
from lite_holdem_ai.evaluation.tournament import TournamentRunner

__all__ = [
    "LiteHoldemEnv",
    "RandomAgent",
    "PassiveAgent",
    "AggressiveAgent",
    "HeuristicAgent",
    "MatchRunner",
    "TournamentRunner",
]


