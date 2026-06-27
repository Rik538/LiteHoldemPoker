# -*- coding: utf-8 -*-

import random

import pytest

from lite_holdem_ai.cfr.sampling import sample_strategy_action
from lite_holdem_ai.game.actions import Action


def test_sample_strategy_action_rejects_empty_legal_actions():
    rng = random.Random(123)

    with pytest.raises(ValueError, match="empty legal_actions"):
        sample_strategy_action(rng, [], [0.0, 0.5, 0.5])


def test_sample_strategy_action_only_returns_legal_actions():
    rng = random.Random(123)

    legal_actions = [Action.CHECK_CALL, Action.BET_RAISE]
    strategy = [1.0, 0.0, 0.0]

    for _ in range(100):
        action = sample_strategy_action(rng, legal_actions, strategy)
        assert action in legal_actions
        
def test_sample_strategy_action_is_seeded():
    legal_actions = [Action.CHECK_CALL, Action.BET_RAISE]
    strategy = [0.0, 0.4, 0.6]

    rng_a = random.Random(123)
    rng_b = random.Random(123)

    actions_a = [
        sample_strategy_action(rng_a, legal_actions, strategy)
        for _ in range(20)
    ]

    actions_b = [
        sample_strategy_action(rng_b, legal_actions, strategy)
        for _ in range(20)
    ]

    assert actions_a == actions_b