# -*- coding: utf-8 -*-
"""
Shared CFR/MCCFR strategy sampling helpers.
"""

from collections.abc import Sequence
from random import Random

from lite_holdem_ai.cfr.node import ACTION_INDEX
from lite_holdem_ai.game.actions import Action


def sample_strategy_action(
    rng: Random,
    legal_actions: Sequence[Action],
    strategy: Sequence[float],
) -> Action:
    """
    Sample one legal action from a full CFR strategy array.

    The strategy array is indexed by ACTION_INDEX and may contain
    probabilities for actions that are not legal in the current state.
    Only legal_actions are considered.
    """
    if not legal_actions:
        raise ValueError("Cannot sample action from empty legal_actions")

    roll = rng.random()
    cumulative = 0.0

    for action in legal_actions:
        idx = ACTION_INDEX[action]
        cumulative += strategy[idx]

        if roll <= cumulative:
            return action

    # Floating-point fallback.
    return legal_actions[-1]