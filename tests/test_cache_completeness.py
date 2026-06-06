# -*- coding: utf-8 -*-
"""
Created on Fri Jun  5 07:53:04 2026

@author: Richard
"""

import math
import os
from itertools import combinations
from pathlib import Path

import pytest

from lite_holdem_ai.equity.cache import EquityCache


CACHE_PATH = Path("cache") / "equity_cache.sqlite"

BOARD_SIZES = [0, 3, 4, 5]

EXPECTED_COUNTS = {
    0: math.comb(20, 2),
    3: math.comb(20, 2) * math.comb(18, 3),
    4: math.comb(20, 2) * math.comb(18, 4),
    5: math.comb(20, 2) * math.comb(18, 5),
}

EXPECTED_TOTAL = sum(EXPECTED_COUNTS.values())


def require_full_cache_test_enabled():
    if os.environ.get("RUN_FULL_CACHE_TESTS") != "1":
        pytest.skip(
            "Full equity cache tests are disabled. "
            "Set RUN_FULL_CACHE_TESTS=1 to run them."
        )

    if not CACHE_PATH.exists():
        pytest.skip(f"Equity cache does not exist at {CACHE_PATH}")


def test_full_equity_cache_has_expected_counts():
    """
    Fast completeness check.

    This verifies that the cache contains the expected number of entries
    for each public board size.
    """
    require_full_cache_test_enabled()

    with EquityCache(CACHE_PATH) as cache:
        assert cache.count() == EXPECTED_TOTAL

        for board_size, expected_count in EXPECTED_COUNTS.items():
            assert cache.count(board_size=board_size) == expected_count


def test_full_equity_cache_contains_all_possible_keys():
    """
    Exhaustive completeness check.

    This iterates through every legal private/public card combination and checks
    that the cache contains an entry.

    This is intentionally slow. Do not run it as part of the normal unit test
    suite.
    """
    require_full_cache_test_enabled()

    all_cards = list(range(20))

    with EquityCache(CACHE_PATH) as cache:
        for board_size in BOARD_SIZES:
            checked = 0

            for private_cards_tuple in combinations(all_cards, 2):
                private_cards = list(private_cards_tuple)
                private_set = set(private_cards)

                remaining_after_private = [
                    card for card in all_cards
                    if card not in private_set
                ]

                for public_cards_tuple in combinations(
                    remaining_after_private,
                    board_size,
                ):
                    public_cards = list(public_cards_tuple)

                    assert cache.contains(private_cards, public_cards), (
                        f"Missing cache entry for "
                        f"private={private_cards}, public={public_cards}"
                    )

                    checked += 1

            assert checked == EXPECTED_COUNTS[board_size]