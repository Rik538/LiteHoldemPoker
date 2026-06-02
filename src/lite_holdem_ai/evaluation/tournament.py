# -*- coding: utf-8 -*-
"""
Created on Sun May 31 14:29:08 2026

@author: Richard
"""

from dataclasses import dataclass, field

from lite_holdem_ai.evaluation.match import MatchRunner
from lite_holdem_ai.game.environment import LiteHoldemEnv


@dataclass
class TournamentResult:
    agent_names: list[str]
    results: dict[tuple[str, str], object] = field(default_factory=dict)

    def payoff_table(self) -> dict[str, dict[str, float]]:
        table = {
            row_name: {col_name: 0.0 for col_name in self.agent_names}
            for row_name in self.agent_names
        }

        for (agent0_name, agent1_name), result in self.results.items():
            table[agent0_name][agent1_name] = result.agent0_avg_payoff
            table[agent1_name][agent0_name] = result.agent1_avg_payoff

        return table

    def print_payoff_table(self) -> None:
        table = self.payoff_table()

        name_width = max(len(name) for name in self.agent_names)
        col_width = 12

        header = " " * (name_width + 2)
        for name in self.agent_names:
            header += f"{name:>{col_width}}"
        print(header)

        for row_name in self.agent_names:
            row = f"{row_name:<{name_width}}  "
            for col_name in self.agent_names:
                row += f"{table[row_name][col_name]:>{col_width}.4f}"
            print(row)

    def rankings(self) -> list[tuple[str, float]]:
        table = self.payoff_table()

        scores = {}

        for agent_name in self.agent_names:
            opponents = [
                other_name
                for other_name in self.agent_names
                if other_name != agent_name
            ]

            if not opponents:
                scores[agent_name] = 0.0
                continue

            scores[agent_name] = sum(
                table[agent_name][opponent_name]
                for opponent_name in opponents
            ) / len(opponents)

        return sorted(scores.items(), key=lambda item: item[1], reverse=True)

    def print_rankings(self) -> None:
        print("Rankings:")
        for rank, (agent_name, score) in enumerate(self.rankings(), start=1):
            print(f"{rank}. {agent_name}: {score:.4f}")
            
    def to_csv(self, path: str) -> None:
        table = self.payoff_table()
    
        with open(path, "w", encoding="utf-8") as f:
            f.write("agent," + ",".join(self.agent_names) + "\n")
    
            for row_name in self.agent_names:
                values = [
                    f"{table[row_name][col_name]:.6f}"
                    for col_name in self.agent_names
                ]
                f.write(row_name + "," + ",".join(values) + "\n")


class TournamentRunner:
    def __init__(
        self,
        agents: list,
        env_factory=lambda: LiteHoldemEnv(),
    ):
        if len(agents) < 2:
            raise ValueError("TournamentRunner requires at least two agents")

        self.agents = agents
        self.env_factory = env_factory

    def run(
        self,
        hands_per_seat: int = 10_000,
        include_self_play: bool = False,
    ) -> TournamentResult:
        agent_names = [
            getattr(agent, "name", type(agent).__name__)
            for agent in self.agents
        ]

        result = TournamentResult(agent_names=agent_names)

        for i, agent_a in enumerate(self.agents):
            for j, agent_b in enumerate(self.agents):
                if not include_self_play and i == j:
                    continue

                # Only run each unordered pair once.
                if j < i:
                    continue

                runner = MatchRunner(
                    env_factory=self.env_factory,
                    agents=[agent_a, agent_b],
                )

                match_result = runner.play_many(
                    hands_per_seat=hands_per_seat,
                    swap_seats=True,
                )

                agent_a_name = getattr(agent_a, "name", type(agent_a).__name__)
                agent_b_name = getattr(agent_b, "name", type(agent_b).__name__)

                result.results[(agent_a_name, agent_b_name)] = match_result

        return result
    
    