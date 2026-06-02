# -*- coding: utf-8 -*-
"""
Created on Sun May 31 13:36:05 2026

@author: Richard
"""

from .state import GameState


class LiteHoldemEnv:
    def __init__(self, state: GameState | None = None):
        self.state = state if state is not None else GameState()

    @property
    def current_player(self) -> int:
        return self.state.current_player

    def reset(self):
        self.state.reset_hand()
        self.state.setup_preflop()
        return self.observe(self.current_player)

    def legal_actions(self):
        return self.state.legal_actions()

    def step(self, action):
        self.state.apply_action(action)

        done = self.state.terminal
        reward = self.state.payoffs.copy() if done else [0, 0]

        info = {
           "street": self.state.street,
        }

        if done:
            observation = None
        else:
            observation = self.observe(self.current_player)

        return observation, reward, done,info

    def deal_public_card(self, card=None):
        self.state.deal_public_card(card=card)
        return self.observe(self.current_player)

    def observe(self, player: int):
        return self.state.get_observation(player)

    def is_terminal(self) -> bool:
        return self.state.terminal

    def payoffs(self):
        return self.state.payoffs.copy()