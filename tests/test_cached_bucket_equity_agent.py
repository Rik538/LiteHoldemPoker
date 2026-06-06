# -*- coding: utf-8 -*-
"""
Created on Fri Jun  5 19:53:32 2026

@author: Richard
"""

import pytest

from lite_holdem_ai.agents.cached_bucket_equity_agent import CachedBucketEquityAgent
from lite_holdem_ai.equity.cache import EquityCache
from lite_holdem_ai.game.actions import Action
from lite_holdem_ai.game.environment import LiteHoldemEnv


def add_cache_entry(cache, private_cards, public_cards, equity, bucket):
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


def test_cached_bucket_equity_agent_can_be_constructed(tmp_path):
    cache_path = tmp_path / "equity_cache.sqlite"

    with EquityCache(cache_path) as cache:
        add_cache_entry(cache, [16, 17], [], equity=0.85, bucket=4)

    agent = CachedBucketEquityAgent(
        name="Cached Bucket Test",
        cache_path=cache_path,
    )

    assert agent.name == "Cached Bucket Test"

    agent.close()


def test_cached_bucket_equity_agent_raises_with_no_legal_actions(tmp_path):
    cache_path = tmp_path / "equity_cache.sqlite"

    with EquityCache(cache_path) as cache:
        add_cache_entry(cache, [16, 17], [], equity=0.85, bucket=4)

    agent = CachedBucketEquityAgent(cache_path=cache_path)

    observation = {
        "private_cards": [16, 17],
        "public_cards": [],
        "pot": 3,
        "amount_to_call": 0,
    }

    with pytest.raises(ValueError):
        agent.select_action(observation, legal_actions=[])

    agent.close()


def test_cached_bucket_agent_bets_premium_when_free(tmp_path):
    cache_path = tmp_path / "equity_cache.sqlite"

    with EquityCache(cache_path) as cache:
        add_cache_entry(cache, [16, 17], [], equity=0.85, bucket=4)

    agent = CachedBucketEquityAgent(cache_path=cache_path)

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


def test_cached_bucket_agent_bets_strong_when_free(tmp_path):
    cache_path = tmp_path / "equity_cache.sqlite"

    with EquityCache(cache_path) as cache:
        add_cache_entry(cache, [12, 16], [], equity=0.65, bucket=3)

    agent = CachedBucketEquityAgent(cache_path=cache_path)

    observation = {
        "private_cards": [12, 16],
        "public_cards": [],
        "pot": 3,
        "amount_to_call": 0,
    }

    legal_actions = [Action.CHECK_CALL, Action.BET_RAISE]

    action = agent.select_action(observation, legal_actions)

    assert action == Action.BET_RAISE

    agent.close()


def test_cached_bucket_agent_checks_medium_when_free(tmp_path):
    cache_path = tmp_path / "equity_cache.sqlite"

    with EquityCache(cache_path) as cache:
        add_cache_entry(cache, [8, 12], [], equity=0.50, bucket=2)

    agent = CachedBucketEquityAgent(cache_path=cache_path)

    observation = {
        "private_cards": [8, 12],
        "public_cards": [],
        "pot": 3,
        "amount_to_call": 0,
    }

    legal_actions = [Action.CHECK_CALL, Action.BET_RAISE]

    action = agent.select_action(observation, legal_actions)

    assert action == Action.CHECK_CALL

    agent.close()


def test_cached_bucket_agent_checks_trash_when_free(tmp_path):
    cache_path = tmp_path / "equity_cache.sqlite"

    with EquityCache(cache_path) as cache:
        add_cache_entry(cache, [0, 1], [], equity=0.20, bucket=0)

    agent = CachedBucketEquityAgent(cache_path=cache_path)

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


