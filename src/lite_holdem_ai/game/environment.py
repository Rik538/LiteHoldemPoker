# -*- coding: utf-8 -*-
"""
Created on Sun May 31 13:36:05 2026

@author: Richard
"""

from .state import GameState
from .actions import Action
from .streets import Street
from .showdown import Showdown


class LiteHoldemEnv:
    def __init__(self, state: GameState | None = None):
        self.state = state if state is not None else GameState()
        self.showdown = Showdown()

    @property
    def current_player(self) -> int:
        return self.state.current_player

    def reset(self):
        self.state.deck.reset_deck()
        self.state.deck.shuffle_deck()

        self.state.player_cards = [[], []]
        self.state.public_cards = []

        self.state.pot = 0
        self.state.player_contributions = [0, 0]

        self.state.current_player = 0
        self.state.round_bets = [0, 0]

        self.state.terminal = False
        self.state.folded_player = None

        self.state.action_history = []
        self.state.actions_this_round = []
        self.state.raises_this_round = 0
        self.state.payoffs = [0, 0]

        self.state.street = Street.PREFLOP.value

        self.setup_preflop(self.state)

        return self.observe(self.state.current_player, self.state)

    def setup_preflop(self, state: GameState | None = None):
        state = self.state if state is None else state

        button_player = state.button_player
        big_blind = 1 - button_player

        state.round_bets[button_player] += state.small_blind
        state.round_bets[big_blind] += state.big_blind

        state.player_contributions[button_player] += state.small_blind
        state.player_contributions[big_blind] += state.big_blind

        state.pot += state.big_blind + state.small_blind

        state.player_cards[0] = state.deck.draw_multiple_cards(2)
        state.player_cards[1] = state.deck.draw_multiple_cards(2)

        state.current_player = button_player

    def legal_actions(self, state: GameState | None = None) -> list[Action]:
        """
        If no state is provided, use self.state.
        If state is provided, calculate legal actions for that state.
        """
        state = self.state if state is None else state

        if state.terminal:
            return []

        to_call = self.amount_to_call(state.current_player,state)
        can_raise = state.raises_this_round < state.MAX_RAISES_PER_ROUND

        if to_call == 0:
            if can_raise:
                return [Action.CHECK_CALL, Action.BET_RAISE]
            return [Action.CHECK_CALL]

        if can_raise:
            return [Action.FOLD, Action.CHECK_CALL, Action.BET_RAISE]

        return [Action.FOLD, Action.CHECK_CALL]

    def deal_flop(self, state: GameState | None = None):
        state = self.state if state is None else state

        if state.public_cards:
            raise Exception(
                f"Public cards present when dealing flop: {state.public_cards}. "
                "Expected no public cards."
            )

        state.public_cards += state.deck.draw_multiple_cards(3)

    def deal_turn(self, state: GameState | None = None):
        state = self.state if state is None else state

        if len(state.public_cards) != 3:
            raise Exception(
                f"Incorrect number of cards for turn: {state.public_cards}. "
                "Expected 3 cards."
            )

        state.public_cards += [state.deck.draw_card()]

    def deal_river(self, state: GameState | None = None):
        state = self.state if state is None else state

        if len(state.public_cards) != 4:
            raise Exception(
                f"Incorrect number of cards for river: {state.public_cards}. "
                "Expected 4 cards."
            )

        state.public_cards += [state.deck.draw_card()]

    def step(self, action: Action):
        self.apply_action(action, self.state)

        done = self.state.terminal
        reward = self.state.payoffs.copy() if done else [0, 0]

        info = {
            "street": self.state.street,
        }

        if done:
            observation = None
        else:
            observation = self.observe(self.state.current_player, self.state)

        return observation, reward, done, info

    def apply_action(self, action: Action, state: GameState | None = None):
        state = self.state if state is None else state

        if state.terminal:
            raise ValueError("Cannot apply action to terminal state")

        if action not in self.legal_actions(state):
            raise ValueError(f"Illegal action: {action}")

        current_player = state.current_player
        to_call = self.amount_to_call(current_player,state)

        state.actions_this_round.append(action)
        state.action_history.append((current_player, state.street, action, to_call))

        if action == Action.CHECK_CALL:
            if to_call == 0:
                # check
                pass
            else:
                # call
                self.apply_call(state)

        elif action == Action.BET_RAISE:
            if to_call == 0:
                # bet
                self.apply_bet(state)
            else:
                # raise
                self.apply_raise(state)

        elif action == Action.FOLD:
            self.apply_fold(state)
            return

        if self.is_round_over(state):
            self.advance_round(state)
        else:
            state.current_player = 1 - state.current_player

    def advance_round(self, state: GameState | None = None):
        state = self.state if state is None else state

        
        street = state.street

        state.round_bets = [0, 0]
        state.actions_this_round = []
        state.raises_this_round = 0

        if street == Street.PREFLOP.value:
            self.deal_flop(state)

        elif street == Street.FLOP.value:
            self.deal_turn(state)

        elif street == Street.TURN.value:
            self.deal_river(state)

        else:
            self.resolve_showdown(state)
            return
        
        state.street += 1
        state.current_player = 1 - state.button_player

    def apply_bet(self, state: GameState | None = None):
        state = self.state if state is None else state

        bet_amount = self.bet_size(state)
        current_player = state.current_player

        state.round_bets[current_player] += bet_amount
        state.player_contributions[current_player] += bet_amount

        state.pot += bet_amount
        state.raises_this_round += 1

    def apply_raise(self, state: GameState | None = None):
        state = self.state if state is None else state

        current_player = state.current_player
        bet_amount = self.bet_size(state) + self.amount_to_call(current_player,state)

        state.round_bets[current_player] += bet_amount
        state.player_contributions[current_player] += bet_amount

        state.pot += bet_amount
        state.raises_this_round += 1

    def apply_call(self, state: GameState | None = None):
        state = self.state if state is None else state

        current_player = state.current_player
        bet_amount = self.amount_to_call(current_player,state)

        state.round_bets[current_player] += bet_amount
        state.player_contributions[current_player] += bet_amount

        state.pot += bet_amount

    def apply_fold(self, state: GameState | None = None):
        state = self.state if state is None else state

        loser = state.current_player
        winner = 1 - loser

        state.folded_player = loser

        state.payoffs[winner] = state.pot - state.player_contributions[winner]
        state.payoffs[loser] = -state.player_contributions[loser]

        state.terminal = True

    def resolve_showdown(self, state: GameState | None = None):
        state = self.state if state is None else state

        state.terminal = True

        p0_payoff, p1_payoff = self.showdown.resolve_showdown(
            state.player_cards[0],
            state.player_cards[1],
            state.public_cards,
            state.pot,
        )

        self.award_pot(p0_payoff, p1_payoff, state)

    def award_pot(self, p0, p1, state: GameState | None = None):
        state = self.state if state is None else state

        pot = state.pot
        state.payoffs[0] = (-pot / 2) + p0
        state.payoffs[1] = (-pot / 2) + p1

    def is_terminal(self) -> bool:
        return self.state.terminal

    def payoffs(self):
        return self.state.payoffs.copy()

    def observe(self, player: int, state: GameState | None = None):
        state = self.state if state is None else state

        return {
            "private_cards": state.player_cards[player].copy(),
            "public_cards": state.public_cards.copy(),
            "street": state.street,
            "pot": state.pot,
            "player_contributions": state.player_contributions.copy(),
            "round_bets": state.round_bets.copy(),
            "player": player,
            "current_player": state.current_player,
            "button_player": state.button_player,
            "legal_actions": self.legal_actions(state),
            "amount_to_call": self.amount_to_call(player,state),
            "raises_this_round": state.raises_this_round,
            "actions_this_round": state.actions_this_round.copy(),
            "action_history": state.action_history.copy(),
        }

    def next_state(self, state: GameState, action: Action) -> GameState:
        """
        Pure-ish transition for CFR/search.
        Returns a copied/mutated child state.
        Does not mutate self.state.
        """
        child = state.clone()
        self.apply_action(action, child)
        return child
    
    def amount_to_call(self,player,state: GameState | None = None):
        state = self.state if state is None else state
        return max(state.round_bets) - state.round_bets[player]
    
    
    def bet_size(self,state: GameState | None = None):
        state = self.state if state is None else state
        if state.street in [Street.PREFLOP.value,Street.FLOP.value]:
            return 2 
        return 4
        
    def is_round_over(self,state: GameState | None = None):
        state = self.state if state is None else state
        if state.terminal:
            return True
        return (
            len(state.actions_this_round) >= 2
            and state.round_bets[0] == state.round_bets[1]
        )