# -*- coding: utf-8 -*-
"""
Created on Tue Jun  2 17:39:49 2026

@author: Richard
"""

from lite_holdem_ai.evaluation.results import MatchResult
from lite_holdem_ai.game.actions import Action


class DummyState:
    def __init__(self):
        self.terminal = True
        self.pot = 10
        self.folded_player = None
        self.street = 4
        self.action_history = [
            (0, 0, Action.BET_RAISE, 0),
            (1, 0, Action.CHECK_CALL, 2),
            (0, 1, Action.CHECK_CALL, 0),
            (1, 1, Action.BET_RAISE, 0),
        ]


def test_match_result_records_showdown_hand():
    result = MatchResult(
        agent0_name="A",
        agent1_name="B",
    )

    state = DummyState()

    result.record_hand(
        payoff_for_agent0=5,
        payoff_for_agent1=-5,
        state=state,
    )

    assert result.hands_played == 1
    assert result.agent0_total_payoff == 5
    assert result.agent1_total_payoff == -5
    assert result.terminal_by_showdown == 1
    assert result.terminal_by_fold == 0
    assert result.agent0_showdown_wins == 1
    assert result.agent1_showdown_wins == 0
    assert result.showdown_splits == 0
    assert result.avg_final_pot == 10


def test_match_result_records_fold_hand():
    result = MatchResult(
        agent0_name="A",
        agent1_name="B",
    )

    state = DummyState()
    state.folded_player = 1
    state.street = 0

    result.record_hand(
        payoff_for_agent0=3,
        payoff_for_agent1=-3,
        state=state,
    )

    assert result.hands_played == 1
    assert result.terminal_by_fold == 1
    assert result.terminal_by_showdown == 0
    assert result.agent0_fold_wins == 1
    assert result.agent1_folds == 1


def test_match_result_average_payoff_and_zero_sum_check():
    result = MatchResult(
        agent0_name="A",
        agent1_name="B",
    )

    state = DummyState()

    result.record_hand(2, -2, state)
    result.record_hand(-1, 1, state)

    assert result.hands_played == 2
    assert result.agent0_avg_payoff == 0.5
    assert result.agent1_avg_payoff == -0.5
    assert result.total_payoff_check == 0


def test_match_result_records_action_counts():
    result = MatchResult(
        agent0_name="A",
        agent1_name="B",
    )

    state = DummyState()

    result.record_hand(5, -5, state)

    assert result.action_counts[Action.BET_RAISE] == 2
    assert result.action_counts[Action.CHECK_CALL] == 2
    assert result.action_counts_by_agent[(0, Action.BET_RAISE)] == 1
    assert result.action_counts_by_agent[(1, Action.BET_RAISE)] == 1
    assert result.facing_bet_counts_by_agent[1] == 1


def test_match_result_summary_contains_core_metrics():
    result = MatchResult(
        agent0_name="A",
        agent1_name="B",
    )

    state = DummyState()
    result.record_hand(5, -5, state)

    summary = result.summary()

    assert summary["agent0"] == "A"
    assert summary["agent1"] == "B"
    assert summary["hands_played"] == 1
    assert "agent0_avg_payoff" in summary
    assert "terminal_by_showdown" in summary
    assert "action_counts" in summary