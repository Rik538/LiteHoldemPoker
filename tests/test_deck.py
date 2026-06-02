# -*- coding: utf-8 -*-
"""
Created on Sun May 31 11:59:20 2026

@author: Richard
"""

from lite_holdem_ai.game.deck import Deck


def test_deck_has_six_cards():
    deck = Deck(seed=1)

    assert len(deck.deck) == 20



def test_draw_top_card_reduces_deck_size():
    deck = Deck(seed=1)

    before = len(deck.deck)
    card = deck.draw_card()
    after = len(deck.deck)

    assert card is not None
    assert after == before - 1


def test_drawing_all_cards_empties_deck():
    deck = Deck(seed=1)

    drawn_cards = []

    for _ in range(20):
        drawn_cards.append(deck.draw_card())

    assert len(drawn_cards) == 20
    assert len(deck.deck) == 0


def test_seeded_deck_is_reproducible():
    deck_a = Deck(seed=123)
    deck_a.shuffle_deck()
    deck_b = Deck(seed=123)
    deck_b.shuffle_deck()

    assert deck_a.deck == deck_b.deck
    
def test_all_cards_unique():
    deck = Deck(seed=1)
    
    unique_deck = list(dict.fromkeys(deck.deck))
    
    assert len(unique_deck) == 20
    
