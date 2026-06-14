# -*- coding: utf-8 -*-
"""
Created on Sat Jun  6 23:32:16 2026

@author: Richard
"""

from dataclasses import dataclass, field

from lite_holdem_ai.game.actions import Action


ACTION_INDEX = {
    Action.FOLD: 0,
    Action.CHECK_CALL: 1,
    Action.BET_RAISE: 2,
}

INDEX_ACTION = {
    0: Action.FOLD,
    1: Action.CHECK_CALL,
    2: Action.BET_RAISE,
}

NUM_ACTIONS = 3


@dataclass
class CFRNode:
    regret_sum: list[float] = field(default_factory=lambda: [0.0] * NUM_ACTIONS)
    strategy_sum: list[float] = field(default_factory=lambda: [0.0] * NUM_ACTIONS)

    def get_strategy(
        self,
        legal_actions,
        reach_probability: float = 1.0,
        accumulate_strategy: bool = True,
    ) -> list[float]:
        if not legal_actions:
            raise ValueError("CFRNode received no legal actions")

        strategy = [0.0] * NUM_ACTIONS
        positive_regret_sum = 0.0

        # Always calculate current strategy from regrets
        for action in legal_actions:
            idx = ACTION_INDEX[action]
            positive_regret = max(self.regret_sum[idx], 0.0)
            strategy[idx] = positive_regret
            positive_regret_sum += positive_regret

        if positive_regret_sum > 0:
            for action in legal_actions:
                idx = ACTION_INDEX[action]
                strategy[idx] /= positive_regret_sum
        else:
            probability = 1.0 / len(legal_actions)

            for action in legal_actions:
                idx = ACTION_INDEX[action]
                strategy[idx] = probability

        # Only this part should be delayed
        if accumulate_strategy:
            for action in legal_actions:
                idx = ACTION_INDEX[action]
                self.strategy_sum[idx] += reach_probability * strategy[idx]

        return strategy

    def average_strategy(self, legal_actions) -> list[float]:
        if not legal_actions:
            raise ValueError("CFRNode received no legal actions")

        avg_strategy = [0.0] * NUM_ACTIONS
        normalising_sum = 0.0

        for action in legal_actions:
            idx = ACTION_INDEX[action]
            normalising_sum += self.strategy_sum[idx]

        if normalising_sum > 0:
            for action in legal_actions:
                idx = ACTION_INDEX[action]
                avg_strategy[idx] = self.strategy_sum[idx] / normalising_sum
        else:
            probability = 1.0 / len(legal_actions)

            for action in legal_actions:
                idx = ACTION_INDEX[action]
                avg_strategy[idx] = probability

        return avg_strategy