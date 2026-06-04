# -*- coding: utf-8 -*-
"""
Created on Wed Jun  3 20:02:17 2026

@author: Richard
"""

import pytest

from lite_holdem_ai.equity.builder import (
    EquityCacheBuilder,
    bucket_from_equity,
    build_equity_cache,
)
from lite_holdem_ai.equity.cache import EquityCache


@pytest.mark.parametrize(
    "equity, expected_bucket",
    [
        (0.00, 0),
        (0.29, 0),
        (0.30, 1),
        (0.44, 1),
        (0.45, 2),
        (0.57, 2),
        (0.58, 3),
        (0.71, 3),
        (0.72, 4),
        (0.99, 4),
    ],
)
def test_bucket_from_equity(equity, expected_bucket):
    assert bucket_from_equity(equity) == expected_bucket


def test_equity_builder_can_be_constructed():
    builder = EquityCacheBuilder()

    assert builder is not None


def test_equity_builder_calculates_preflop_equity_result():
    builder = EquityCacheBuilder()

    result = builder.calculate_equity(
        private_cards=[16, 17],
        public_cards=[],
    )

    assert 0.0 <= result["equity"] <= 1.0
    assert result["total"] > 0
    assert result["wins"] + result["losses"] + result["splits"] == result["total"]


def test_equity_builder_calculates_flop_equity_result():
    builder = EquityCacheBuilder()

    result = builder.calculate_equity(
        private_cards=[16, 17],
        public_cards=[0, 4, 8],
    )

    assert 0.0 <= result["equity"] <= 1.0
    assert result["total"] > 0
    assert result["wins"] + result["losses"] + result["splits"] == result["total"]


def test_equity_builder_calculates_turn_equity_result():
    builder = EquityCacheBuilder()

    result = builder.calculate_equity(
        private_cards=[16, 17],
        public_cards=[0, 4, 8, 12],
    )

    assert 0.0 <= result["equity"] <= 1.0
    assert result["total"] > 0
    assert result["wins"] + result["losses"] + result["splits"] == result["total"]


def test_equity_builder_calculates_river_equity_result():
    builder = EquityCacheBuilder()

    result = builder.calculate_equity(
        private_cards=[16, 17],
        public_cards=[0, 4, 8, 12, 1],
    )

    assert 0.0 <= result["equity"] <= 1.0
    assert result["total"] > 0
    assert result["wins"] + result["losses"] + result["splits"] == result["total"]


def test_equity_builder_rejects_invalid_public_card_count():
    builder = EquityCacheBuilder()

    with pytest.raises(ValueError):
        builder.calculate_equity(
            private_cards=[16, 17],
            public_cards=[0, 4],
        )


def test_build_equity_cache_preflop_only_with_fake_equity(tmp_path, monkeypatch):
    path = tmp_path / "equity_cache.sqlite"

    fake_result = {
        "wins": 1,
        "losses": 1,
        "splits": 0,
        "total": 2,
        "equity": 0.5,
    }

    monkeypatch.setattr(
        EquityCacheBuilder,
        "calculate_equity",
        lambda self, private_cards, public_cards: fake_result,
    )

    build_equity_cache(
        path=path,
        board_sizes=[0],
        batch_size=50,
        clear_existing=True,
        verbose=False,
    )

    with EquityCache(path) as cache:
        assert cache.count(board_size=0) == 190
        assert cache.count() == 190

        result = cache.get([16, 17], [])
        assert result["equity"] == 0.5
        assert result["bucket"] == 2


def test_builder_skips_existing_records_with_fake_equity(tmp_path, monkeypatch):
    path = tmp_path / "equity_cache.sqlite"

    fake_result = {
        "wins": 1,
        "losses": 1,
        "splits": 0,
        "total": 2,
        "equity": 0.5,
    }

    monkeypatch.setattr(
        EquityCacheBuilder,
        "calculate_equity",
        lambda self, private_cards, public_cards: fake_result,
    )

    build_equity_cache(
        path=path,
        board_sizes=[0],
        batch_size=50,
        clear_existing=True,
        verbose=False,
    )

    with EquityCache(path) as cache:
        first_count = cache.count(board_size=0)

    build_equity_cache(
        path=path,
        board_sizes=[0],
        batch_size=50,
        clear_existing=False,
        verbose=False,
    )

    with EquityCache(path) as cache:
        second_count = cache.count(board_size=0)

    assert first_count == 190
    assert second_count == 190


def test_builder_rejects_invalid_board_size(tmp_path):
    path = tmp_path / "equity_cache.sqlite"

    with pytest.raises(ValueError):
        build_equity_cache(
            path=path,
            board_sizes=[2],
            verbose=False,
        )