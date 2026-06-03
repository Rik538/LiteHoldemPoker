# -*- coding: utf-8 -*-
"""
Created on Tue Jun  2 19:53:24 2026

@author: Richard
"""

import pickle

import pytest

from lite_holdem_ai.agents.bucket_equity_agent import BucketEquityAgent
from lite_holdem_ai.agents.random_agent import RandomAgent
from lite_holdem_ai.game.actions import Action
from lite_holdem_ai.game.environment import LiteHoldemEnv


def make_test_cache(path):
    """
    Fake complete preflop cache for fast tests.

    The values do not need to be exact. These tests check:
    - cache loading
    - bucket mapping
    - action selection
    - legal action safety
    - full-hand integration
    """
    cache = {}

    for c1 in range(20):
        for c2 in range(c1 + 1, 20):
            rank_score = (c1 // 4 + c2 // 4) / 8
            equity = max(0.05, min(0.95, rank_score))

            cache[(c1, c2)] = {
                "wins": 1,
                "losses": 1,
                "splits": 0,
                "total": 2,
                "equity": equity,
            }

    with open(path, "wb") as f:
        pickle.dump(cache, f)

    return cache


def make_cache_with_one_hand(path, hand, equity):
    cache = {
        tuple(sorted(hand)): {
            "wins": int(equity * 100),
            "losses": int((1.0 - equity) * 100),
            "splits": 0,
            "total": 100,
            "equity": equity,
        }
    }

    with open(path, "wb") as f:
        pickle.dump(cache, f)

    return cache


def test_bucket_equity_agent_can_be_constructed_with_cache(tmp_path):
    cache_path = tmp_path / "preflop_equity_cache.pkl"
    make_test_cache(cache_path)

    agent = BucketEquityAgent(
        name="Bucket Equity Test",
        cache_path=cache_path,
    )

    assert agent.name == "Bucket Equity Test"
    assert len(agent.preflop_cache) == 190


def test_bucket_equity_agent_raises_if_no_cache_and_not_building(tmp_path):
    missing_path = tmp_path / "missing_cache.pkl"

    with pytest.raises(FileNotFoundError):
        BucketEquityAgent(
            name="Bucket Equity Test",
            cache_path=missing_path,
            build_cache_if_missing=False,
        )


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
        (0.95, 4),
    ],
)
def test_bucket_from_equity(equity, expected_bucket, tmp_path):
    cache_path = tmp_path / "preflop_equity_cache.pkl"
    make_test_cache(cache_path)

    agent = BucketEquityAgent(
        name="Bucket Equity Test",
        cache_path=cache_path,
    )

    assert agent.bucket_from_equity(equity) == expected_bucket


def test_bucket_equity_agent_selects_legal_action_preflop(tmp_path):
    cache_path = tmp_path / "preflop_equity_cache.pkl"
    make_test_cache(cache_path)

    agent = BucketEquityAgent(
        name="Bucket Equity Test",
        cache_path=cache_path,
    )

    observation = {
        "private_cards": [16, 17],
        "public_cards": [],
        "pot": 3,
        "amount_to_call": 0,
    }

    legal_actions = [Action.CHECK_CALL, Action.BET_RAISE]

    action = agent.select_action(observation, legal_actions)

    assert action in legal_actions


def test_bucket_equity_agent_bets_premium_when_free(tmp_path):
    cache_path = tmp_path / "preflop_equity_cache.pkl"
    make_cache_with_one_hand(cache_path, hand=[16, 17], equity=0.85)

    agent = BucketEquityAgent(
        name="Bucket Equity Test",
        cache_path=cache_path,
    )

    observation = {
        "private_cards": [16, 17],
        "public_cards": [],
        "pot": 3,
        "amount_to_call": 0,
    }

    legal_actions = [Action.CHECK_CALL, Action.BET_RAISE]

    action = agent.select_action(observation, legal_actions)

    assert action == Action.BET_RAISE


def test_bucket_equity_agent_checks_trash_when_free(tmp_path):
    cache_path = tmp_path / "preflop_equity_cache.pkl"
    make_cache_with_one_hand(cache_path, hand=[0, 1], equity=0.20)

    agent = BucketEquityAgent(
        name="Bucket Equity Test",
        cache_path=cache_path,
    )

    observation = {
        "private_cards": [0, 1],
        "public_cards": [],
        "pot": 3,
        "amount_to_call": 0,
    }

    legal_actions = [Action.CHECK_CALL, Action.BET_RAISE]

    action = agent.select_action(observation, legal_actions)

    assert action == Action.CHECK_CALL


