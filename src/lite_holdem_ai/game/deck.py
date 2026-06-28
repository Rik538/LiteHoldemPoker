# -*- coding: utf-8 -*-
"""
Created on Sun May 17 14:25:01 2026

@author: Richard
"""

from .cards import Cards
import random

class Deck():
    
    def __init__(self,seed=None):
        self.C = Cards()
        self.deck = []
        self.rng = random.Random(seed)
        self.build_deck()
    
    def build_deck(self):
        self.deck = list(range(20))
                
    def reset_deck(self):
        self.build_deck()
        
    def get_cards_left(self):
        return len(self.deck)
    
    def shuffle_deck(self):
        self.rng.shuffle(self.deck)

        
    def draw_card(self):
        return self.deck.pop()
    
    def draw_multiple_cards(self,no_cards):
        cards = []
        for x in range(no_cards):
            cards.append(self.draw_card())
            
        return cards
            
    def cards_remaining(self,cards_removed):
        full_deck = list(range(20))
        
        for card in cards_removed:
            full_deck.remove(card)
            
        return full_deck
    
    def remove_card(self,card):
        self.deck.remove(card)
        
    def contains(self,card):
        if card in self.deck:
            return True 
        return False
    
    def clone(self):
        cloned = Deck.__new__(Deck)
    
        cloned.deck = self.deck.copy()
    
        # Keep the same RNG object instead of deep-copying it.
        # CFR branch traversal should not need an independent random generator.
        if hasattr(self, "rng"):
            cloned.rng = self.rng
    
        return cloned
    
    def reseed(self, seed):
        self.rng.seed(seed)
            

        
    
    