def test_cached_bucket_agent_raises_premium_facing_bet(tmp_path):
    cache_path = tmp_path / "equity_cache.sqlite"

    with EquityCache(cache_path) as cache:
        add_cache_entry(cache, [16, 17], [], equity=0.85, bucket=4)

    agent = CachedBucketEquityAgent(cache_path=cache_path)

    observation = {
        "private_cards": [16, 17],
        "public_cards": [],
        "pot": 10,
        "amount_to_call": 2,
    }

    legal_actions = [Action.FOLD, Action.CHECK_CALL, Action.BET_RAISE]

    action = agent.select_action(observation, legal_actions)

    assert action == Action.BET_RAISE

    agent.close()


def test_cached_bucket_agent_calls_strong_if_raise_not_available(tmp_path):
    cache_path = tmp_path / "equity_cache.sqlite"

    with EquityCache(cache_path) as cache:
        add_cache_entry(cache, [12, 16], [], equity=0.65, bucket=3)

    agent = CachedBucketEquityAgent(cache_path=cache_path)

    observation = {
        "private_cards": [12, 16],
        "public_cards": [],
        "pot": 10,
        "amount_to_call": 2,
    }

    legal_actions = [Action.FOLD, Action.CHECK_CALL]

    action = agent.select_action(observation, legal_actions)

    assert action == Action.CHECK_CALL

    agent.close()


def test_cached_bucket_agent_calls_medium_when_pot_odds_good(tmp_path):
    cache_path = tmp_path / "equity_cache.sqlite"

    with EquityCache(cache_path) as cache:
        add_cache_entry(cache, [8, 12], [], equity=0.50, bucket=2)

    agent = CachedBucketEquityAgent(cache_path=cache_path)

    observation = {
        "private_cards": [8, 12],
        "public_cards": [],
        "pot": 10,
        "amount_to_call": 2,
    }

    legal_actions = [Action.FOLD, Action.CHECK_CALL, Action.BET_RAISE]

    action = agent.select_action(observation, legal_actions)

    assert action == Action.CHECK_CALL

    agent.close()


def test_cached_bucket_agent_folds_medium_when_pot_odds_bad(tmp_path):
    cache_path = tmp_path / "equity_cache.sqlite"

    with EquityCache(cache_path) as cache:
        add_cache_entry(cache, [8, 12], [], equity=0.50, bucket=2)

    agent = CachedBucketEquityAgent(cache_path=cache_path)

    observation = {
        "private_cards": [8, 12],
        "public_cards": [],
        "pot": 2,
        "amount_to_call": 10,
    }

    legal_actions = [Action.FOLD, Action.CHECK_CALL, Action.BET_RAISE]

    action = agent.select_action(observation, legal_actions)

    assert action == Action.FOLD

    agent.close()


def test_cached_bucket_agent_folds_trash_facing_bet(tmp_path):
    cache_path = tmp_path / "equity_cache.sqlite"

    with EquityCache(cache_path) as cache:
        add_cache_entry(cache, [0, 1], [], equity=0.20, bucket=0)

    agent = CachedBucketEquityAgent(cache_path=cache_path)

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


def test_cached_bucket_agent_missing_cache_entry_raises_key_error(tmp_path):
    cache_path = tmp_path / "equity_cache.sqlite"

    EquityCache(cache_path).close()

    agent = CachedBucketEquityAgent(cache_path=cache_path)

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


def test_cached_bucket_agent_can_play_one_preflop_action_from_env(tmp_path):
    cache_path = tmp_path / "equity_cache.sqlite"

    env = LiteHoldemEnv()
    observation = env.reset()

    private_cards = observation["private_cards"]
    public_cards = observation["public_cards"]

    with EquityCache(cache_path) as cache:
        add_cache_entry(
            cache,
            private_cards=private_cards,
            public_cards=public_cards,
            equity=0.65,
            bucket=3,
        )

    agent = CachedBucketEquityAgent(cache_path=cache_path)

    legal_actions = env.legal_actions()
    action = agent.select_action(observation, legal_actions)

    assert action in legal_actions

    agent.close()