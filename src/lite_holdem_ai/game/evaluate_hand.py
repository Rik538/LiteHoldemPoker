# -*- coding: utf-8 -*-
"""
Created on Sun May 17 15:22:05 2026

@author: Richard
"""
from enum import IntEnum
from .cards import Cards

class Hand(IntEnum):
    HIGH = 0
    PAIR = 1
    TWO_PAIR = 2
    THREE = 3
    STRAIGHT = 4
    FLUSH = 5
    FULL_HOUSE = 6
    FOUR = 7
    STRAIGHT_FLUSH = 8

class EvaluateHand():
    
    def __init__(self):
        self.C = Cards()
        
    def build_context(self,private_cards,public_cards):
        cards = private_cards+public_cards
        
        self.card_ranks = []
        self.card_suits = []
        
        
        for card in cards:
            self.card_ranks.append(self.C.card_rank(card).value)
            self.card_suits.append(self.C.card_suit(card).value)
            
        self.unique_ranks = list(dict.fromkeys(self.card_ranks))
        self.unique_ranks.sort(reverse=True)
        
        self.rank_appearances = {0:0,1:0,2:0,3:0,4:0}
        for rank in self.card_ranks:
            self.rank_appearances[rank] += 1 
            
        self.suit_appearances = {0:0,1:0,2:0,3:0}
        for suit in self.card_suits:
            self.suit_appearances[suit] += 1 
        
        
        
    
    def evaluate(self,private_cards,public_cards):
        
        self.build_context(private_cards, public_cards)
        
        result = self.is_straight_flush()
        if result: return result
        
        result = self.is_four_kind()
        if result: return result
        
        result = self.is_full_house()
        if result: return result
    
        result = self.is_flush(private_cards+public_cards)
        if result: return result
        
        result = self.is_straight()
        if result: return result
        
        result = self.is_three_kind()
        if result: return result 
        
        result = self.is_two_pair()
        if result: return result
        
        result = self.is_pair()
        if result: return result
        
        return self.find_high_card()
        
            

    
    def find_high_card(self):
        return (Hand.HIGH, tuple(self.unique_ranks[0:5]))
    
    def is_pair(self):
        
        pair = -1
            
        for rank in self.rank_appearances.keys():
            if self.rank_appearances[rank] == 2:
                if rank > pair:
                    pair = rank
                    
        if pair == -1:
            return None
                
        card_ranks = self.unique_ranks
        card_ranks.remove(pair)
        
        return (Hand.PAIR.value,tuple([pair])+tuple(card_ranks[0:3]))
    
    def is_two_pair(self):
        
        pairs = []
        
       
            
        for rank in self.rank_appearances.keys():
            if self.rank_appearances[rank] == 2:
                pairs.append(rank)
                    
        if len(pairs) < 2:
            return None
        
        pairs.sort(reverse=True)
        pairs = pairs[0:2]
        
        
        card_ranks = self.unique_ranks
        
        for pair in pairs:
            card_ranks.remove(pair)
        
    
        return (Hand.TWO_PAIR.value,tuple(pairs)+tuple([card_ranks[0]]))
    
    def is_three_kind(self):
        
        
        three = -1
        
        for rank in self.rank_appearances.keys():
            if self.rank_appearances[rank] == 3:
                if rank > three:
                    three = rank
        
        if three == -1:
            return None
                
        card_ranks = self.unique_ranks
        card_ranks.remove(three)
        
        return (Hand.THREE.value,tuple([three])+tuple(card_ranks[0:2]))
    
    def is_straight(self):

        if self.unique_ranks == [4,3,2,1,0]:
            return (Hand.STRAIGHT.value,(4,))        
        return None
    
    def is_flush(self,cards):
        
        
        flush_suit = -1
        flush_ranks = []
        

            
        for suit in self.suit_appearances.keys():
            if self.suit_appearances[suit] >= 5:
                flush_suit = suit
                
        if flush_suit == -1:
            return None
        
        for card in cards:
            if self.C.card_suit(card).value == flush_suit:
                flush_ranks.append(self.C.card_rank(card).value)
                
        flush_ranks.sort(reverse=True)
            
        return (Hand.FLUSH.value,tuple(flush_ranks[0:5]))
    
    def is_full_house(self):
        
       
        pairs = []
        three = -1
     
        for rank in self.rank_appearances.keys():
            if self.rank_appearances[rank] >= 3:
                if rank > three:
                    three = rank
            if self.rank_appearances[rank] >= 2:
                pairs.append(rank)
                
        if three in pairs:
            pairs.remove(three)
                
        if three == -1 or not pairs :
            return None
        
        
        
        pairs.sort(reverse=True)
        pair = pairs[0]
        
        return (Hand.FULL_HOUSE.value,(three,pair))
    
    def is_four_kind(self):
        

        four = -1
            
        for rank in self.rank_appearances.keys():
            if self.rank_appearances[rank] == 4:
                four = rank
                    
        if four == -1:
            return None
                
        card_ranks = self.unique_ranks
        card_ranks.remove(four)
        
        return (Hand.FOUR.value,tuple([four])+tuple([card_ranks[0]]))
    
    def is_straight_flush(self):
        

        flush_suit = -1
            
        for suit in self.suit_appearances.keys():
            if self.suit_appearances[suit] >= 5:
                flush_suit = suit
                
        if flush_suit == -1:
            return None

            
        return (Hand.STRAIGHT_FLUSH.value,(4,))
        
        
    
    

    

    