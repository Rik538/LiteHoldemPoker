# -*- coding: utf-8 -*-

import pytest

from lite_holdem_ai.game.actions import Action
from lite_holdem_ai.game.environment import LiteHoldemEnv
from lite_holdem_ai.game.streets import Street


def make_env():
    return LiteHoldemEnv()


def test_reset_initialises_preflop_hand():
    env = make_env()
    observation = env.reset()
    state = env.state

    assert state.street == Street.PREFLOP.value
    assert state.terminal is False
    assert state.folded_player is None

    assert len(state.player_cards[0]) == 2
    assert len(state.player_cards[1]) == 2
    assert state.public_cards == []

    assert state.pot == state.small_blind + state.big_blind
    assert sum(state.player_contributions) == state.pot

    assert state.round_bets[state.button_player] == state.small_blind
    assert state.round_bets[1 - state.button_player] == state.big_blind

    assert state.current_player == state.button_player
    assert observation["current_player"] == state.current_player
    assert observation["street"] == Street.PREFLOP.value


def test_current_player_property_reads_environment_state():
    env = make_env()
    env.reset()

    env.state.current_player = 1
    assert env.current_player == 1

    env.state.current_player = 0
    assert env.current_player == 0


def test_legal_actions_returns_empty_for_terminal_state():
    env = make_env()
    env.reset()

    state = env.state.clone()
    state.terminal = True

    assert env.legal_actions(state) == []


def test_legal_actions_when_not_facing_bet_allows_check_or_bet():
    env = make_env()
    env.reset()

    state = env.state.clone()
    state.round_bets = [0, 0]
    state.current_player = 0
    state.raises_this_round = 0

    assert env.legal_actions(state) == [Action.CHECK_CALL, Action.BET_RAISE]


def test_legal_actions_when_facing_bet_allows_fold_call_raise():
    env = make_env()
    env.reset()

    state = env.state.clone()
    state.current_player = 0
    state.round_bets = [0, 2]
    state.raises_this_round = 0

    assert env.legal_actions(state) == [
        Action.FOLD,
        Action.CHECK_CALL,
        Action.BET_RAISE,
    ]


def test_legal_actions_when_facing_bet_and_raise_cap_reached():
    env = make_env()
    env.reset()

    state = env.state.clone()
    state.current_player = 0
    state.round_bets = [0, 2]
    state.raises_this_round = state.MAX_RAISES_PER_ROUND

    assert env.legal_actions(state) == [Action.FOLD, Action.CHECK_CALL]


def test_fold_is_illegal_when_not_facing_bet():
    env = make_env()
    env.reset()

    state = env.state.clone()
    state.current_player = 0
    state.round_bets = [0, 0]
    state.raises_this_round = 0

    assert Action.FOLD not in env.legal_actions(state)

    with pytest.raises(ValueError, match="Illegal action"):
        env.apply_action(Action.FOLD, state)


def test_apply_action_fold_sets_terminal_and_zero_sum_payoffs():
    env = make_env()
    env.reset()

    state = env.state.clone()
    current_player = state.current_player
    opponent = 1 - current_player

    assert Action.FOLD in env.legal_actions(state)

    env.apply_action(Action.FOLD, state)

    assert state.terminal is True
    assert state.folded_player == current_player

    assert state.payoffs[current_player] == -state.player_contributions[current_player]
    assert state.payoffs[opponent] == state.pot - state.player_contributions[opponent]
    assert sum(state.payoffs) == 0


def test_apply_action_call_matches_bets_and_updates_pot():
    env = make_env()
    env.reset()

    state = env.state.clone()
    player = state.current_player
    to_call = env.amount_to_call(player,env.state)
    pot_before = state.pot
    contribution_before = state.player_contributions[player]

    assert to_call > 0

    env.apply_action(Action.CHECK_CALL, state)

    assert state.player_contributions[player] == contribution_before + to_call
    assert state.pot == pot_before + to_call
    assert state.round_bets[0] == state.round_bets[1]


def test_apply_action_bet_updates_round_bets_pot_and_raises():
    env = make_env()
    env.reset()

    state = env.state.clone()
    state.street = Street.FLOP.value
    state.current_player = 0
    state.round_bets = [0, 0]
    state.player_contributions = [0, 0]
    state.pot = 0
    state.actions_this_round = []
    state.raises_this_round = 0

    env.apply_action(Action.BET_RAISE, state)

    assert state.round_bets[0] == 2
    assert state.player_contributions[0] == 2
    assert state.pot == 2
    assert state.raises_this_round == 1
    assert state.current_player == 1


def test_apply_action_raise_calls_amount_to_call_plus_bet_size():
    env = make_env()
    env.reset()

    state = env.state.clone()
    state.street = Street.FLOP.value
    state.current_player = 0
    state.round_bets = [0, 2]
    state.player_contributions = [0, 2]
    state.pot = 2
    state.actions_this_round = [Action.BET_RAISE]
    state.raises_this_round = 1

    env.apply_action(Action.BET_RAISE, state)

    assert state.round_bets[0] == 4
    assert state.player_contributions[0] == 4
    assert state.pot == 6
    assert state.raises_this_round == 2
    assert state.current_player == 1


