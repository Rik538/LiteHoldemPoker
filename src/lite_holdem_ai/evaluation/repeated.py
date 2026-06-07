# -*- coding: utf-8 -*-
"""
Repeated tournament evaluation.

Runs multiple tournament evaluations and aggregates payoff tables cell by cell.
"""

import csv
import math
from collections import defaultdict
from pathlib import Path

from lite_holdem_ai.evaluation.tournament import TournamentRunner
from lite_holdem_ai.game.environment import LiteHoldemEnv


class RepeatedTournamentResult:
    def __init__(self, agent_names):
        self.agent_names = agent_names
        self.samples = defaultdict(list)

    def add_payoff_table(self, table):
        for row_agent in self.agent_names:
            for col_agent in self.agent_names:
                value = table[row_agent][col_agent]
                self.samples[(row_agent, col_agent)].append(value)

    def mean_table(self):
        table = {}

        for row_agent in self.agent_names:
            table[row_agent] = {}

            for col_agent in self.agent_names:
                values = self.samples[(row_agent, col_agent)]

                if len(values) == 0:
                    table[row_agent][col_agent] = 0.0
                else:
                    table[row_agent][col_agent] = sum(values) / len(values)

        return table

    def cell_stats(self, row_agent, col_agent):
        values = self.samples[(row_agent, col_agent)]
        n = len(values)

        if n == 0:
            raise ValueError("No samples for this matchup")

        mean = sum(values) / n

        if n == 1:
            std = 0.0
            stderr = 0.0
            ci95 = 0.0
        else:
            variance = sum((x - mean) ** 2 for x in values) / (n - 1)
            std = math.sqrt(variance)
            stderr = std / math.sqrt(n)
            ci95 = 1.96 * stderr

        return {
            "n": n,
            "mean": mean,
            "std": std,
            "stderr": stderr,
            "ci95": ci95,
        }

    def ranking_scores(self):
        mean_table = self.mean_table()
        scores = {}

        for agent in self.agent_names:
            opponents = [
                other for other in self.agent_names
                if other != agent
            ]

            scores[agent] = sum(
                mean_table[agent][opponent]
                for opponent in opponents
            ) / len(opponents)

        return sorted(
            scores.items(),
            key=lambda item: item[1],
            reverse=True,
        )

    def ranking_stats(self):
        """
        Computes ranking score uncertainty by calculating each agent's tournament
        score per repeated run, then taking mean/stderr/CI over those scores.
        """
        if not self.agent_names:
            return []

        first_key = (self.agent_names[0], self.agent_names[0])
        n_runs = len(self.samples[first_key])

        rows = []

        for agent in self.agent_names:
            opponents = [
                other for other in self.agent_names
                if other != agent
            ]

            run_scores = []

            for run_idx in range(n_runs):
                score = sum(
                    self.samples[(agent, opponent)][run_idx]
                    for opponent in opponents
                ) / len(opponents)

                run_scores.append(score)

            mean = sum(run_scores) / len(run_scores)

            if len(run_scores) == 1:
                std = 0.0
                stderr = 0.0
                ci95 = 0.0
            else:
                variance = sum((x - mean) ** 2 for x in run_scores) / (len(run_scores) - 1)
                std = math.sqrt(variance)
                stderr = std / math.sqrt(len(run_scores))
                ci95 = 1.96 * stderr

            rows.append(
                {
                    "agent": agent,
                    "n": len(run_scores),
                    "mean": mean,
                    "std": std,
                    "stderr": stderr,
                    "ci95": ci95,
                }
            )

        return sorted(
            rows,
            key=lambda row: row["mean"],
            reverse=True,
        )

    def print_mean_table(self):
        table = self.mean_table()

        header = "".ljust(18)

        for name in self.agent_names:
            header += name.rjust(14)

        print(header)

        for row_name in self.agent_names:
            row = row_name.ljust(18)

            for col_name in self.agent_names:
                row += f"{table[row_name][col_name]:14.4f}"

            print(row)

    def print_rankings(self):
        print("Rankings:")

        for rank, row in enumerate(self.ranking_stats(), start=1):
            print(
                f"{rank}. {row['agent']}: "
                f"{row['mean']:.4f} ± {row['ci95']:.4f} "
                f"(n={row['n']})"
            )

    def to_csv(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            writer.writerow([
                "row_agent",
                "col_agent",
                "n",
                "mean",
                "std",
                "stderr",
                "ci95",
            ])

            for row_agent in self.agent_names:
                for col_agent in self.agent_names:
                    stats = self.cell_stats(row_agent, col_agent)

                    writer.writerow([
                        row_agent,
                        col_agent,
                        stats["n"],
                        stats["mean"],
                        stats["std"],
                        stats["stderr"],
                        stats["ci95"],
                    ])


class RepeatedTournamentRunner:
    def __init__(
        self,
        agent_factory,
        env_factory=lambda: LiteHoldemEnv(),
    ):
        self.agent_factory = agent_factory
        self.env_factory = env_factory

        test_agents = self.agent_factory(0)

        if len(test_agents) < 2:
            raise ValueError("RepeatedTournamentRunner requires at least two agents")

        self.agent_names = [
            getattr(agent, "name", type(agent).__name__)
            for agent in test_agents
        ]

        for agent in test_agents:
            if hasattr(agent, "close"):
                agent.close()

    def run(
        self,
        hands_per_seat: int = 10_000,
        include_self_play: bool = False,
        number_tournaments: int = 5,
    ) -> RepeatedTournamentResult:
        if number_tournaments <= 0:
            raise ValueError("number_tournaments must be positive")

        repeated = RepeatedTournamentResult(self.agent_names)

        for run_seed in range(number_tournaments):
            agents = self.agent_factory(run_seed)

            runner = TournamentRunner(
                agents=agents,
                env_factory=self.env_factory,
            )

            result = runner.run(
                hands_per_seat=hands_per_seat,
                include_self_play=include_self_play,
            )

            repeated.add_payoff_table(result.payoff_table())

            for agent in agents:
                if hasattr(agent, "close"):
                    agent.close()

        return repeated