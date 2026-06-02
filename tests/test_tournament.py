# -*- coding: utf-8 -*-
"""
Created on Tue Jun  2 17:40:36 2026

@author: Richard
"""

from lite_holdem_ai.agents.aggressive_agent import AggressiveAgent
from lite_holdem_ai.agents.passive_agent import PassiveAgent
from lite_holdem_ai.agents.random_agent import RandomAgent
from lite_holdem_ai.evaluation.tournament import TournamentRunner
from lite_holdem_ai.game.environment import LiteHoldemEnv


def test_tournament_runner_requires_at_least_two_agents():
    try:
        TournamentRunner([RandomAgent(seed=1)])
        assert False, "Expected ValueError"
    except ValueError:
        pass


def test_tournament_runner_runs_pairwise_matches():
    agents = [
        RandomAgent(seed=1, name="Random"),
        PassiveAgent(name="Passive"),
        AggressiveAgent(name="Aggressive"),
    ]

    runner = TournamentRunner(
        agents=agents,
        env_factory=lambda: LiteHoldemEnv(),
    )

    result = runner.run(hands_per_seat=2, include_self_play=False)

    expected_pairs = {
        ("Random", "Passive"),
        ("Random", "Aggressive"),
        ("Passive", "Aggressive"),
    }

    assert set(result.results.keys()) == expected_pairs


def test_tournament_payoff_table_has_all_agents():
    agents = [
        RandomAgent(seed=1, name="Random"),
        PassiveAgent(name="Passive"),
        AggressiveAgent(name="Aggressive"),
    ]

    runner = TournamentRunner(
        agents=agents,
        env_factory=lambda: LiteHoldemEnv(),
    )

    result = runner.run(hands_per_seat=2, include_self_play=False)
    table = result.payoff_table()

    assert set(table.keys()) == {"Random", "Passive", "Aggressive"}

    for row in table.values():
        assert set(row.keys()) == {"Random", "Passive", "Aggressive"}


def test_tournament_payoff_table_is_antisymmetric():
    agents = [
        RandomAgent(seed=1, name="Random"),
        PassiveAgent(name="Passive"),
        AggressiveAgent(name="Aggressive"),
    ]

    runner = TournamentRunner(
        agents=agents,
        env_factory=lambda: LiteHoldemEnv(),
    )

    result = runner.run(hands_per_seat=2, include_self_play=False)
    table = result.payoff_table()

    names = ["Random", "Passive", "Aggressive"]

    for a in names:
        for b in names:
            assert table[a][b] == -table[b][a]


def test_tournament_rankings_include_all_agents():
    agents = [
        RandomAgent(seed=1, name="Random"),
        PassiveAgent(name="Passive"),
        AggressiveAgent(name="Aggressive"),
    ]

    runner = TournamentRunner(
        agents=agents,
        env_factory=lambda: LiteHoldemEnv(),
    )

    result = runner.run(hands_per_seat=2, include_self_play=False)
    rankings = result.rankings()

    assert len(rankings) == 3
    assert {name for name, score in rankings} == {
        "Random",
        "Passive",
        "Aggressive",
    }


def test_tournament_result_can_export_csv(tmp_path):
    agents = [
        RandomAgent(seed=1, name="Random"),
        PassiveAgent(name="Passive"),
        AggressiveAgent(name="Aggressive"),
    ]

    runner = TournamentRunner(
        agents=agents,
        env_factory=lambda: LiteHoldemEnv(),
    )

    result = runner.run(hands_per_seat=2, include_self_play=False)

    output_path = tmp_path / "tournament.csv"
    result.to_csv(str(output_path))

    assert output_path.exists()

    text = output_path.read_text(encoding="utf-8")

    assert "agent,Random,Passive,Aggressive" in text
    assert "Random" in text
    assert "Passive" in text
    assert "Aggressive" in text