# -*- coding: utf-8 -*-
"""
Created on Sun May 31 18:14:56 2026

@author: Richard
"""

from lite_holdem_ai.agents.random_agent import RandomAgent
from lite_holdem_ai.evaluation.match import MatchRunner
from lite_holdem_ai.game.environment import LiteHoldemEnv


def test_match_runner_can_play_one_hand():
    runner = MatchRunner(
        env_factory=lambda: LiteHoldemEnv(),
        agents=[
            RandomAgent(seed=1, name="Random A"),
            RandomAgent(seed=2, name="Random B"),
        ],
    )

    payoffs, state = runner.play_hand()

    assert state.terminal
    assert len(payoffs) == 2
    assert sum(payoffs) == 0


def test_match_runner_can_play_many_hands_without_seat_swap():
    runner = MatchRunner(
        env_factory=lambda: LiteHoldemEnv(),
        agents=[
            RandomAgent(seed=1, name="Random A"),
            RandomAgent(seed=2, name="Random B"),
        ],
    )

    result = runner.play_many(hands_per_seat=20, swap_seats=False)

    assert result.hands_played == 20
    assert result.agent0_total_payoff + result.agent1_total_payoff == 0
    assert result.agent0_net_wins + result.agent1_net_wins + result.net_draws == 20


def test_match_runner_can_play_many_hands_with_seat_swap():
    runner = MatchRunner(
        env_factory=lambda: LiteHoldemEnv(),
        agents=[
            RandomAgent(seed=1, name="Random A"),
            RandomAgent(seed=2, name="Random B"),
        ],
    )

    result = runner.play_many(hands_per_seat=20, swap_seats=True)

    assert result.hands_played == 40
    assert result.agent0_total_payoff + result.agent1_total_payoff == 0
    assert result.agent0_net_wins + result.agent1_net_wins + result.net_draws == 40


def test_match_result_summary_contains_main_metrics():
    runner = MatchRunner(
        env_factory=lambda: LiteHoldemEnv(),
        agents=[
            RandomAgent(seed=1, name="Random A"),
            RandomAgent(seed=2, name="Random B"),
        ],
    )

    result = runner.play_many(hands_per_seat=10, swap_seats=True)
    summary = result.summary()

    assert summary["hands_played"] == 20
    assert "agent0_avg_payoff" in summary
    assert "agent1_avg_payoff" in summary
    assert "terminal_by_fold" in summary
    assert "terminal_by_showdown" in summary