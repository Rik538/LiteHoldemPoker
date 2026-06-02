# -*- coding: utf-8 -*-
"""
Created on Sun May 31 17:31:09 2026

@author: Richard
"""

import pytest

from lite_holdem_ai.game.actions import Action
from lite_holdem_ai.game.environment import LiteHoldemEnv


def choose_safe_action(legal_actions):
    """
    Conservative policy for tests:
    prefer check/call, otherwise take first legal action.
    """
    if Action.CHECK_CALL in legal_actions:
        return Action.CHECK_CALL

    return legal_actions[0]


def play_until_terminal(env, max_steps=200):
    obs = env.reset()

    for _ in range(max_steps):
        if env.is_terminal():
            break

        legal_actions = env.legal_actions()
        assert len(legal_actions) > 0

        action = choose_safe_action(legal_actions)

        obs, reward, done, info = env.step(action)

        assert isinstance(reward, list)
        assert len(reward) == 2
        assert isinstance(done, bool)
        assert isinstance(info, dict)

    return env


def test_env_imports():
    assert LiteHoldemEnv is not None


def test_env_reset_returns_observation():
    env = LiteHoldemEnv()

    obs = env.reset()

    assert obs is not None
    assert "pot" in obs
    assert "current_player" in obs
    assert "legal_actions" in obs
    assert "public_cards" in obs


def test_env_current_player_property_is_valid():
    env = LiteHoldemEnv()
    env.reset()

    assert env.current_player in [0, 1]


def test_env_legal_actions_not_empty_after_reset():
    env = LiteHoldemEnv()
    env.reset()

    legal_actions = env.legal_actions()

    assert len(legal_actions) > 0
    assert all(isinstance(action, Action) for action in legal_actions)


def test_env_step_returns_transition_tuple():
    env = LiteHoldemEnv()
    obs = env.reset()

    legal_actions = env.legal_actions()
    action = choose_safe_action(legal_actions)

    next_obs, reward, done, info = env.step(action)

    assert isinstance(reward, list)
    assert len(reward) == 2
    assert isinstance(done, bool)
    assert isinstance(info, dict)

    if done:
        assert next_obs is None
    else:
        assert next_obs is not None


def test_env_observe_each_player():
    env = LiteHoldemEnv()
    env.reset()

    obs0 = env.observe(0)
    obs1 = env.observe(1)

    assert obs0 is not None
    assert obs1 is not None

    assert "public_cards" in obs0
    assert "public_cards" in obs1
    assert "pot" in obs0
    assert "pot" in obs1

    # Private cards should usually differ.
    assert obs0 != obs1


def test_env_can_play_until_terminal_with_check_call_policy():
    env = LiteHoldemEnv()

    play_until_terminal(env, max_steps=200)

    assert env.is_terminal()
    assert sum(env.payoffs()) == 0


def test_env_fold_terminal_payoffs_are_zero_sum():
    env = LiteHoldemEnv()
    env.reset()

    if Action.BET_RAISE not in env.legal_actions():
        pytest.skip("BET_RAISE not legal in initial state")

    env.step(Action.BET_RAISE)

    if Action.FOLD not in env.legal_actions():
        pytest.skip("FOLD not legal after bet/raise")

    env.step(Action.FOLD)

    assert env.is_terminal()
    assert sum(env.payoffs()) == 0


def test_env_payoffs_returns_copy_or_valid_list():
    env = LiteHoldemEnv()

    play_until_terminal(env, max_steps=200)

    payoffs = env.payoffs()

    assert isinstance(payoffs, list)
    assert len(payoffs) == 2
    assert sum(payoffs) == 0


def test_env_step_rejects_illegal_action():
    env = LiteHoldemEnv()
    env.reset()

    if Action.FOLD in env.legal_actions():
        pytest.skip("FOLD is legal in this state, cannot test illegal fold")

    with pytest.raises(ValueError):
        env.step(Action.FOLD)