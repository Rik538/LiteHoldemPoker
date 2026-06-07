# -*- coding: utf-8 -*-
"""
Created on Sun May 17 17:45:09 2026

@author: Richard
"""



from dataclasses import dataclass, field
from .deck import Deck
from .actions import Action 
from .streets import Street
from .showdown import Showdown
import copy




    

@dataclass
class GameState:
    deck: Deck = field(default_factory=Deck)
    player_cards: list[list[int]] = field(default_factory=lambda: [[], []])
    public_cards: list[int] = field(default_factory=list)

    pot: int = 0
    player_contributions: list[int] = field(default_factory=lambda: [0, 0])

    current_player: int = 0
    street: int = 0

    round_bets: list[int] = field(default_factory=lambda: [0, 0])

    terminal: bool = False
    folded_player: int | None = None

    action_history: list = field(default_factory=list)
    raises_this_round: int = 0

    actions_this_round: list = field(default_factory=list)
    payoffs: list[int] = field(default_factory=lambda: [0, 0])
    
    button_player: int = 0
    small_blind: int = 1
    big_blind: int = 2
    
    hand_number: int = 0
    
    MAX_RAISES_PER_ROUND = 2
    showdown = Showdown()
    


    def reset_hand(self):
        self.deck.reset_deck()
        self.deck.shuffle_deck()

        self.player_cards = [[],[]]
        self.public_cards = []

        self.pot = 0
        self.player_contributions = [0, 0]

        self.current_player = 0
        self.round_bets = [0, 0]

        self.terminal = False
        self.folded_player = None

        self.action_history = []
        self.actions_this_round = []
        self.raises_this_round = 0
        self.payoffs = [0, 0]

        self.street = Street.PREFLOP.value
        
    def setup_preflop(self):
        
        button_player = self.button_player
        big_blind = 1-button_player
        self.round_bets[button_player] += self.small_blind
        self.round_bets[big_blind] += self.big_blind
        
        self.player_contributions[button_player] += self.small_blind
        self.player_contributions[big_blind] += self.big_blind
        
        self.pot += self.big_blind + self.small_blind
        
        self.player_cards[0] = self.deck.draw_multiple_cards(2)
        self.player_cards[1] = self.deck.draw_multiple_cards(2)
        
        self.current_player = button_player
        
        
    def deal_flop(self):
        if self.public_cards:
            raise Exception(f"Public cards present when dealing flop: {self.public_cards}. Expected none cards.") 
        self.public_cards += self.deck.draw_multiple_cards(3)
        
    def deal_turn(self):
        if len(self.public_cards) != 3:
            raise Exception(f"Incorrect number of cards for turn: {self.public_cards}. Expected 3 cards.")
        self.public_cards += [self.deck.draw_card()]
    
    def deal_river(self):
        if len(self.public_cards) != 4:
            raise Exception(f"Incorrect number of cards for river: {self.public_cards}. Expected 4 cards.")
        self.public_cards += [self.deck.draw_card()]
        
    def amount_to_call(self,player):
        return max(self.round_bets) - self.round_bets[player]
    
    def legal_actions(self):
        if self.terminal:
            return []

        can_raise = False
        to_call = self.amount_to_call(self.current_player)

        if self.raises_this_round < self.MAX_RAISES_PER_ROUND:
            can_raise = True

        if to_call == 0:
            if can_raise:
                return [Action.CHECK_CALL,Action.BET_RAISE]
            return [Action.CHECK_CALL]
        
        if to_call > 0 and can_raise:
            return [Action.FOLD,Action.CHECK_CALL,Action.BET_RAISE]
        
        return [Action.FOLD,Action.CHECK_CALL]
    
    def bet_size(self):
        if self.street in [Street.PREFLOP,Street.FLOP]:
            return 2 
        return 4
        
    def is_round_over(self):
        if self.terminal:
            return True
    
        return (
            len(self.actions_this_round) >= 2
            and self.round_bets[0] == self.round_bets[1]
        )
    
    def advance_round(self):
        self.street += 1 
        street = self.street
        
        self.round_bets = [0, 0]
        self.actions_this_round = []
        self.raises_this_round = 0
        
        if street == Street.FLOP.value:
            self.deal_flop()
        elif street == Street.TURN.value:
            self.deal_turn() 
        elif street == Street.RIVER.value:
            self.deal_river()
        else:
            self.resolve_showdown()
            return
            
        self.current_player = 1 - self.button_player
            
    def resolve_showdown(self):
        self.terminal = True
        p0_payoff,p1_payoff = self.showdown.resolve_showdown(
            self.player_cards[0], self.player_cards[1], self.public_cards, self.pot)
        
        self.award_pot(p0_payoff, p1_payoff)
    
        
    def apply_action(self, action):
        if self.terminal:
            raise ValueError("Cannot apply action to terminal state")

        if action not in self.legal_actions():
            raise ValueError(f"Illegal action: {action}")

        self.actions_this_round.append(action)
        to_call = self.amount_to_call(self.current_player)
        self.action_history.append((self.current_player, self.street, action, to_call))
        

        if action == Action.CHECK_CALL:
            if self.amount_to_call(self.current_player) == 0:
                # check
                pass
            else:
                # call
                self.apply_call()

        elif action == Action.BET_RAISE:
            if self.amount_to_call(self.current_player) == 0:
                #bet
                self.apply_bet()
            else:
                #raise
                self.apply_raise()

        elif action == Action.FOLD:
            self.apply_fold()
            return

        if self.is_round_over():
            self.advance_round()
        else:
            self.current_player = 1 - self.current_player
            
    def apply_bet(self):
        bet_amount = self.bet_size()
        current_player = self.current_player

        self.round_bets[current_player] += bet_amount
        self.player_contributions[current_player] += bet_amount

        self.pot += bet_amount
        self.raises_this_round += 1

    def apply_raise(self):
        bet_amount = self.bet_size()+self.amount_to_call(self.current_player)
        current_player = self.current_player

        self.round_bets[current_player] += bet_amount
        self.player_contributions[current_player] += bet_amount

        self.pot += bet_amount
        self.raises_this_round += 1

    def apply_call(self):
        bet_amount = self.amount_to_call(self.current_player)
        current_player = self.current_player

        self.round_bets[current_player] += bet_amount
        self.player_contributions[current_player] += bet_amount

        self.pot += bet_amount
        
    def apply_fold(self):
        loser = self.current_player
        winner = 1-loser
        self.folded_player = loser
        
        self.payoffs[winner] = self.pot - self.player_contributions[winner]
        self.payoffs[loser] = -self.player_contributions[loser]
        self.terminal = True
        
    def award_pot(self,p0,p1):
        pot = self.pot
        self.payoffs[0] = (-pot/2) + p0
        self.payoffs[1] = (-pot/2) + p1
        
    def get_observation(self, player):
        return {
            "private_cards": self.player_cards[player].copy(),
            "public_cards": self.public_cards.copy(),
            "street": self.street,
            "pot": self.pot,
            "player_contributions": self.player_contributions.copy(),
            "round_bets": self.round_bets.copy(),
            "current_player": self.current_player,
            "button_player": self.button_player,
            "legal_actions": self.legal_actions(),
            "amount_to_call": self.amount_to_call(player),
            "raises_this_round": self.raises_this_round,
            "actions_this_round": self.actions_this_round.copy(),
            "action_history": self.action_history.copy(),
        }

    
    def clone(self):
        new_state = GameState.__new__(GameState)
    
        new_state.deck = self.deck.clone()
    
        new_state.player_cards = [
            self.player_cards[0].copy(),
            self.player_cards[1].copy(),
        ]
    
        new_state.public_cards = self.public_cards.copy()
    
        new_state.pot = self.pot
        new_state.player_contributions = self.player_contributions.copy()
        new_state.current_player = self.current_player
        new_state.street = self.street
        new_state.round_bets = self.round_bets.copy()
    
        new_state.terminal = self.terminal
        new_state.folded_player = self.folded_player
    
        new_state.action_history = self.action_history.copy()
        new_state.raises_this_round = self.raises_this_round
        new_state.actions_this_round = self.actions_this_round.copy()
        new_state.payoffs = self.payoffs.copy()
    
        new_state.button_player = self.button_player
        new_state.small_blind = self.small_blind
        new_state.big_blind = self.big_blind
        new_state.hand_number = self.hand_number
    
        return new_state
        

        

        
