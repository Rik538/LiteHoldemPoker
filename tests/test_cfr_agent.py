# -*- coding: utf-8 -*-
"""
Created on Sun Jun  7 13:10:40 2026

@author: Richard
"""

import pytest

from lite_holdem_ai.cfr.agent import CFRAgent
from lite_holdem_ai.cfr.infoset import EquityBucketInfosetKeyBuilder
from lite_holdem_ai.cfr.node import ACTION_INDEX, CFRNode
from lite_holdem_ai.game.actions import Action
from lite_holdem_ai.game.environment import LiteHoldemEnv


class ConstantBucketProvider:
    def __init__(self, bucket=2):
        self.bucket = bucket

    def get_bucket(self, private_cards, public_cards):
        return self.bucket


def make_infoset_builder(bucket=2):
    bucket_provider = ConstantBucketProvider(bucket=bucket)
    return EquityBucketInfosetKeyBuilder(bucket_provider)


def make_observation_and_key():
    env = LiteHoldemEnv()
    observation = env.reset()

    infoset_builder = make_infoset_builder()
    key = infoset_builder.from_observation(observation)

    return observation, env.legal_actions(), infoset_builder, key


def make_node_for_actions(legal_actions, preferred_action=None):
    node = CFRNode()
    node.legal_actions = legal_actions.copy()

    if preferred_action is None:
        for action in legal_actions:
            idx = ACTION_INDEX[action]
            node.strategy_sum[idx] = 1.0
    else:
        idx = ACTION_INDEX[preferred_action]
        node.strategy_sum[idx] = 10.0

    return node


def test_cfr_agent_can_be_constructed():
    infoset_builder = make_infoset_builder()

    agent = CFRAgent(
        nodes={},
        infoset_builder=infoset_builder,
        name="CFR Test",
        seed=1,
    )

    assert agent.name == "CFR Test"
    assert agent.nodes == {}
    assert agent.infoset_builder is infoset_builder
    assert agent.missing_nodes == 0


def test_cfr_agent_raises_with_no_legal_actions():
    infoset_builder = make_infoset_builder()

    agent = CFRAgent(
        nodes={},
        infoset_builder=infoset_builder,
        name="CFR Test",
        seed=1,
    )

    with pytest.raises(ValueError):
        agent.select_action(observation={}, legal_actions=[])


def test_cfr_agent_selects_legal_action_from_known_node():
    observation, legal_actions, infoset_builder, key = make_observation_and_key()

    node = make_node_for_actions(legal_actions)

    agent = CFRAgent(
        nodes={key: node},
        infoset_builder=infoset_builder,
        name="CFR Test",
        seed=1,
    )

    for _ in range(50):
        action = agent.select_action(observation, legal_actions)
        assert action in legal_actions

    assert agent.missing_nodes == 0


def test_cfr_agent_uses_average_strategy_preference():
    observation, legal_actions, infoset_builder, key = make_observation_and_key()

    if Action.BET_RAISE not in legal_actions:
        pytest.skip("BET_RAISE not legal in initial state")

    node = make_node_for_actions(
        legal_actions=legal_actions,
        preferred_action=Action.BET_RAISE,
    )

    agent = CFRAgent(
        nodes={key: node},
        infoset_builder=infoset_builder,
        name="CFR Test",
        seed=1,
    )

    action = agent.select_action(observation, legal_actions)

    assert action == Action.BET_RAISE
    assert agent.missing_nodes == 0


def test_cfr_agent_falls_back_when_node_missing():
    observation, legal_actions, infoset_builder, key = make_observation_and_key()

    agent = CFRAgent(
        nodes={},
        infoset_builder=infoset_builder,
        name="CFR Test",
        seed=1,
    )

    action = agent.select_action(observation, legal_actions)

    assert action in legal_actions
    assert agent.missing_nodes == 1


def test_cfr_agent_missing_node_fallback_is_seeded():
    observation, legal_actions, infoset_builder, key = make_observation_and_key()

    agent_a = CFRAgent(
        nodes={},
        infoset_builder=infoset_builder,
        name="CFR A",
        seed=123,
    )

    agent_b = CFRAgent(
        nodes={},
        infoset_builder=infoset_builder,
        name="CFR B",
        seed=123,
    )

    actions_a = [
        agent_a.select_action(observation, legal_actions)
        for _ in range(10)
    ]

    actions_b = [
        agent_b.select_action(observation, legal_actions)
        for _ in range(10)
    ]

    assert actions_a == actions_b


def test_cfr_agent_can_play_one_action_from_env():
    env = LiteHoldemEnv()
    observation = env.reset()
    legal_actions = env.legal_actions()

    infoset_builder = make_infoset_builder()
    key = infoset_builder.from_observation(observation)

    node = make_node_for_actions(legal_actions)

    agent = CFRAgent(
        nodes={key: node},
        infoset_builder=infoset_builder,
        name="CFR Test",
        seed=1,
    )

    action = agent.select_action(observation, legal_actions)

    assert action in legal_actions

    next_obs, reward, done, info = env.step(action)

    assert isinstance(reward, list)
    assert len(reward) == 2
    assert isinstance(done, bool)
    assert isinstance(info, dict)


def test_cfr_agent_can_play_full_hand_against_random_fallback():
    env = LiteHoldemEnv()
    infoset_builder = make_infoset_builder()

    agents = [
        CFRAgent(
            nodes={},
            infoset_builder=infoset_builder,
            name="CFR",
            seed=1,
        ),
        CFRAgent(
            nodes={},
            infoset_builder=infoset_builder,
            name="CFR 2",
            seed=2,
        ),
    ]

    env.reset()

    for _ in range(200):
        if env.is_terminal():
            break

        player = env.current_player
        observation = env.observe(player)
        legal_actions = env.legal_actions()

        action = agents[player].select_action(observation, legal_actions)

        assert action in legal_actions

        env.step(action)

    assert env.is_terminal()
    assert sum(env.payoffs()) == 0