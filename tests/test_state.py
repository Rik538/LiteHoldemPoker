# -*- coding: utf-8 -*-
"""
Created on Sun May 31 17:26:54 2026

@author: Richard
"""

import pytest

from lite_holdem_ai.game.actions import Action
from lite_holdem_ai.game.state import GameState


def test_game_state_imports():
    assert GameState is not None


def test_reset_hand_initialises_basic_state():
    state = GameState()
    state.reset_hand()
    state.setup_preflop()

    assert state.terminal is False
    assert state.folded_player is None
    assert len(state.payoffs) == 2
    assert sum(state.payoffs) == 0

    assert len(state.player_cards) == 2
    assert len(state.player_cards[0]) == 2
    assert len(state.player_cards[1]) == 2

    assert isinstance(state.public_cards, list)
    assert len(state.public_cards) == 0

    assert state.pot > 0
    assert len(state.player_contributions) == 2
    assert sum(state.player_contributions) == state.pot


def test_reset_hand_deals_unique_private_cards():
    state = GameState()
    state.reset_hand()
    state.setup_preflop()

    all_private_cards = state.player_cards[0] + state.player_cards[1]

    assert len(all_private_cards) == 4
    assert len(set(all_private_cards)) == 4


def test_initial_current_player_is_valid():
    state = GameState()
    state.reset_hand()

    assert state.current_player in [0, 1]


def test_initial_legal_actions_are_not_empty():
    state = GameState()
    state.reset_hand()

    legal_actions = state.legal_actions()

    assert len(legal_actions) > 0
    assert all(isinstance(action, Action) for action in legal_actions)


def test_observation_contains_core_fields():
    state = GameState()
    state.reset_hand()

    player = state.current_player
    obs = state.get_observation(player)

    assert "public_cards" in obs
    assert "pot" in obs
    assert "current_player" in obs
    assert "legal_actions" in obs
    assert "amount_to_call" in obs

    # Accept either naming style.
    assert "private_cards" in obs or "hole_cards" in obs or "private_card" in obs


def test_apply_check_call_records_action():
    state = GameState()
    state.reset_hand()

    if Action.CHECK_CALL not in state.legal_actions():
        pytest.skip("CHECK_CALL not legal in initial state")

    state.apply_action(Action.CHECK_CALL)

    assert len(state.action_history) >= 1
    assert state.terminal is False


def test_bet_raise_changes_pot_or_contributions():
    state = GameState()
    state.reset_hand()

    if Action.BET_RAISE not in state.legal_actions():
        pytest.skip("BET_RAISE not legal in initial state")

    old_pot = state.pot
    old_contributions = state.player_contributions.copy()

    state.apply_action(Action.BET_RAISE)

    assert state.pot > old_pot
    assert state.player_contributions != old_contributions
    assert len(state.action_history) >= 1


def test_fold_ends_hand_when_facing_bet():
    state = GameState()
    state.reset_hand()

    if Action.BET_RAISE not in state.legal_actions():
        pytest.skip("BET_RAISE not legal in initial state")

    state.apply_action(Action.BET_RAISE)

    if Action.FOLD not in state.legal_actions():
        pytest.skip("FOLD not legal after bet/raise")

    folded_player = state.current_player
    state.apply_action(Action.FOLD)

    assert state.terminal is True
    assert state.folded_player == folded_player
    assert sum(state.payoffs) == 0


def test_illegal_action_raises_value_error():
    state = GameState()
    state.reset_hand()

    # FOLD is often illegal if there is no bet to call.
    if Action.FOLD in state.legal_actions():
        pytest.skip("FOLD is legal in this state, cannot use as illegal action test")

    with pytest.raises(ValueError):
        state.apply_action(Action.FOLD)


def test_clone_is_independent():
    state = GameState()
    state.reset_hand()

    cloned = state.clone()

    cloned.pot += 10
    cloned.player_contributions[0] += 10

    assert cloned.pot != state.pot
    assert cloned.player_contributions != state.player_contributions


def test_payoffs_are_zero_sum_after_fold_terminal():
    state = GameState()
    state.reset_hand()

    if Action.BET_RAISE not in state.legal_actions():
        pytest.skip("BET_RAISE not legal in initial state")

    state.apply_action(Action.BET_RAISE)

    if Action.FOLD not in state.legal_actions():
        pytest.skip("FOLD not legal after bet/raise")

    state.apply_action(Action.FOLD)

    assert state.terminal is True
    assert sum(state.payoffs) == 0