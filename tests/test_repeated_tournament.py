# -*- coding: utf-8 -*-
"""
Created on Sun Jun  7 20:58:44 2026

@author: Richard
"""

import pytest

from lite_holdem_ai.agents.passive_agent import PassiveAgent
from lite_holdem_ai.agents.random_agent import RandomAgent
from lite_holdem_ai.evaluation.repeated import (
    RepeatedTournamentResult,
    RepeatedTournamentRunner,
)
from lite_holdem_ai.game.environment import LiteHoldemEnv


def make_sample_table():
    return {
        "A": {
            "A": 0.0,
            "B": 1.0,
            "C": -0.5,
        },
        "B": {
            "A": -1.0,
            "B": 0.0,
            "C": 0.25,
        },
        "C": {
            "A": 0.5,
            "B": -0.25,
            "C": 0.0,
        },
    }


def make_second_sample_table():
    return {
        "A": {
            "A": 0.0,
            "B": 2.0,
            "C": -1.5,
        },
        "B": {
            "A": -2.0,
            "B": 0.0,
            "C": 0.75,
        },
        "C": {
            "A": 1.5,
            "B": -0.75,
            "C": 0.0,
        },
    }


def test_repeated_result_can_be_constructed():
    result = RepeatedTournamentResult(["A", "B", "C"])

    assert result.agent_names == ["A", "B", "C"]
    assert len(result.samples) == 0


def test_repeated_result_add_payoff_table():
    result = RepeatedTournamentResult(["A", "B", "C"])

    result.add_payoff_table(make_sample_table())

    assert result.samples[("A", "B")] == [1.0]
    assert result.samples[("B", "A")] == [-1.0]
    assert result.samples[("C", "C")] == [0.0]


def test_repeated_result_mean_table_single_sample():
    result = RepeatedTournamentResult(["A", "B", "C"])

    result.add_payoff_table(make_sample_table())

    table = result.mean_table()

    assert table["A"]["B"] == 1.0
    assert table["B"]["A"] == -1.0
    assert table["A"]["C"] == -0.5
    assert table["C"]["A"] == 0.5


def test_repeated_result_mean_table_multiple_samples():
    result = RepeatedTournamentResult(["A", "B", "C"])

    result.add_payoff_table(make_sample_table())
    result.add_payoff_table(make_second_sample_table())

    table = result.mean_table()

    assert table["A"]["B"] == pytest.approx(1.5)
    assert table["B"]["A"] == pytest.approx(-1.5)
    assert table["A"]["C"] == pytest.approx(-1.0)
    assert table["C"]["A"] == pytest.approx(1.0)


def test_repeated_result_cell_stats_single_sample():
    result = RepeatedTournamentResult(["A", "B", "C"])

    result.add_payoff_table(make_sample_table())

    stats = result.cell_stats("A", "B")

    assert stats["n"] == 1
    assert stats["mean"] == 1.0
    assert stats["std"] == 0.0
    assert stats["stderr"] == 0.0
    assert stats["ci95"] == 0.0


def test_repeated_result_cell_stats_multiple_samples():
    result = RepeatedTournamentResult(["A", "B", "C"])

    result.add_payoff_table(make_sample_table())
    result.add_payoff_table(make_second_sample_table())

    stats = result.cell_stats("A", "B")

    assert stats["n"] == 2
    assert stats["mean"] == pytest.approx(1.5)
    assert stats["std"] > 0.0
    assert stats["stderr"] > 0.0
    assert stats["ci95"] > 0.0


def test_repeated_result_cell_stats_missing_sample_raises():
    result = RepeatedTournamentResult(["A", "B"])

    with pytest.raises(ValueError):
        result.cell_stats("A", "B")


def test_repeated_result_ranking_scores():
    result = RepeatedTournamentResult(["A", "B", "C"])

    result.add_payoff_table(make_sample_table())
    result.add_payoff_table(make_second_sample_table())

    rankings = result.ranking_scores()

    assert len(rankings) == 3

    ranked_names = [name for name, score in rankings]

    assert set(ranked_names) == {"A", "B", "C"}

    # C should rank highest in the sample data:
    # C vs A positive, C vs B negative but small.
    scores = dict(rankings)
    assert scores["A"] == pytest.approx(0.25)
    assert scores["B"] == pytest.approx(-0.5)
    assert scores["C"] == pytest.approx(0.25)
    
    assert rankings[0][1] == pytest.approx(0.25)
    assert rankings[-1][0] == "B"


def test_repeated_result_ranking_stats():
    result = RepeatedTournamentResult(["A", "B", "C"])

    result.add_payoff_table(make_sample_table())
    result.add_payoff_table(make_second_sample_table())

    ranking_stats = result.ranking_stats()

    assert len(ranking_stats) == 3

    for row in ranking_stats:
        assert set(row.keys()) == {
            "agent",
            "n",
            "mean",
            "std",
            "stderr",
            "ci95",
        }

        assert row["n"] == 2
        assert row["std"] >= 0.0
        assert row["stderr"] >= 0.0
        assert row["ci95"] >= 0.0

    assert {row["agent"] for row in ranking_stats} == {"A", "B", "C"}


