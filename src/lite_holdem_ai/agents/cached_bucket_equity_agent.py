# -*- coding: utf-8 -*-
"""
Cached bucket equity agent for Lite Hold'em.

This agent reads both exact equity and equity bucket from a SQLite EquityCache.
"""

from pathlib import Path

from lite_holdem_ai.agents.cached_equity_agent import CachedEquityAgent
from lite_holdem_ai.game.actions import Action


class CachedBucketEquityAgent(CachedEquityAgent):
    name = "Cached Bucket Equity"

    def __init__(
        self,
        name: str | None = None,
        cache_path: str | Path = "cache/equity_cache.sqlite",
    ):
        super().__init__(
            name=name if name is not None else "Cached Bucket Equity",
            cache_path=cache_path,
        )

    def select_action(self, observation, legal_actions):
        if not legal_actions:
            raise ValueError("CachedBucketEquityAgent received no legal actions")

        private_cards = observation["private_cards"]
        public_cards = observation["public_cards"]
        pot = observation["pot"]
        amount_to_call = observation["amount_to_call"]

        result = self.cache.get(private_cards, public_cards)
        equity = result["equity"]
        bucket = result["bucket"]

        action = self.act_from_bucket(
            bucket=bucket,
            equity=equity,
            pot=pot,
            amount_to_call=amount_to_call,
            legal_actions=legal_actions,
        )

        if action in legal_actions:
            return action

        if Action.CHECK_CALL in legal_actions:
            return Action.CHECK_CALL

        return legal_actions[0]

    def act_from_bucket(
        self,
        bucket: int,
        equity: float,
        pot: float,
        amount_to_call: float,
        legal_actions,
    ):
        if amount_to_call == 0:
            return self.act_bucket_when_free(bucket, legal_actions)

        return self.act_bucket_facing_bet(
            bucket=bucket,
            equity=equity,
            pot=pot,
            amount_to_call=amount_to_call,
            legal_actions=legal_actions,
        )

    def act_bucket_when_free(self, bucket: int, legal_actions):
        if bucket >= 3 and Action.BET_RAISE in legal_actions:
            return Action.BET_RAISE

        if Action.CHECK_CALL in legal_actions:
            return Action.CHECK_CALL

        return legal_actions[0]

    def act_bucket_facing_bet(
        self,
        bucket: int,
        equity: float,
        pot: float,
        amount_to_call: float,
        legal_actions,
    ):
        pot_odds = self.pot_odds(pot, amount_to_call)

        if bucket == 4:
            if Action.BET_RAISE in legal_actions:
                return Action.BET_RAISE

            if Action.CHECK_CALL in legal_actions:
                return Action.CHECK_CALL

            return legal_actions[0]

        if bucket == 3:
            if Action.BET_RAISE in legal_actions and equity >= 0.68:
                return Action.BET_RAISE

            if Action.CHECK_CALL in legal_actions:
                return Action.CHECK_CALL

            return legal_actions[0]

        if bucket == 2:
            if Action.CHECK_CALL in legal_actions and equity >= pot_odds:
                return Action.CHECK_CALL

            if Action.FOLD in legal_actions:
                return Action.FOLD

            if Action.CHECK_CALL in legal_actions:
                return Action.CHECK_CALL

            return legal_actions[0]

        if bucket == 1:
            if Action.CHECK_CALL in legal_actions and equity >= pot_odds + 0.05:
                return Action.CHECK_CALL

            if Action.FOLD in legal_actions:
                return Action.FOLD

            if Action.CHECK_CALL in legal_actions:
                return Action.CHECK_CALL

            return legal_actions[0]

        if Action.FOLD in legal_actions:
            return Action.FOLD

        if Action.CHECK_CALL in legal_actions:
            return Action.CHECK_CALL

        return legal_actions[0]