def test_bucket_equity_agent_raises_premium_facing_bet(tmp_path):
    cache_path = tmp_path / "preflop_equity_cache.pkl"
    make_cache_with_one_hand(cache_path, hand=[16, 17], equity=0.85)

    agent = BucketEquityAgent(
        name="Bucket Equity Test",
        cache_path=cache_path,
    )

    observation = {
        "private_cards": [16, 17],
        "public_cards": [],
        "pot": 10,
        "amount_to_call": 2,
    }

    legal_actions = [Action.FOLD, Action.CHECK_CALL, Action.BET_RAISE]

    action = agent.select_action(observation, legal_actions)

    assert action == Action.BET_RAISE


def test_bucket_equity_agent_calls_strong_when_raise_not_available(tmp_path):
    cache_path = tmp_path / "preflop_equity_cache.pkl"
    make_cache_with_one_hand(cache_path, hand=[12, 16], equity=0.65)

    agent = BucketEquityAgent(
        name="Bucket Equity Test",
        cache_path=cache_path,
    )

    observation = {
        "private_cards": [12, 16],
        "public_cards": [],
        "pot": 10,
        "amount_to_call": 2,
    }

    legal_actions = [Action.FOLD, Action.CHECK_CALL]

    action = agent.select_action(observation, legal_actions)

    assert action == Action.CHECK_CALL


def test_bucket_equity_agent_calls_medium_when_pot_odds_good(tmp_path):
    cache_path = tmp_path / "preflop_equity_cache.pkl"
    make_cache_with_one_hand(cache_path, hand=[8, 12], equity=0.50)

    agent = BucketEquityAgent(
        name="Bucket Equity Test",
        cache_path=cache_path,
    )

    observation = {
        "private_cards": [8, 12],
        "public_cards": [],
        "pot": 10,
        "amount_to_call": 2,
    }

    legal_actions = [Action.FOLD, Action.CHECK_CALL, Action.BET_RAISE]

    action = agent.select_action(observation, legal_actions)

    assert action == Action.CHECK_CALL


def test_bucket_equity_agent_folds_medium_when_pot_odds_bad(tmp_path):
    cache_path = tmp_path / "preflop_equity_cache.pkl"
    make_cache_with_one_hand(cache_path, hand=[8, 12], equity=0.50)

    agent = BucketEquityAgent(
        name="Bucket Equity Test",
        cache_path=cache_path,
    )

    observation = {
        "private_cards": [8, 12],
        "public_cards": [],
        "pot": 2,
        "amount_to_call": 10,
    }

    legal_actions = [Action.FOLD, Action.CHECK_CALL, Action.BET_RAISE]

    action = agent.select_action(observation, legal_actions)

    assert action == Action.FOLD


def test_bucket_equity_agent_folds_trash_facing_bet(tmp_path):
    cache_path = tmp_path / "preflop_equity_cache.pkl"
    make_cache_with_one_hand(cache_path, hand=[0, 1], equity=0.20)

    agent = BucketEquityAgent(
        name="Bucket Equity Test",
        cache_path=cache_path,
    )

    observation = {
        "private_cards": [0, 1],
        "public_cards": [],
        "pot": 4,
        "amount_to_call": 4,
    }

    legal_actions = [Action.FOLD, Action.CHECK_CALL, Action.BET_RAISE]

    action = agent.select_action(observation, legal_actions)

    assert action == Action.FOLD


def test_bucket_equity_agent_raises_with_no_legal_actions(tmp_path):
    cache_path = tmp_path / "preflop_equity_cache.pkl"
    make_test_cache(cache_path)

    agent = BucketEquityAgent(
        name="Bucket Equity Test",
        cache_path=cache_path,
    )

    observation = {
        "private_cards": [0, 1],
        "public_cards": [],
        "pot": 3,
        "amount_to_call": 0,
    }

    with pytest.raises(ValueError):
        agent.select_action(observation, legal_actions=[])


def test_bucket_equity_agent_result_is_between_zero_and_one(tmp_path):
    cache_path = tmp_path / "preflop_equity_cache.pkl"
    make_test_cache(cache_path)

    agent = BucketEquityAgent(
        name="Bucket Equity Test",
        cache_path=cache_path,
    )

    result = agent.calculate_equity(
        private_cards=[16, 17],
        public_cards=[],
    )

    assert 0.0 <= result["equity"] <= 1.0
    assert result["total"] > 0


def test_bucket_equity_agent_can_play_full_hand_against_random(tmp_path):
    cache_path = tmp_path / "preflop_equity_cache.pkl"
    make_test_cache(cache_path)

    env = LiteHoldemEnv()

    agents = [
        BucketEquityAgent(
            name="Bucket Equity",
            cache_path=cache_path,
        ),
        RandomAgent(seed=1, name="Random"),
    ]

    obs = env.reset()

    for _ in range(200):
        if env.is_terminal():
            break

        player = env.current_player
        legal_actions = env.legal_actions()
        observation = env.observe(player)

        action = agents[player].select_action(observation, legal_actions)

        assert action in legal_actions

        obs, reward, done, info = env.step(action)

    assert env.is_terminal()
    assert sum(env.payoffs()) == 0