def test_repeated_result_to_csv(tmp_path):
    result = RepeatedTournamentResult(["A", "B", "C"])

    result.add_payoff_table(make_sample_table())
    result.add_payoff_table(make_second_sample_table())

    output_path = tmp_path / "repeated.csv"

    result.to_csv(output_path)

    assert output_path.exists()

    text = output_path.read_text(encoding="utf-8")

    assert "row_agent,col_agent,n,mean,std,stderr,ci95" in text
    assert "A,B,2" in text
    assert "B,A,2" in text
    assert "C,C,2" in text


def test_repeated_result_print_methods_do_not_crash(capsys):
    result = RepeatedTournamentResult(["A", "B", "C"])

    result.add_payoff_table(make_sample_table())
    result.add_payoff_table(make_second_sample_table())

    result.print_mean_table()
    result.print_rankings()

    captured = capsys.readouterr()

    assert "A" in captured.out
    assert "B" in captured.out
    assert "C" in captured.out
    assert "Rankings:" in captured.out


def test_repeated_runner_rejects_less_than_two_agents():
    def agent_factory(seed):
        return [
            RandomAgent(seed=seed, name="Random"),
        ]

    with pytest.raises(ValueError):
        RepeatedTournamentRunner(
            agent_factory=agent_factory,
            env_factory=lambda: LiteHoldemEnv(),
        )


def test_repeated_runner_can_be_constructed():
    def agent_factory(seed):
        return [
            RandomAgent(seed=seed, name="Random"),
            PassiveAgent(name="Passive"),
        ]

    runner = RepeatedTournamentRunner(
        agent_factory=agent_factory,
        env_factory=lambda: LiteHoldemEnv(),
    )

    assert runner.agent_names == ["Random", "Passive"]


def test_repeated_runner_rejects_non_positive_number_tournaments():
    def agent_factory(seed):
        return [
            RandomAgent(seed=seed, name="Random"),
            PassiveAgent(name="Passive"),
        ]

    runner = RepeatedTournamentRunner(
        agent_factory=agent_factory,
        env_factory=lambda: LiteHoldemEnv(),
    )

    with pytest.raises(ValueError):
        runner.run(
            hands_per_seat=1,
            include_self_play=False,
            number_tournaments=0,
        )


def test_repeated_runner_runs_multiple_tournaments():
    def agent_factory(seed):
        return [
            RandomAgent(seed=seed, name="Random"),
            PassiveAgent(name="Passive"),
        ]

    runner = RepeatedTournamentRunner(
        agent_factory=agent_factory,
        env_factory=lambda: LiteHoldemEnv(),
    )

    result = runner.run(
        hands_per_seat=2,
        include_self_play=False,
        number_tournaments=3,
    )

    assert isinstance(result, RepeatedTournamentResult)
    assert result.agent_names == ["Random", "Passive"]

    assert len(result.samples[("Random", "Passive")]) == 3
    assert len(result.samples[("Passive", "Random")]) == 3
    assert len(result.samples[("Random", "Random")]) == 3
    assert len(result.samples[("Passive", "Passive")]) == 3


def test_repeated_runner_mean_table_after_run():
    def agent_factory(seed):
        return [
            RandomAgent(seed=seed, name="Random"),
            PassiveAgent(name="Passive"),
        ]

    runner = RepeatedTournamentRunner(
        agent_factory=agent_factory,
        env_factory=lambda: LiteHoldemEnv(),
    )

    result = runner.run(
        hands_per_seat=2,
        include_self_play=False,
        number_tournaments=2,
    )

    table = result.mean_table()

    assert set(table.keys()) == {"Random", "Passive"}
    assert set(table["Random"].keys()) == {"Random", "Passive"}
    assert set(table["Passive"].keys()) == {"Random", "Passive"}

    assert table["Random"]["Passive"] == pytest.approx(
        -table["Passive"]["Random"]
    )


def test_repeated_runner_closes_agents():
    class CloseTrackingAgent(RandomAgent):
        def __init__(self, seed, name):
            super().__init__(seed=seed, name=name)
            self.closed = False

        def close(self):
            self.closed = True
            closed_agents.append(self)

    closed_agents = []

    def agent_factory(seed):
        return [
            CloseTrackingAgent(seed=seed, name="A"),
            CloseTrackingAgent(seed=seed + 1, name="B"),
        ]

    runner = RepeatedTournamentRunner(
        agent_factory=agent_factory,
        env_factory=lambda: LiteHoldemEnv(),
    )

    runner.run(
        hands_per_seat=1,
        include_self_play=False,
        number_tournaments=2,
    )

    # Two test agents from __init__, then two agents per tournament.
    assert len(closed_agents) == 2 + (2 * 2)

    assert all(agent.closed for agent in closed_agents)