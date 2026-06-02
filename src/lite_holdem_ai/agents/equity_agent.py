# -*- coding: utf-8 -*-
"""
Created on Tue May 19 19:39:48 2026

@author: Richard
"""

from itertools import combinations
from importlib.resources import files
import os
import pickle
import random

from .base import Agent
from lite_holdem_ai.game.actions import Action
from lite_holdem_ai.game.deck import Deck
from lite_holdem_ai.game.showdown import Showdown



def default_preflop_cache_path():
    return files("lite_holdem_ai").joinpath("data/preflop_equity_cache.pkl")


class EquityAgent(Agent):
    name = "Equity"

    def __init__(
        self,
        name: str | None = None,
        seed: int | None = None,
        cache_path=None,
        build_cache_if_missing: bool = False,
    ):
        self.name = name if name is not None else "Equity"
        self.rng = random.Random(seed)

        self.deck = Deck()
        self.showdown = Showdown()

        self.cache_path = cache_path if cache_path is not None else default_preflop_cache_path()
        self.preflop_cache = {}

        self.value_bet_threshold = 0.62
        self.raise_threshold = 0.72
        self.call_margin = 0.00

        self.load_or_build_preflop_cache(
            build_if_missing=build_cache_if_missing
        )

    def select_action(self, observation, legal_actions):
        if not legal_actions:
            raise ValueError("EquityAgent received no legal actions")

        private_cards = observation["private_cards"]
        public_cards = observation["public_cards"]
        pot = observation["pot"]
        amount_to_call = observation["amount_to_call"]

        equity_result = self.calculate_equity(private_cards, public_cards)
        equity = equity_result["equity"]

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

    def calculate_equity(self, private_cards, public_cards):
        known_cards = private_cards + public_cards
        remaining_cards = self.deck.cards_remaining(known_cards)

        board_len = len(public_cards)

        if board_len == 0:
            key = tuple(sorted(private_cards))

            if key not in self.preflop_cache:
                raise KeyError(
                    f"Missing preflop equity for private hand {key}. "
                    "Build the preflop cache before using EquityAgent."
                )

            return self.preflop_cache[key]

        if board_len == 3:
            return self.flop_equity(private_cards, public_cards, remaining_cards)

        if board_len == 4:
            return self.turn_equity(private_cards, public_cards, remaining_cards)

        if board_len == 5:
            return self.river_equity(private_cards, public_cards, remaining_cards)

        raise ValueError(f"Invalid public card count: {board_len}")

    def pot_odds(self, pot, amount_to_call):
        if amount_to_call <= 0:
            return 0.0

        return amount_to_call / (pot + amount_to_call)

    def make_result(self, wins, losses, splits, total_hands):
        if total_hands == 0:
            raise ValueError("No equity scenarios were evaluated")

        equity = (wins + 0.5 * splits) / total_hands

        return {
            "wins": wins,
            "losses": losses,
            "splits": splits,
            "total": total_hands,
            "equity": equity,
        }

    def update_counts(self, result, wins, losses, splits):
        if result == 0:
            wins += 1
        elif result == 1:
            losses += 1
        else:
            splits += 1

        return wins, losses, splits

    def river_equity(self, private_cards, public_cards, remaining_cards):
        wins = 0
        losses = 0
        splits = 0
        total_hands = 0

        for opponent_hand in combinations(remaining_cards, 2):
            result = self.showdown.resolve_hands(
                private_cards,
                list(opponent_hand),
                public_cards,
            )

            wins, losses, splits = self.update_counts(
                result,
                wins,
                losses,
                splits,
            )

            total_hands += 1

        return self.make_result(wins, losses, splits, total_hands)

    def turn_equity(self, private_cards, public_cards, remaining_cards):
        wins = 0
        losses = 0
        splits = 0
        total_hands = 0

        for opponent_hand in combinations(remaining_cards, 2):
            opponent_set = set(opponent_hand)

            remaining_after_opp = [
                card for card in remaining_cards
                if card not in opponent_set
            ]

            for river_card in remaining_after_opp:
                full_public = public_cards + [river_card]

                result = self.showdown.resolve_hands(
                    private_cards,
                    list(opponent_hand),
                    full_public,
                )

                wins, losses, splits = self.update_counts(
                    result,
                    wins,
                    losses,
                    splits,
                )

                total_hands += 1

        return self.make_result(wins, losses, splits, total_hands)

    def flop_equity(self, private_cards, public_cards, remaining_cards):
        wins = 0
        losses = 0
        splits = 0
        total_hands = 0

        for opponent_hand in combinations(remaining_cards, 2):
            opponent_set = set(opponent_hand)

            remaining_after_opp = [
                card for card in remaining_cards
                if card not in opponent_set
            ]

            for future_cards in combinations(remaining_after_opp, 2):
                full_public = public_cards + list(future_cards)

                result = self.showdown.resolve_hands(
                    private_cards,
                    list(opponent_hand),
                    full_public,
                )

                wins, losses, splits = self.update_counts(
                    result,
                    wins,
                    losses,
                    splits,
                )

                total_hands += 1

        return self.make_result(wins, losses, splits, total_hands)

    def preflop_equity(self, private_cards, public_cards, remaining_cards):
        wins = 0
        losses = 0
        splits = 0
        total_hands = 0

        for opponent_hand in combinations(remaining_cards, 2):
            opponent_set = set(opponent_hand)

            remaining_after_opp = [
                card for card in remaining_cards
                if card not in opponent_set
            ]

            for board_cards in combinations(remaining_after_opp, 5):
                result = self.showdown.resolve_hands(
                    private_cards,
                    list(opponent_hand),
                    list(board_cards),
                )

                wins, losses, splits = self.update_counts(
                    result,
                    wins,
                    losses,
                    splits,
                )

                total_hands += 1

        return self.make_result(wins, losses, splits, total_hands)

    def load_or_build_preflop_cache(self, build_if_missing: bool = False):
        if os.path.exists(self.cache_path):
            self.load_preflop_cache(self.cache_path)
            return

        if build_if_missing:
            self.build_preflop_cache()
            self.save_preflop_cache(self.cache_path)
            return

        raise FileNotFoundError(
            f"Preflop equity cache not found at {self.cache_path}. "
            "Either provide cache_path or use build_cache_if_missing=True."
        )

    def save_preflop_cache(self, filepath=None):
        if filepath is None:
            filepath = self.cache_path

        with open(filepath, "wb") as f:
            pickle.dump(self.preflop_cache, f)

    def load_preflop_cache(self, filepath=None):
        if filepath is None:
            filepath = self.cache_path

        with open(filepath, "rb") as f:
            self.preflop_cache = pickle.load(f)

    def build_preflop_cache(self):
        self.preflop_cache = {}

        all_cards = list(range(20))

        for private_hand in combinations(all_cards, 2):
            private_cards = list(private_hand)
            key = tuple(sorted(private_cards))

            remaining_cards = self.deck.cards_remaining(private_cards)

            self.preflop_cache[key] = self.preflop_equity(
                private_cards=private_cards,
                public_cards=[],
                remaining_cards=remaining_cards,
            )

        return self.preflop_cache   
    
    
    
    
    
    