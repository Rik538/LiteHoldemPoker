# -*- coding: utf-8 -*-
"""
Created on Tue Jun  2 17:39:24 2026

@author: Richard
"""

import pytest

from lite_holdem_ai.agents.random_agent import RandomAgent
from lite_holdem_ai.agents.passive_agent import PassiveAgent
from lite_holdem_ai.agents.aggressive_agent import AggressiveAgent
from lite_holdem_ai.agents.heuristic_agent import HeuristicAgent
from lite_holdem_ai.game.actions import Action
from lite_holdem_ai.game.environment import LiteHoldemEnv


AGENT_CLASSES = [
    RandomAgent,
    PassiveAgent,
    AggressiveAgent,
    HeuristicAgent,
]


def make_agent(agent_cls, seed=1, name=None):
    try:
        return agent_cls(seed=seed, name=name)
    except TypeError:
        try:
            return agent_cls(seed=seed)
        except TypeError:
            try:
                return agent_cls(name=name)
            except TypeError:
                return agent_cls()


@pytest.mark.parametrize("agent_cls", AGENT_CLASSES)
def test_agent_can_be_constructed(agent_cls):
    agent = make_agent(agent_cls)

    assert agent is not None
    assert hasattr(agent, "select_action")


@pytest.mark.parametrize("agent_cls", AGENT_CLASSES)
def test_agent_selects_legal_action_after_reset(agent_cls):
    env = LiteHoldemEnv()
    obs = env.reset()

    agent = make_agent(agent_cls, seed=1)
    legal_actions = env.legal_actions()

    for _ in range(50):
        action = agent.select_action(obs, legal_actions)
        assert action in legal_actions


@pytest.mark.parametrize("agent_cls", AGENT_CLASSES)
def test_agent_selects_legal_action_when_facing_bet(agent_cls):
    env = LiteHoldemEnv()
    env.reset()

    if Action.BET_RAISE not in env.legal_actions():
        pytest.skip("BET_RAISE not legal in initial state")

    env.step(Action.BET_RAISE)

    player = env.current_player
    obs = env.observe(player)
    legal_actions = env.legal_actions()

    assert len(legal_actions) > 0

    agent = make_agent(agent_cls, seed=1)

    for _ in range(50):
        action = agent.select_action(obs, legal_actions)
        assert action in legal_actions


@pytest.mark.parametrize("agent_cls", AGENT_CLASSES)
def test_agent_can_play_full_hand_against_itself(agent_cls):
    env = LiteHoldemEnv()

    agents = [
        make_agent(agent_cls, seed=1, name="Agent A"),
        make_agent(agent_cls, seed=2, name="Agent B"),
    ]

    obs = env.reset()

    for _ in range(200):
        if env.is_terminal():
            break

        player = env.current_player
        legal_actions = env.legal_actions()
        action = agents[player].select_action(obs, legal_actions)

        assert action in legal_actions

        obs, reward, done, info = env.step(action)

    assert env.is_terminal()
    assert sum(env.payoffs()) == 0


def test_random_agent_raises_with_no_legal_actions():
    agent = RandomAgent(seed=1)

    with pytest.raises(ValueError):
        agent.select_action(observation=None, legal_actions=[])


def test_passive_agent_prefers_check_call():
    agent = PassiveAgent()

    legal_actions = [Action.FOLD, Action.CHECK_CALL, Action.BET_RAISE]

    action = agent.select_action(observation=None, legal_actions=legal_actions)

    assert action == Action.CHECK_CALL


def test_aggressive_agent_prefers_bet_raise():
    agent = AggressiveAgent()

    legal_actions = [Action.CHECK_CALL, Action.BET_RAISE]

    action = agent.select_action(observation=None, legal_actions=legal_actions)

    assert action == Action.BET_RAISE