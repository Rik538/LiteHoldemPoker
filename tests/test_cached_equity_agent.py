# -*- coding: utf-8 -*-
"""
Created on Fri Jun  5 19:52:59 2026

@author: Richard
"""

import pytest

from lite_holdem_ai.agents.cached_equity_agent import CachedEquityAgent
from lite_holdem_ai.agents.random_agent import RandomAgent
from lite_holdem_ai.equity.cache import EquityCache
from lite_holdem_ai.game.actions import Action
from lite_holdem_ai.game.environment import LiteHoldemEnv


def add_cache_entry(cache, private_cards, public_cards, equity, bucket=2):
    result = {
        "wins": int(equity * 100),
        "losses": int((1.0 - equity) * 100),
        "splits": 0,
        "total": 100,
        "equity": equity,
    }

    cache.set(
        private_cards=private_cards,
        public_cards=public_cards,
        result=result,
        bucket=bucket,
    )


def make_test_cache(path):
    """
    Creates a small-but-complete fake cache for hands likely to appear in tests.

    For full-hand integration, we insert every private/public combination that
    may occur, using simple fake equity values. This tests lookup/integration,
    not exact equity correctness.
    """
    with EquityCache(path) as cache:
        all_cards = list(range(20))

        # Preflop entries
        for c1 in range(20):
            for c2 in range(c1 + 1, 20):
                private_cards = [c1, c2]
                equity = max(0.05, min(0.95, ((c1 // 4) + (c2 // 4)) / 8))
                bucket = bucket_from_equity_for_test(equity)
                add_cache_entry(cache, private_cards, [], equity, bucket)

        # Add a wider set of postflop entries for integration tests.
        # This is not the full real cache, but enough for deterministic tests
        # if the exact board appears from env.reset. To avoid brittle full-hand
        # tests, we also have direct unit tests below.
        known_private_hands = [
            [0, 1],
            [4, 5],
            [8, 9],
            [12, 13],
            [16, 17],
        ]
        known_boards = [
            [0, 4, 8],
            [0, 4, 8, 12],
            [0, 4, 8, 12, 16],
            [1, 5, 9],
            [1, 5, 9, 13],
            [1, 5, 9, 13, 17],
        ]

        for private_cards in known_private_hands:
            for public_cards in known_boards:
                if set(private_cards).isdisjoint(public_cards):
                    add_cache_entry(
                        cache,
                        private_cards=private_cards,
                        public_cards=public_cards,
                        equity=0.60,
                        bucket=3,
                    )


def bucket_from_equity_for_test(equity):
    if equity < 0.30:
        return 0
    if equity < 0.45:
        return 1
    if equity < 0.58:
        return 2
    if equity < 0.72:
        return 3
    return 4


def test_cached_equity_agent_can_be_constructed(tmp_path):
    cache_path = tmp_path / "equity_cache.sqlite"

    with EquityCache(cache_path) as cache:
        add_cache_entry(cache, [16, 17], [], equity=0.80, bucket=4)

    agent = CachedEquityAgent(
        name="Cached Equity Test",
        cache_path=cache_path,
    )

    assert agent.name == "Cached Equity Test"

    agent.close()


def test_cached_equity_agent_raises_with_no_legal_actions(tmp_path):
    cache_path = tmp_path / "equity_cache.sqlite"

    with EquityCache(cache_path) as cache:
        add_cache_entry(cache, [16, 17], [], equity=0.80, bucket=4)

    agent = CachedEquityAgent(cache_path=cache_path)

    observation = {
        "private_cards": [16, 17],
        "public_cards": [],
        "pot": 3,
        "amount_to_call": 0,
    }

    with pytest.raises(ValueError):
        agent.select_action(observation, legal_actions=[])

    agent.close()


def test_cached_equity_agent_value_bets_high_equity_when_free(tmp_path):
    cache_path = tmp_path / "equity_cache.sqlite"

    with EquityCache(cache_path) as cache:
        add_cache_entry(cache, [16, 17], [], equity=0.80, bucket=4)

    agent = CachedEquityAgent(cache_path=cache_path)

    observation = {
        "private_cards": [16, 17],
        "public_cards": [],
        "pot": 3,
        "amount_to_call": 0,
    }

    legal_actions = [Action.CHECK_CALL, Action.BET_RAISE]

    action = agent.select_action(observation, legal_actions)

    assert action == Action.BET_RAISE

    agent.close()


def test_cached_equity_agent_checks_low_equity_when_free(tmp_path):
    cache_path = tmp_path / "equity_cache.sqlite"

    with EquityCache(cache_path) as cache:
        add_cache_entry(cache, [0, 1], [], equity=0.20, bucket=0)

    agent = CachedEquityAgent(cache_path=cache_path)

    observation = {
        "private_cards": [0, 1],
        "public_cards": [],
        "pot": 3,
        "amount_to_call": 0,
    }

    legal_actions = [Action.CHECK_CALL, Action.BET_RAISE]

    action = agent.select_action(observation, legal_actions)

    assert action == Action.CHECK_CALL

    agent.close()


def test_cached_equity_agent_calls_when_equity_beats_pot_odds(tmp_path):
    cache_path = tmp_path / "equity_cache.sqlite"

    with EquityCache(cache_path) as cache:
        add_cache_entry(cache, [8, 9], [], equity=0.60, bucket=3)

    agent = CachedEquityAgent(cache_path=cache_path)

    observation = {
        "private_cards": [8, 9],
        "public_cards": [],
        "pot": 10,
        "amount_to_call": 2,
    }

    legal_actions = [Action.FOLD, Action.CHECK_CALL, Action.BET_RAISE]

    action = agent.select_action(observation, legal_actions)

    assert action in [Action.CHECK_CALL, Action.BET_RAISE]

    agent.close()


def test_cached_equity_agent_folds_when_equity_below_pot_odds(tmp_path):
    cache_path = tmp_path / "equity_cache.sqlite"

    with EquityCache(cache_path) as cache:
        add_cache_entry(cache, [0, 1], [], equity=0.10, bucket=0)

    agent = CachedEquityAgent(cache_path=cache_path)

    observation = {
        "private_cards": [0, 1],
        "public_cards": [],
        "pot": 4,
        "amount_to_call": 4,
    }

    legal_actions = [Action.FOLD, Action.CHECK_CALL, Action.BET_RAISE]

    action = agent.select_action(observation, legal_actions)

    assert action == Action.FOLD

    agent.close()


def test_cached_equity_agent_missing_cache_entry_raises_key_error(tmp_path):
    cache_path = tmp_path / "equity_cache.sqlite"

    # Create empty valid cache.
    EquityCache(cache_path).close()

    agent = CachedEquityAgent(cache_path=cache_path)

    observation = {
        "private_cards": [16, 17],
        "public_cards": [],
        "pot": 3,
        "amount_to_call": 0,
    }

    legal_actions = [Action.CHECK_CALL, Action.BET_RAISE]

    with pytest.raises(KeyError):
        agent.select_action(observation, legal_actions)

    agent.close()


def test_cached_equity_agent_can_play_one_preflop_action_from_env(tmp_path):
    cache_path = tmp_path / "equity_cache.sqlite"

    env = LiteHoldemEnv()
    observation = env.reset()

    private_cards = observation["private_cards"]
    public_cards = observation["public_cards"]

    with EquityCache(cache_path) as cache:
        add_cache_entry(cache, private_cards, public_cards, equity=0.65, bucket=3)

    agent = CachedEquityAgent(cache_path=cache_path)

    legal_actions = env.legal_actions()
    action = agent.select_action(observation, legal_actions)

    assert action in legal_actions

    agent.close()


def test_cached_equity_agent_pot_odds_utility(tmp_path):
    cache_path = tmp_path / "equity_cache.sqlite"
    EquityCache(cache_path).close()

    agent = CachedEquityAgent(cache_path=cache_path)

    assert agent.pot_odds(10, 0) == 0.0
    assert agent.pot_odds(10, 5) == pytest.approx(5 / 15)

    agent.close()