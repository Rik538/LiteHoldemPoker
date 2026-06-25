# -*- coding: utf-8 -*-
"""
Created on Sun May 31 17:26:54 2026

@author: Richard
"""
# -*- coding: utf-8 -*-

from copy import deepcopy


from lite_holdem_ai.game.actions import Action
from lite_holdem_ai.game.state import GameState
from lite_holdem_ai.game.streets import Street


def test_game_state_default_values_are_sensible():
    state = GameState()

    assert state.player_cards == [[], []]
    assert state.public_cards == []

    assert state.pot == 0
    assert state.player_contributions == [0, 0]
    assert state.round_bets == [0, 0]

    assert state.current_player == 0
    assert state.terminal is False
    assert state.folded_player is None

    assert state.action_history == []
    assert state.actions_this_round == []
    assert state.raises_this_round == 0
    assert state.payoffs == [0, 0]


def test_amount_to_call_when_player_is_behind():
    state = GameState()
    state.round_bets = [1, 2]

    assert state.amount_to_call(0) == 1
    assert state.amount_to_call(1) == 0


def test_amount_to_call_when_bets_are_equal():
    state = GameState()
    state.round_bets = [2, 2]

    assert state.amount_to_call(0) == 0
    assert state.amount_to_call(1) == 0


def test_amount_to_call_never_goes_negative():
    state = GameState()
    state.round_bets = [4, 2]

    assert state.amount_to_call(0) == 0
    assert state.amount_to_call(1) == 2


def test_bet_size_preflop_and_flop_is_small_bet():
    state = GameState()

    state.street = Street.PREFLOP.value
    assert state.bet_size() == 2

    state.street = Street.FLOP.value
    assert state.bet_size() == 2


def test_bet_size_turn_and_river_is_big_bet():
    state = GameState()

    state.street = Street.TURN.value
    assert state.bet_size() == 4

    state.street = Street.RIVER.value
    assert state.bet_size() == 4


def test_round_not_over_with_no_actions():
    state = GameState()
    state.round_bets = [0, 0]
    state.actions_this_round = []

    assert state.is_round_over() is False


def test_round_not_over_with_only_one_action():
    state = GameState()
    state.round_bets = [0, 0]
    state.actions_this_round = [Action.CHECK_CALL]

    assert state.is_round_over() is False


def test_round_over_after_check_check():
    state = GameState()
    state.round_bets = [0, 0]
    state.actions_this_round = [Action.CHECK_CALL, Action.CHECK_CALL]

    assert state.is_round_over() is True


def test_round_not_over_after_bet_before_response():
    state = GameState()
    state.round_bets = [2, 0]
    state.actions_this_round = [Action.BET_RAISE]

    assert state.is_round_over() is False


def test_round_over_after_bet_call():
    state = GameState()
    state.round_bets = [2, 2]
    state.actions_this_round = [Action.BET_RAISE, Action.CHECK_CALL]

    assert state.is_round_over() is True


def test_round_not_over_when_bets_are_unequal_even_after_two_actions():
    state = GameState()
    state.round_bets = [4, 2]
    state.actions_this_round = [Action.BET_RAISE, Action.CHECK_CALL]

    assert state.is_round_over() is False


def test_clone_returns_independent_state_object():
    state = GameState()
    state.player_cards = [[1, 2], [3, 4]]
    state.public_cards = [5, 6, 7]
    state.player_contributions = [1, 2]
    state.round_bets = [1, 2]
    state.actions_this_round = [Action.CHECK_CALL]
    state.action_history = [(0, Street.PREFLOP.value, Action.CHECK_CALL, 1)]
    state.payoffs = [10, -10]

    cloned = state.clone()

    assert cloned is not state
    assert cloned.player_cards == state.player_cards
    assert cloned.public_cards == state.public_cards
    assert cloned.player_contributions == state.player_contributions
    assert cloned.round_bets == state.round_bets
    assert cloned.actions_this_round == state.actions_this_round
    assert cloned.action_history == state.action_history
    assert cloned.payoffs == state.payoffs

    cloned.player_cards[0].append(99)
    cloned.public_cards.append(88)
    cloned.player_contributions[0] += 10
    cloned.round_bets[0] += 10
    cloned.actions_this_round.append(Action.BET_RAISE)
    cloned.action_history.append((1, Street.FLOP.value, Action.BET_RAISE, 0))
    cloned.payoffs[0] += 100

    assert state.player_cards == [[1, 2], [3, 4]]
    assert state.public_cards == [5, 6, 7]
    assert state.player_contributions == [1, 2]
    assert state.round_bets == [1, 2]
    assert state.actions_this_round == [Action.CHECK_CALL]
    assert state.action_history == [(0, Street.PREFLOP.value, Action.CHECK_CALL, 1)]
    assert state.payoffs == [10, -10]


def test_clone_preserves_terminal_fields():
    state = GameState()
    state.terminal = True
    state.folded_player = 1
    state.payoffs = [3, -3]

    cloned = state.clone()

    assert cloned.terminal is True
    assert cloned.folded_player == 1
    assert cloned.payoffs == [3, -3]


def test_deepcopy_still_works_for_game_state():
    state = GameState()
    state.player_cards = [[1, 2], [3, 4]]

    copied = deepcopy(state)
    copied.player_cards[0].append(99)

    assert state.player_cards == [[1, 2], [3, 4]]
    assert copied.player_cards == [[1, 2, 99], [3, 4]]