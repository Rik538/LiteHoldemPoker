# -*- coding: utf-8 -*-
"""
Build SQLite equity caches for Lite Hold'em.

The builder computes exact equity for all possible private/public card
combinations and stores the result in EquityCache.
"""

from __future__ import annotations

from itertools import combinations
from pathlib import Path

from lite_holdem_ai.equity.cache import EquityCache
from lite_holdem_ai.game.deck import Deck
from lite_holdem_ai.game.showdown import Showdown


def bucket_from_equity(equity: float) -> int:
    """
    Convert exact equity into the same bucket scale used by BucketEquityAgent.

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


class EquityCacheBuilder:
    def __init__(self):
        self.deck = Deck()
        self.showdown = Showdown()

    def build(
        self,
        path: str | Path,
        board_sizes: list[int] | None = None,
        batch_size: int = 1000,
        clear_existing: bool = False,
        verbose: bool = True,
    ) -> None:
        """
        Build an equity cache.

        board_sizes controls which streets are generated:

            0 = preflop
            3 = flop
            4 = turn
            5 = river

        Example:

            builder.build("cache/equity_cache.sqlite", board_sizes=[0])
            builder.build("cache/equity_cache.sqlite", board_sizes=[0, 3, 4, 5])
        """
        if board_sizes is None:
            board_sizes = [0, 3, 4, 5]

        valid_board_sizes = {0, 3, 4, 5}

        for board_size in board_sizes:
            if board_size not in valid_board_sizes:
                raise ValueError(
                    f"Invalid board size {board_size}. "
                    f"Expected one of {sorted(valid_board_sizes)}."
                )

        with EquityCache(path) as cache:
            if clear_existing:
                cache.clear()

            for board_size in board_sizes:
                self.build_board_size(
                    cache=cache,
                    board_size=board_size,
                    batch_size=batch_size,
                    verbose=verbose,
                )

    def build_board_size(
        self,
        cache: EquityCache,
        board_size: int,
        batch_size: int = 1000,
        verbose: bool = True,
    ) -> None:
        all_cards = list(range(20))

        records = []
        processed = 0
        skipped = 0

        for private_cards_tuple in combinations(all_cards, 2):
            private_cards = list(private_cards_tuple)
            private_set = set(private_cards)

            remaining_after_private = [
                card for card in all_cards
                if card not in private_set
            ]

            for public_cards_tuple in combinations(remaining_after_private, board_size):
                public_cards = list(public_cards_tuple)

                if cache.contains(private_cards, public_cards):
                    skipped += 1
                    continue

                result = self.calculate_equity(
                    private_cards=private_cards,
                    public_cards=public_cards,
                )

                bucket = bucket_from_equity(result["equity"])

                records.append(
                    (
                        private_cards,
                        public_cards,
                        result,
                        bucket,
                    )
                )

                processed += 1

                if len(records) >= batch_size:
                    cache.set_many(records)
                    records.clear()

                    if verbose:
                        print(
                            f"Board size {board_size}: "
                            f"processed={processed}, skipped={skipped}, "
                            f"cached={cache.count(board_size)}"
                        )

        if records:
            cache.set_many(records)

        if verbose:
            print(
                f"Finished board size {board_size}: "
                f"processed={processed}, skipped={skipped}, "
                f"cached={cache.count(board_size)}"
            )

    def calculate_equity(self, private_cards, public_cards) -> dict:
        known_cards = private_cards + public_cards
        remaining_cards = self.deck.cards_remaining(known_cards)

        board_len = len(public_cards)

        if board_len == 0:
            return self.preflop_equity(private_cards, remaining_cards)

        if board_len == 3:
            return self.flop_equity(private_cards, public_cards, remaining_cards)

        if board_len == 4:
            return self.turn_equity(private_cards, public_cards, remaining_cards)

        if board_len == 5:
            return self.river_equity(private_cards, public_cards, remaining_cards)

        raise ValueError(f"Invalid public card count: {board_len}")

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

    def preflop_equity(self, private_cards, remaining_cards):
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


def build_equity_cache(
    path: str | Path,
    board_sizes: list[int] | None = None,
    batch_size: int = 1000,
    clear_existing: bool = False,
    verbose: bool = True,
) -> None:
    builder = EquityCacheBuilder()
    builder.build(
        path=path,
        board_sizes=board_sizes,
        batch_size=batch_size,
        clear_existing=clear_existing,
        verbose=verbose,
    )