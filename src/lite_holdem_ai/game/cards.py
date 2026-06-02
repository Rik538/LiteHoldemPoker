# -*- coding: utf-8 -*-
"""
Created on Sun May 17 14:12:36 2026

@author: Richard
"""

from enum import IntEnum


class Rank(IntEnum):
    TEN = 0
    JACK = 1
    QUEEN = 2
    KING = 3
    ACE = 4


class Suit(IntEnum):
    CLUBS = 0
    DIAMONDS = 1
    HEARTS = 2
    SPADES = 3
    
    
    
class Cards():

    def make_card(self,rank: Rank, suit: Suit) -> int:
        return int(rank) * 4 + int(suit)
    
    def card_rank(self,card: int) -> Rank:
        return Rank(card // 4)


    def card_suit(self,card: int) -> Suit:
        return Suit(card % 4)
    
    
    def card_to_str(self,card: int) -> str:
        rank_symbols = {
            Rank.TEN: "T",
            Rank.JACK: "J",
            Rank.QUEEN: "Q",
            Rank.KING: "K",
            Rank.ACE: "A",
        }
    
        suit_symbols = {
            Suit.CLUBS: "c",
            Suit.DIAMONDS: "d",
            Suit.HEARTS: "h",
            Suit.SPADES: "s",
        }
    
        return rank_symbols[self.card_rank(card)] + suit_symbols[self.card_suit(card)]
    
    
    




    
