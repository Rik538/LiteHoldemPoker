# -*- coding: utf-8 -*-

import pytest

from lite_holdem_ai.game.actions import Action
from lite_holdem_ai.game.environment import LiteHoldemEnv


ALL_ACTIONS = {
    Action.FOLD,
    Action.CHECK_CALL,
    Action.BET_RAISE,
}


def snapshot_state(state):
    """
    Snapshot only stable public state fields.

    This is used to prove env.next_state(parent, action) does not mutate parent.
    """
    return {
        "player_cards": tuple(tuple(cards) for cards in state.player_cards),
        "public_cards": tuple(state.public_cards),
        "pot": state.pot,
        "player_contributions": tuple(state.player_contributions),
        "current_player": state.current_player,
        "street": state.street,
        "round_bets": tuple(state.round_bets),
        "terminal": state.terminal,
        "folded_player": state.folded_player,
        "raises_this_round": state.raises_this_round,
        "actions_this_round": tuple(state.actions_this_round),
        "action_history": tuple(state.action_history),
        "payoffs": tuple(state.payoffs),
    }


def assert_zero_sum_payoffs(state):
    assert len(state.payoffs) == 2
    assert state.payoffs[0] + state.payoffs[1] == pytest.approx(0)


def assert_pot_matches_contributions(state):
    assert state.pot == sum(state.player_contributions)


def choose_safe_action(legal_actions):
    """
    Prefer CHECK_CALL so the hand naturally advances through streets
    without folding.
    """
    if Action.CHECK_CALL in legal_actions:
        return Action.CHECK_CALL

    return legal_actions[0]


def play_until_terminal(env, state, max_steps=100):
    for _ in range(max_steps):
        if state.terminal:
            return state

        legal_actions = env.legal_actions(state)

        assert legal_actions
        assert set(legal_actions).issubset(ALL_ACTIONS)

        action = choose_safe_action(legal_actions)
        state = env.next_state(state, action)

        assert_pot_matches_contributions(state)

    raise AssertionError("Hand did not terminate within max_steps")


def test_reset_starts_non_terminal_state_with_legal_actions():
    env = LiteHoldemEnv()
    env.reset()

    state = env.state

    assert state.terminal is False
    assert env.legal_actions(state)
    assert set(env.legal_actions(state)).issubset(ALL_ACTIONS)
    assert_pot_matches_contributions(state)


def test_terminal_state_has_no_legal_actions_after_fold():
    env = LiteHoldemEnv()
    env.reset()

    state = env.state

    if Action.FOLD not in env.legal_actions(state):
        if Action.BET_RAISE not in env.legal_actions(state):
            pytest.skip("Cannot construct fold state from initial state")

        state = env.next_state(state, Action.BET_RAISE)

    folded_player = state.current_player
    terminal = env.next_state(state, Action.FOLD)

    assert terminal.terminal is True
    assert terminal.folded_player == folded_player
    assert env.legal_actions(terminal) == []
    assert_zero_sum_payoffs(terminal)
    assert_pot_matches_contributions(terminal)


def test_check_call_line_reaches_showdown_terminal_state():
    env = LiteHoldemEnv()
    env.reset()

    terminal = play_until_terminal(env, env.state)

    assert terminal.terminal is True
    assert terminal.folded_player is None
    assert len(terminal.public_cards) == 5
    assert_zero_sum_payoffs(terminal)
    assert env.legal_actions(terminal) == []


def test_next_state_does_not_mutate_parent_state():
    env = LiteHoldemEnv()
    env.reset()

    parent = env.state
    before = snapshot_state(parent)

    legal_actions = env.legal_actions(parent)
    action = choose_safe_action(legal_actions)

    child = env.next_state(parent, action)

    assert child is not parent
    assert snapshot_state(parent) == before


def test_next_state_does_not_mutate_environment_state_when_given_explicit_state():
    env = LiteHoldemEnv()
    env.reset()

    env_state_before = snapshot_state(env.state)

    branch_state = env.state.clone()
    legal_actions = env.legal_actions(branch_state)
    action = choose_safe_action(legal_actions)

    child = env.next_state(branch_state, action)

    assert child is not branch_state
    assert snapshot_state(env.state) == env_state_before


def test_step_updates_environment_state_but_keeps_invariants():
    env = LiteHoldemEnv()
    env.reset()

    before = snapshot_state(env.state)

    legal_actions = env.legal_actions()
    action = choose_safe_action(legal_actions)

    env.step(action)

    after = snapshot_state(env.state)

    assert after != before
    assert_pot_matches_contributions(env.state)

    if env.state.terminal:
        assert_zero_sum_payoffs(env.state)
        assert env.legal_actions(env.state) == []
    else:
        assert env.legal_actions(env.state)


def test_non_terminal_states_always_have_at_least_one_legal_action():
    env = LiteHoldemEnv()
    env.reset()

    state = env.state

    for _ in range(100):
        if state.terminal:
            break

        legal_actions = env.legal_actions(state)

        assert legal_actions
        assert set(legal_actions).issubset(ALL_ACTIONS)

        state = env.next_state(state, choose_safe_action(legal_actions))

    assert state.terminal is True


def test_folded_terminal_payoffs_award_pot_to_non_folder():
    env = LiteHoldemEnv()
    env.reset()

    state = env.state

    if Action.FOLD not in env.legal_actions(state):
        if Action.BET_RAISE not in env.legal_actions(state):
            pytest.skip("Cannot construct fold state from initial state")

        state = env.next_state(state, Action.BET_RAISE)

    folded_player = state.current_player
    winner = 1 - folded_player

    terminal = env.next_state(state, Action.FOLD)

    assert terminal.terminal is True
    assert terminal.folded_player == folded_player
    assert terminal.payoffs[winner] > 0
    assert terminal.payoffs[folded_player] < 0
    assert_zero_sum_payoffs(terminal)


def test_action_history_grows_after_non_terminal_action():
    env = LiteHoldemEnv()
    env.reset()

    state = env.state
    before_len = len(state.action_history)

    action = choose_safe_action(env.legal_actions(state))
    child = env.next_state(state, action)

    assert len(child.action_history) == before_len + 1


def test_public_cards_never_exceed_five_during_hand():
    env = LiteHoldemEnv()
    env.reset()

    state = env.state

    for _ in range(100):
        assert len(state.public_cards) <= 5

        if state.terminal:
            break

        action = choose_safe_action(env.legal_actions(state))
        state = env.next_state(state, action)

    assert state.terminal is True
    assert len(state.public_cards) <= 5