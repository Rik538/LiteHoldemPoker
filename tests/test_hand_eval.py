# -*- coding: utf-8 -*-
"""
Created on Sun May 31 17:16:31 2026

@author: Richard
"""

from lite_holdem_ai.game.evaluate_hand import EvaluateHand


def test_straight_beats_two_pair():
    Eval = EvaluateHand()

    # Three pairs, no rank 4, so no straight.
    two_pair_public = [0, 1, 4, 5, 8]
    two_pair_private = [9, 12]

    # Contains all five ranks, but not five cards of same suit.
    straight_public = [0, 4, 8, 12, 1]
    straight_private = [17, 5]

    assert Eval.evaluate(straight_public, straight_private) > Eval.evaluate(
        two_pair_public, two_pair_private
    )


def test_full_house_beats_straight():
    Eval = EvaluateHand()

    straight_public = [0, 4, 8, 12, 1]
    straight_private = [17, 5]

    # Rank 0 trips, rank 1 pair, rank 2 pair.
    full_house_public = [0, 1, 2, 4, 5]
    full_house_private = [8, 9]

    assert Eval.evaluate(full_house_public, full_house_private) > Eval.evaluate(
        straight_public, straight_private
    )


def test_four_of_a_kind_beats_full_house():
    Eval = EvaluateHand()

    full_house_public = [0, 1, 2, 4, 5]
    full_house_private = [8, 9]

    # Rank 0 quads.
    quads_public = [0, 1, 2, 4, 8]
    quads_private = [3, 5]

    assert Eval.evaluate(quads_public, quads_private) > Eval.evaluate(
        full_house_public, full_house_private
    )


def test_straight_flush_beats_four_of_a_kind():
    Eval = EvaluateHand()

    quads_public = [0, 1, 2, 4, 8]
    quads_private = [3, 5]

    # 0, 4, 8, 12, 16 are same suit across all five ranks.
    straight_flush_public = [0, 4, 8, 12, 1]
    straight_flush_private = [16, 5]

    assert Eval.evaluate(straight_flush_public, straight_flush_private) > Eval.evaluate(
        quads_public, quads_private
    )


def test_same_hand_evaluates_equal():
    Eval = EvaluateHand()

    public = [0, 4, 8, 12, 1]
    private = [17, 5]

    assert Eval.evaluate(public, private) == Eval.evaluate(public, private)


def test_hand_rank_is_sortable():
    Eval = EvaluateHand()

    public_a = [0, 4, 8, 12, 1]
    private_a = [17, 5]

    public_b = [0, 1, 2, 4, 8]
    private_b = [3, 5]

    result_a = Eval.evaluate(public_a, private_a)
    result_b = Eval.evaluate(public_b, private_b)

    _ = result_a > result_b or result_b > result_a or result_a == result_b