# -*- coding: utf-8 -*-
"""
Match running utilities for Lite Hold'em.
"""

from collections.abc import Callable

from lite_holdem_ai.evaluation.results import MatchResult
from lite_holdem_ai.game.environment import LiteHoldemEnv


class MatchRunner:
    def __init__(
        self,
        env_factory: Callable[[], LiteHoldemEnv],
        agents: list,
        max_steps_per_hand: int = 200,
    ):
        if len(agents) != 2:
            raise ValueError("MatchRunner currently supports exactly 2 agents")

        self.env_factory = env_factory
        self.agents = agents
        self.max_steps_per_hand = max_steps_per_hand

    def agent_name(self, index: int) -> str:
        return getattr(self.agents[index], "name", type(self.agents[index]).__name__)

    def play_hand(self) -> tuple[list[int], object]:
        env = self.env_factory()
        env.reset()

        steps = 0

        while not env.is_terminal():
            if steps >= self.max_steps_per_hand:
                raise RuntimeError(
                    f"Hand exceeded max_steps_per_hand={self.max_steps_per_hand}. "
                    "This usually means the betting-round transition logic is stuck."
                )

            player = env.current_player
            agent = self.agents[player]

            observation = env.observe(player)
            legal_actions = env.legal_actions()

            if not legal_actions:
                raise RuntimeError(
                    f"No legal actions for player {player} in non-terminal state."
                )

            action = agent.select_action(observation, legal_actions)

            if action not in legal_actions:
                agent_name = getattr(agent, "name", type(agent).__name__)
                raise ValueError(
                    f"{agent_name} returned illegal action {action}. "
                    f"Legal actions were {legal_actions}"
                )

            env.step(action)
            steps += 1

        payoffs = env.payoffs()

        assert env.is_terminal()
        assert len(payoffs) == 2
        assert sum(payoffs) == 0

        return payoffs, env.state

    def play_many(
        self,
        hands_per_seat: int,
        swap_seats: bool = True,
    ) -> MatchResult:
        result = MatchResult(
            agent0_name=self.agent_name(0),
            agent1_name=self.agent_name(1),
        )

        for _ in range(hands_per_seat):
            # Agent 0 as player 0, Agent 1 as player 1.
            payoffs, state = self.play_hand()

            result.record_hand(
                payoff_for_agent0=payoffs[0],
                payoff_for_agent1=payoffs[1],
                state=state,
            )

            if swap_seats:
                # Agent 1 as player 0, Agent 0 as player 1.
                swapped_runner = MatchRunner(
                    env_factory=self.env_factory,
                    agents=[self.agents[1], self.agents[0]],
                    max_steps_per_hand=self.max_steps_per_hand,
                )

                payoffs, state = swapped_runner.play_hand()

                # Convert seat payoffs back to original agent order.
                result.record_hand(
                    payoff_for_agent0=payoffs[1],
                    payoff_for_agent1=payoffs[0],
                    state=state,
                )

        return result