def test_check_check_advances_from_flop_to_turn():
    env = make_env()
    env.reset()

    state = env.state.clone()
    state.street = Street.FLOP.value
    state.public_cards = state.deck.draw_multiple_cards(3)
    state.current_player = 0
    state.button_player = 1
    state.round_bets = [0, 0]
    state.actions_this_round = []
    state.raises_this_round = 0

    env.apply_action(Action.CHECK_CALL, state)
    assert state.street == Street.FLOP.value
    assert state.current_player == 1

    env.apply_action(Action.CHECK_CALL, state)

    assert state.street == Street.TURN.value
    assert len(state.public_cards) == 4
    assert state.round_bets == [0, 0]
    assert state.actions_this_round == []
    assert state.raises_this_round == 0
    assert state.current_player == 1 - state.button_player


def test_preflop_call_then_check_advances_to_flop():
    env = make_env()
    env.reset()

    state = env.state.clone()

    env.apply_action(Action.CHECK_CALL, state)
    assert state.street == Street.PREFLOP.value

    env.apply_action(Action.CHECK_CALL, state)

    assert state.street == Street.FLOP.value
    assert len(state.public_cards) == 3
    assert state.round_bets == [0, 0]
    assert state.actions_this_round == []
    assert state.raises_this_round == 0


def test_checking_all_streets_reaches_showdown():
    env = make_env()
    env.reset()

    state = env.state.clone()
    guard = 0

    while not state.terminal:
        legal_actions = env.legal_actions(state)
        assert Action.CHECK_CALL in legal_actions

        env.apply_action(Action.CHECK_CALL, state)

        guard += 1
        assert guard < 20

    assert state.terminal is True
    assert len(state.public_cards) == 5
    assert sum(state.payoffs) == 0


def test_step_mutates_environment_state():
    env = make_env()
    env.reset()

    assert env.state.terminal is False

    observation, reward, done, info = env.step(Action.FOLD)

    assert env.state.terminal is True
    assert done is True
    assert observation is None
    assert reward == env.state.payoffs
    assert info["street"] == Street.PREFLOP.value


def test_apply_action_with_explicit_state_does_not_mutate_env_state():
    env = make_env()
    env.reset()

    branch_state = env.state.clone()

    env.apply_action(Action.FOLD, branch_state)

    assert branch_state.terminal is True
    assert env.state.terminal is False
    assert env.state.folded_player is None


def test_next_state_returns_child_without_mutating_parent_or_env_state():
    env = make_env()
    env.reset()

    parent_state = env.state.clone()
    parent_snapshot = parent_state.clone()

    child_state = env.next_state(parent_state, Action.FOLD)

    assert child_state is not parent_state
    assert child_state.terminal is True

    assert parent_state.terminal == parent_snapshot.terminal
    assert parent_state.folded_player == parent_snapshot.folded_player
    assert parent_state.payoffs == parent_snapshot.payoffs
    assert parent_state.action_history == parent_snapshot.action_history

    assert env.state.terminal is False
    assert env.state.folded_player is None


def test_next_state_child_lists_are_independent_from_parent():
    env = make_env()
    env.reset()

    parent_state = env.state.clone()
    child_state = env.next_state(parent_state, Action.FOLD)

    child_state.action_history.append(("debug",))
    child_state.actions_this_round.append(Action.CHECK_CALL)
    child_state.public_cards.append(999)
    child_state.player_cards[0].append(888)

    assert ("debug",) not in parent_state.action_history
    assert parent_state.actions_this_round != child_state.actions_this_round
    assert 999 not in parent_state.public_cards
    assert 888 not in parent_state.player_cards[0]


def test_observe_uses_supplied_state_not_env_state():
    env = make_env()
    env.reset()

    branch_state = env.state.clone()
    branch_state.pot = 999
    branch_state.current_player = 1
    branch_state.round_bets = [0, 0]
    branch_state.public_cards = [1, 2, 3]

    observation = env.observe(1, branch_state)

    assert observation["pot"] == 999
    assert observation["current_player"] == 1
    assert observation["public_cards"] == [1, 2, 3]
    assert observation["legal_actions"] == [Action.CHECK_CALL, Action.BET_RAISE]

    assert env.state.pot != 999


def test_observation_lists_are_copies():
    env = make_env()
    env.reset()

    observation = env.observe(env.state.current_player)

    observation["public_cards"].append(999)
    observation["player_contributions"][0] += 100
    observation["round_bets"][0] += 100
    observation["actions_this_round"].append(Action.FOLD)
    observation["action_history"].append(("debug",))

    assert 999 not in env.state.public_cards
    assert env.state.player_contributions != observation["player_contributions"]
    assert env.state.round_bets != observation["round_bets"]
    assert env.state.actions_this_round != observation["actions_this_round"]
    assert env.state.action_history != observation["action_history"]


