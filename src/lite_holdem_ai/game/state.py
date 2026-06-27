# -*- coding: utf-8 -*-
"""
Created on Sun May 17 17:45:09 2026

@author: Richard
"""



from dataclasses import dataclass, field
from .deck import Deck



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
    payoffs: list[float] = field(default_factory=lambda: [0, 0])
    
    button_player: int = 0
    small_blind: int = 1
    big_blind: int = 2
    
    hand_number: int = 0
    
    MAX_RAISES_PER_ROUND = 2
    
        
    
    
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
        

        

        
