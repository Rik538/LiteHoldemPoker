# -*- coding: utf-8 -*-
"""
Created on Mon Jun  1 21:13:10 2026

@author: Richard
"""

from lite_holdem_ai.agents.heuristic_agent import HeuristicAgent
from lite_holdem_ai.game.actions import Action

def test_heuristic_agent_selects_legal_action_preflop():
    agent = HeuristicAgent()

    observation = {
        "private_cards": [16, 17],
        "public_cards": [],
        "pot": 3,
        "amount_to_call": 0,
        "street": 0,
    }

    legal_actions = [Action.CHECK_CALL, Action.BET_RAISE]

    action = agent.select_action(observation, legal_actions)

    assert action in legal_actions
    
    
def test_heuristic_agent_bets_strong_hand_when_free():
    agent = HeuristicAgent()

    observation = {
        "private_cards": [16, 17],  # high pocket pair if rank = card // 4
        "public_cards": [],
        "pot": 3,
        "amount_to_call": 0,
        "street": 0,
    }

    legal_actions = [Action.CHECK_CALL, Action.BET_RAISE]

    action = agent.select_action(observation, legal_actions)

    assert action == Action.BET_RAISE
    
    
    
def test_heuristic_agent_folds_weak_hand_facing_bet():
    agent = HeuristicAgent()

    observation = {
        "private_cards": [0, 5],
        "public_cards": [],
        "pot": 3,
        "amount_to_call": 4,
        "street": 0,
    }

    legal_actions = [Action.FOLD, Action.CHECK_CALL, Action.BET_RAISE]

    action = agent.select_action(observation, legal_actions)

    assert action in legal_actions