def test_deal_flop_uses_supplied_state_not_env_state():
    env = make_env()
    env.reset()

    branch_state = env.state.clone()
    assert branch_state.public_cards == []
    assert env.state.public_cards == []

    env.deal_flop(branch_state)

    assert len(branch_state.public_cards) == 3
    assert env.state.public_cards == []


def test_deal_turn_uses_supplied_state_not_env_state():
    env = make_env()
    env.reset()

    branch_state = env.state.clone()
    env.deal_flop(branch_state)

    assert len(branch_state.public_cards) == 3
    assert env.state.public_cards == []

    env.deal_turn(branch_state)

    assert len(branch_state.public_cards) == 4
    assert env.state.public_cards == []


def test_deal_river_uses_supplied_state_not_env_state():
    env = make_env()
    env.reset()

    branch_state = env.state.clone()
    env.deal_flop(branch_state)
    env.deal_turn(branch_state)

    assert len(branch_state.public_cards) == 4
    assert env.state.public_cards == []

    env.deal_river(branch_state)

    assert len(branch_state.public_cards) == 5
    assert env.state.public_cards == []


def test_resolve_showdown_uses_supplied_state_not_env_state():
    env = make_env()
    env.reset()

    branch_state = env.state.clone()

    while len(branch_state.public_cards) < 5:
        if len(branch_state.public_cards) == 0:
            env.deal_flop(branch_state)
        elif len(branch_state.public_cards) == 3:
            env.deal_turn(branch_state)
        elif len(branch_state.public_cards) == 4:
            env.deal_river(branch_state)

    env.resolve_showdown(branch_state)

    assert branch_state.terminal is True
    assert sum(branch_state.payoffs) == 0

    assert env.state.terminal is False
    assert env.state.payoffs == [0, 0]


def test_payoffs_returns_copy():
    env = make_env()
    env.reset()
    env.step(Action.FOLD)

    payoffs = env.payoffs()
    payoffs[0] += 999

    assert payoffs != env.state.payoffs


def test_cannot_apply_action_to_terminal_state():
    env = make_env()
    env.reset()

    state = env.state.clone()
    state.terminal = True

    with pytest.raises(ValueError, match="terminal state"):
        env.apply_action(Action.CHECK_CALL, state)

def test_amount_to_call_when_player_is_behind():
    env = make_env()
    env.reset()
    env.state.round_bets = [1, 2]
    
    assert env.amount_to_call(0,env.state) == 1
    assert env.amount_to_call(1,env.state) == 0        
    
def test_amount_to_call_when_bets_are_equal():
    env = make_env()
    env.reset()
    env.state.round_bets = [2, 2]

    assert env.amount_to_call(0,env.state) == 0
    assert env.amount_to_call(1,env.state) == 0   
        
def test_amount_to_call_never_goes_negative():
    env = make_env()
    env.reset()
    env.state.round_bets = [4, 2]

    assert env.amount_to_call(0,env.state) == 0
    assert env.amount_to_call(1,env.state) == 2


def test_bet_size_preflop_and_flop_is_small_bet():
    env = make_env()
    env.reset()
    state = env.state

    state.street = Street.PREFLOP.value
    assert env.bet_size(state) == 2

    state.street = Street.FLOP.value
    assert env.bet_size(state) == 2
    
def test_bet_size_turn_and_river_is_big_bet():
    env = make_env()
    env.reset()
    state = env.state

    state.street = Street.TURN.value
    assert env.bet_size(state) == 4

    state.street = Street.RIVER.value
    assert env.bet_size(state) == 4
    
def test_round_not_over_with_no_actions():
    env = make_env()
    env.reset()
    state = env.state
    state.round_bets = [0, 0]
    state.actions_this_round = []

    assert env.is_round_over(state) is False


def test_round_not_over_with_only_one_action():
    env = make_env()
    env.reset()
    state = env.state
    state.round_bets = [0, 0]
    state.actions_this_round = [Action.CHECK_CALL]

    assert env.is_round_over(state) is False
    


def test_round_over_after_check_check():
    env = make_env()
    env.reset()
    state = env.state
    state.round_bets = [0, 0]
    state.actions_this_round = [Action.CHECK_CALL, Action.CHECK_CALL]

    assert env.is_round_over(state) is True


def test_round_not_over_after_bet_before_response():
    env = make_env()
    env.reset()
    state = env.state
    state.round_bets = [2, 0]
    state.actions_this_round = [Action.BET_RAISE]

    assert env.is_round_over(state) is False

def test_round_over_after_bet_call():
    env = make_env()
    env.reset()
    state = env.state
    state.round_bets = [2, 2]
    state.actions_this_round = [Action.BET_RAISE, Action.CHECK_CALL]

    assert env.is_round_over(state) is True


def test_round_not_over_when_bets_are_unequal_even_after_two_actions():
    env = make_env()
    env.reset()
    state = env.state
    state.round_bets = [4, 2]
    state.actions_this_round = [Action.BET_RAISE, Action.CHECK_CALL]

    assert env.is_round_over(state) is False
        
        