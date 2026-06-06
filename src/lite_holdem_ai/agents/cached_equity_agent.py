# -*- coding: utf-8 -*-
"""
Cached equity agent for Lite Hold'em.

This agent reads exact equity from a SQLite EquityCache instead of calculating
equity during gameplay.
"""

from pathlib import Path

from lite_holdem_ai.agents.base import Agent
from lite_holdem_ai.equity.cache import EquityCache
from lite_holdem_ai.game.actions import Action


class CachedEquityAgent(Agent):
    name = "Cached Equity"

    def __init__(
        self,
        name: str | None = None,
        cache_path: str | Path = "cache/equity_cache.sqlite",
    ):
        self.name = name if name is not None else "Cached Equity"
        self.cache = EquityCache(cache_path)

        self.value_bet_threshold = 0.62
        self.raise_threshold = 0.72
        self.call_margin = 0.00

    def close(self):
        self.cache.close()

    def select_action(self, observation, legal_actions):
        if not legal_actions:
            raise ValueError("CachedEquityAgent received no legal actions")

        private_cards = observation["private_cards"]
        public_cards = observation["public_cards"]
        pot = observation["pot"]
        amount_to_call = observation["amount_to_call"]

        result = self.cache.get(private_cards, public_cards)
        equity = result["equity"]

        if amount_to_call == 0:
            if Action.BET_RAISE in legal_actions and equity >= self.value_bet_threshold:
                return Action.BET_RAISE

            if Action.CHECK_CALL in legal_actions:
                return Action.CHECK_CALL

            return legal_actions[0]

        pot_odds = self.pot_odds(pot, amount_to_call)

        if Action.BET_RAISE in legal_actions and equity >= self.raise_threshold:
            return Action.BET_RAISE

        if Action.CHECK_CALL in legal_actions and equity >= pot_odds + self.call_margin:
            return Action.CHECK_CALL

        if Action.FOLD in legal_actions:
            return Action.FOLD

        return legal_actions[0]

    def pot_odds(self, pot, amount_to_call):
        if amount_to_call <= 0:
            return 0.0

        return amount_to_call / (pot + amount_to_call)