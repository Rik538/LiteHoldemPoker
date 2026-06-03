# -*- coding: utf-8 -*-
"""
Bucketed equity agent for Lite Hold'em.

This agent reuses EquityAgent's exact equity calculation, then maps equity
to coarse buckets before choosing an action.
"""

from lite_holdem_ai.agents.equity_agent import EquityAgent
from lite_holdem_ai.game.actions import Action


class BucketEquityAgent(EquityAgent):
    name = "Bucket Equity"

    def __init__(
        self,
        name: str | None = None,
        seed: int | None = None,
        cache_path=None,
        build_cache_if_missing: bool = False,
    ):
        super().__init__(
            name=name if name is not None else "Bucket Equity",
            seed=seed,
            cache_path=cache_path,
            build_cache_if_missing=build_cache_if_missing,
        )

    def select_action(self, observation, legal_actions):
        if not legal_actions:
            raise ValueError("BucketEquityAgent received no legal actions")

        private_cards = observation["private_cards"]
        public_cards = observation["public_cards"]
        pot = observation["pot"]
        amount_to_call = observation["amount_to_call"]

        equity_result = self.calculate_equity(private_cards, public_cards)
        equity = equity_result["equity"]

        bucket = self.bucket_from_equity(equity)

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

    def bucket_from_equity(self, equity: float) -> int:
        """
        Convert exact equity into a coarse hand-strength bucket.

        0 = trash
        1 = weak
        2 = medium
        3 = strong
        4 = premium
        """
        if equity < 0.30:
            return 0

        if equity < 0.45:
            return 1

        if equity < 0.58:
            return 2

        if equity < 0.72:
            return 3

        return 4

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
        """
        No bet to call.

        CHECK_CALL means check.
        BET_RAISE means bet.
        """
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
        """
        Facing a bet.

        FOLD means fold.
        CHECK_CALL means call.
        BET_RAISE means raise.
        """
        pot_odds = self.pot_odds(pot, amount_to_call)

        # Bucket 4: premium - raise if possible, otherwise call.
        if bucket == 4:
            if Action.BET_RAISE in legal_actions:
                return Action.BET_RAISE

            if Action.CHECK_CALL in legal_actions:
                return Action.CHECK_CALL

            return legal_actions[0]

        # Bucket 3: strong - call, raise only with very strong equity.
        if bucket == 3:
            if Action.BET_RAISE in legal_actions and equity >= 0.68:
                return Action.BET_RAISE

            if Action.CHECK_CALL in legal_actions:
                return Action.CHECK_CALL

            return legal_actions[0]

        # Bucket 2: medium - call if pot odds justify it.
        if bucket == 2:
            if Action.CHECK_CALL in legal_actions and equity >= pot_odds:
                return Action.CHECK_CALL

            if Action.FOLD in legal_actions:
                return Action.FOLD

            if Action.CHECK_CALL in legal_actions:
                return Action.CHECK_CALL

            return legal_actions[0]

        # Bucket 1: weak - only call if price is good.
        if bucket == 1:
            if Action.CHECK_CALL in legal_actions and equity >= pot_odds + 0.05:
                return Action.CHECK_CALL

            if Action.FOLD in legal_actions:
                return Action.FOLD

            if Action.CHECK_CALL in legal_actions:
                return Action.CHECK_CALL

            return legal_actions[0]

        # Bucket 0: trash - fold facing a bet.
        if Action.FOLD in legal_actions:
            return Action.FOLD

        if Action.CHECK_CALL in legal_actions:
            return Action.CHECK_CALL

        return legal_actions[0]