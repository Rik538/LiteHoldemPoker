# -*- coding: utf-8 -*-
"""
Created on Tue Jun  2 18:10:37 2026

@author: Richard
"""

import pickle

import pytest

from lite_holdem_ai.agents.equity_agent import EquityAgent
from lite_holdem_ai.game.actions import Action
from lite_holdem_ai.game.environment import LiteHoldemEnv


def make_test_cache(path):
    """
    Creates a complete enough fake preflop cache for tests.

    We do not need exact equity values here. These tests check agent behaviour,
    cache loading, legal-action selection, and integration.
    """
    cache = {}

    for c1 in range(20):
        for c2 in range(c1 + 1, 20):
            # Give stronger-looking high-card hands higher fake equity.
            score = (c1 // 4 + c2 // 4) / 8
            equity = max(0.05, min(0.95, score))

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


def test_equity_agent_can_be_constructed_with_cache(tmp_path):
    cache_path = tmp_path / "preflop_equity_cache.pkl"
    make_test_cache(cache_path)

    agent = EquityAgent(
        name="Equity Test",
        cache_path=cache_path,
    )

    assert agent.name == "Equity Test"
    assert len(agent.preflop_cache) == 190


def test_equity_agent_raises_if_no_cache_and_not_building(tmp_path):
    missing_path = tmp_path / "missing_cache.pkl"

    with pytest.raises(FileNotFoundError):
        EquityAgent(
            name="Equity Test",
            cache_path=missing_path,
            build_cache_if_missing=False,
        )


def test_equity_agent_selects_legal_action_preflop(tmp_path):
    cache_path = tmp_path / "preflop_equity_cache.pkl"
    make_test_cache(cache_path)

    agent = EquityAgent(
        name="Equity Test",
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


def test_equity_agent_value_bets_high_equity_preflop(tmp_path):
    cache_path = tmp_path / "preflop_equity_cache.pkl"

    cache = {
        (16, 17): {
            "wins": 80,
            "losses": 20,
            "splits": 0,
            "total": 100,
            "equity": 0.80,
        }
    }

    with open(cache_path, "wb") as f:
        pickle.dump(cache, f)

    agent = EquityAgent(
        name="Equity Test",
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


def test_equity_agent_checks_low_equity_when_free(tmp_path):
    cache_path = tmp_path / "preflop_equity_cache.pkl"

    cache = {
        (0, 1): {
            "wins": 20,
            "losses": 80,
            "splits": 0,
            "total": 100,
            "equity": 0.20,
        }
    }

    with open(cache_path, "wb") as f:
        pickle.dump(cache, f)

    agent = EquityAgent(
        name="Equity Test",
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


def test_equity_agent_calls_when_equity_beats_pot_odds(tmp_path):
    cache_path = tmp_path / "preflop_equity_cache.pkl"

    cache = {
        (8, 9): {
            "wins": 60,
            "losses": 40,
            "splits": 0,
            "total": 100,
            "equity": 0.60,
        }
    }

    with open(cache_path, "wb") as f:
        pickle.dump(cache, f)

    agent = EquityAgent(
        name="Equity Test",
        cache_path=cache_path,
    )

    observation = {
        "private_cards": [8, 9],
        "public_cards": [],
        "pot": 10,
        "amount_to_call": 2,
    }

    legal_actions = [Action.FOLD, Action.CHECK_CALL, Action.BET_RAISE]

    action = agent.select_action(observation, legal_actions)

    assert action in [Action.CHECK_CALL, Action.BET_RAISE]


def test_equity_agent_folds_when_equity_below_pot_odds(tmp_path):
    cache_path = tmp_path / "preflop_equity_cache.pkl"

    cache = {
        (0, 1): {
            "wins": 10,
            "losses": 90,
            "splits": 0,
            "total": 100,
            "equity": 0.10,
        }
    }

    with open(cache_path, "wb") as f:
        pickle.dump(cache, f)

    agent = EquityAgent(
        name="Equity Test",
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


def test_equity_agent_raises_with_no_legal_actions(tmp_path):
    cache_path = tmp_path / "preflop_equity_cache.pkl"
    make_test_cache(cache_path)

    agent = EquityAgent(
        name="Equity Test",
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


def test_equity_agent_pot_odds():
    cache_path = None

    # Avoid needing cache construction for this specific utility test by
    # creating a temporary minimal agent through __new__.
    agent = EquityAgent.__new__(EquityAgent)

    assert agent.pot_odds(10, 0) == 0.0
    assert agent.pot_odds(10, 5) == pytest.approx(5 / 15)


def test_equity_result_is_between_zero_and_one(tmp_path):
    cache_path = tmp_path / "preflop_equity_cache.pkl"
    make_test_cache(cache_path)

    agent = EquityAgent(
        name="Equity Test",
        cache_path=cache_path,
    )

    result = agent.calculate_equity(
        private_cards=[16, 17],
        public_cards=[],
    )

    assert 0.0 <= result["equity"] <= 1.0
    assert result["total"] > 0


def test_equity_agent_can_play_full_hand_against_random(tmp_path):
    from lite_holdem_ai.agents.random_agent import RandomAgent

    cache_path = tmp_path / "preflop_equity_cache.pkl"
    make_test_cache(cache_path)

    env = LiteHoldemEnv()

    agents = [
        EquityAgent(
            name="Equity",
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