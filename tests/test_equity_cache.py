# -*- coding: utf-8 -*-
"""
Created on Wed Jun  3 19:57:12 2026

@author: Richard
"""

import pytest

from lite_holdem_ai.equity.cache import EquityCache


def sample_result(equity=0.75):
    return {
        "wins": 75,
        "losses": 25,
        "splits": 0,
        "total": 100,
        "equity": equity,
    }


def test_equity_cache_can_be_created(tmp_path):
    path = tmp_path / "equity_cache.sqlite"

    cache = EquityCache(path)

    assert path.exists()
    assert cache.count() == 0

    cache.close()


def test_equity_cache_set_and_get(tmp_path):
    path = tmp_path / "equity_cache.sqlite"

    cache = EquityCache(path)

    cache.set(
        private_cards=[16, 17],
        public_cards=[0, 4, 8],
        result=sample_result(0.75),
        bucket=4,
    )

    result = cache.get(
        private_cards=[16, 17],
        public_cards=[0, 4, 8],
    )

    assert result["equity"] == 0.75
    assert result["bucket"] == 4
    assert result["wins"] == 75
    assert result["losses"] == 25
    assert result["splits"] == 0
    assert result["total"] == 100

    cache.close()


def test_equity_cache_keys_are_canonical(tmp_path):
    path = tmp_path / "equity_cache.sqlite"

    cache = EquityCache(path)

    cache.set(
        private_cards=[17, 16],
        public_cards=[8, 0, 4],
        result=sample_result(0.62),
        bucket=3,
    )

    result = cache.get(
        private_cards=[16, 17],
        public_cards=[0, 4, 8],
    )

    assert result["equity"] == 0.62
    assert result["bucket"] == 3

    cache.close()


def test_equity_cache_contains(tmp_path):
    path = tmp_path / "equity_cache.sqlite"

    cache = EquityCache(path)

    assert cache.contains([16, 17], [0, 4, 8]) is False

    cache.set(
        private_cards=[16, 17],
        public_cards=[0, 4, 8],
        result=sample_result(0.75),
        bucket=4,
    )

    assert cache.contains([16, 17], [0, 4, 8]) is True

    cache.close()


def test_equity_cache_missing_key_raises(tmp_path):
    path = tmp_path / "equity_cache.sqlite"

    cache = EquityCache(path)

    with pytest.raises(KeyError):
        cache.get([16, 17], [0, 4, 8])

    cache.close()


def test_equity_cache_count_by_board_size(tmp_path):
    path = tmp_path / "equity_cache.sqlite"

    cache = EquityCache(path)

    cache.set([16, 17], [], sample_result(0.70), bucket=3)
    cache.set([16, 17], [0, 4, 8], sample_result(0.75), bucket=4)
    cache.set([16, 17], [0, 4, 8, 12], sample_result(0.65), bucket=3)

    assert cache.count() == 3
    assert cache.count(board_size=0) == 1
    assert cache.count(board_size=3) == 1
    assert cache.count(board_size=4) == 1
    assert cache.count(board_size=5) == 0

    cache.close()


def test_equity_cache_set_many(tmp_path):
    path = tmp_path / "equity_cache.sqlite"

    cache = EquityCache(path)

    records = [
        ([16, 17], [], sample_result(0.70), 3),
        ([16, 17], [0, 4, 8], sample_result(0.75), 4),
        ([12, 13], [1, 5, 9, 14], sample_result(0.40), 1),
    ]

    cache.set_many(records)

    assert cache.count() == 3
    assert cache.get([16, 17], [])["bucket"] == 3
    assert cache.get([16, 17], [0, 4, 8])["bucket"] == 4
    assert cache.get([12, 13], [1, 5, 9, 14])["bucket"] == 1

    cache.close()


def test_equity_cache_context_manager(tmp_path):
    path = tmp_path / "equity_cache.sqlite"

    with EquityCache(path) as cache:
        cache.set([16, 17], [], sample_result(0.70), bucket=3)
        assert cache.count() == 1