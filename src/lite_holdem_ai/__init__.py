# -*- coding: utf-8 -*-
"""
Lite Hold'em AI package.

Public API exports for the main game environment, agents, CFR tools,
equity tools, and evaluation utilities.
"""

__version__ = "0.5.0"


# Game
from lite_holdem_ai.game.environment import LiteHoldemEnv

# Standalone agents
from lite_holdem_ai.agents.random_agent import RandomAgent
from lite_holdem_ai.agents.passive_agent import PassiveAgent
from lite_holdem_ai.agents.aggressive_agent import AggressiveAgent
from lite_holdem_ai.agents.heuristic_agent import HeuristicAgent
from lite_holdem_ai.agents.equity_agent import EquityAgent
from lite_holdem_ai.agents.bucket_equity_agent import BucketEquityAgent
from lite_holdem_ai.agents.cached_equity_agent import CachedEquityAgent
from lite_holdem_ai.agents.cached_bucket_equity_agent import CachedBucketEquityAgent

# CFR
from lite_holdem_ai.cfr.agent import CFRAgent
from lite_holdem_ai.cfr.trainer import CFRTrainer

# Evaluation
from lite_holdem_ai.evaluation.match import MatchRunner
from lite_holdem_ai.evaluation.tournament import TournamentRunner

# Equity cache tools
from lite_holdem_ai.equity.cache import EquityCache
from lite_holdem_ai.equity.builder import EquityCacheBuilder, build_equity_cache


__all__ = [
    "__version__",
    # Game
    "LiteHoldemEnv",
    # Agents
    "RandomAgent",
    "PassiveAgent",
    "AggressiveAgent",
    "HeuristicAgent",
    "EquityAgent",
    "BucketEquityAgent",
    "CachedEquityAgent",
    "CachedBucketEquityAgent",
    # CFR
    "CFRAgent",
    "CFRTrainer",
    # Evaluation
    "MatchRunner",
    "TournamentRunner",
    # Equity cache
    "EquityCache",
    "EquityCacheBuilder",
    "build_equity_cache",
]