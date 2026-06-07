# -*- coding: utf-8 -*-
"""
Created on Sat Jun  6 23:32:37 2026

@author: Richard
"""

import pytest

from lite_holdem_ai.cfr.node import ACTION_INDEX, CFRNode
from lite_holdem_ai.game.actions import Action


def test_cfr_node_uniform_strategy_when_no_regrets():
    node = CFRNode()
    legal_actions = [Action.CHECK_CALL, Action.BET_RAISE]

    strategy = node.get_strategy(legal_actions)

    assert strategy[ACTION_INDEX[Action.CHECK_CALL]] == pytest.approx(0.5)
    assert strategy[ACTION_INDEX[Action.BET_RAISE]] == pytest.approx(0.5)
    assert strategy[ACTION_INDEX[Action.FOLD]] == 0.0


def test_cfr_node_uses_positive_regrets():
    node = CFRNode()
    node.regret_sum[ACTION_INDEX[Action.CHECK_CALL]] = 1.0
    node.regret_sum[ACTION_INDEX[Action.BET_RAISE]] = 3.0

    legal_actions = [Action.CHECK_CALL, Action.BET_RAISE]

    strategy = node.get_strategy(legal_actions)

    assert strategy[ACTION_INDEX[Action.CHECK_CALL]] == pytest.approx(0.25)
    assert strategy[ACTION_INDEX[Action.BET_RAISE]] == pytest.approx(0.75)


def test_cfr_node_ignores_illegal_actions():
    node = CFRNode()
    node.regret_sum[ACTION_INDEX[Action.FOLD]] = 100.0

    legal_actions = [Action.CHECK_CALL, Action.BET_RAISE]

    strategy = node.get_strategy(legal_actions)

    assert strategy[ACTION_INDEX[Action.FOLD]] == 0.0
    assert strategy[ACTION_INDEX[Action.CHECK_CALL]] == pytest.approx(0.5)
    assert strategy[ACTION_INDEX[Action.BET_RAISE]] == pytest.approx(0.5)


def test_cfr_node_average_strategy_uniform_when_no_strategy_sum():
    node = CFRNode()
    legal_actions = [Action.FOLD, Action.CHECK_CALL]

    avg_strategy = node.average_strategy(legal_actions)

    assert avg_strategy[ACTION_INDEX[Action.FOLD]] == pytest.approx(0.5)
    assert avg_strategy[ACTION_INDEX[Action.CHECK_CALL]] == pytest.approx(0.5)
    assert avg_strategy[ACTION_INDEX[Action.BET_RAISE]] == 0.0


def test_cfr_node_average_strategy_uses_strategy_sum():
    node = CFRNode()
    node.strategy_sum[ACTION_INDEX[Action.FOLD]] = 2.0
    node.strategy_sum[ACTION_INDEX[Action.CHECK_CALL]] = 6.0

    legal_actions = [Action.FOLD, Action.CHECK_CALL]

    avg_strategy = node.average_strategy(legal_actions)

    assert avg_strategy[ACTION_INDEX[Action.FOLD]] == pytest.approx(0.25)
    assert avg_strategy[ACTION_INDEX[Action.CHECK_CALL]] == pytest.approx(0.75)


def test_cfr_node_rejects_empty_legal_actions():
    node = CFRNode()

    with pytest.raises(ValueError):
        node.get_strategy([])

    with pytest.raises(ValueError):
        node.average_strategy([])