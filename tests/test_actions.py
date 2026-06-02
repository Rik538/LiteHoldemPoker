# -*- coding: utf-8 -*-
"""
Created on Sun May 31 17:14:05 2026

@author: Richard
"""

from lite_holdem_ai.game.actions import Action


def test_action_members_exist():
    assert Action.FOLD
    assert Action.CHECK_CALL
    assert Action.BET_RAISE