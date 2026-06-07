# -*- coding: utf-8 -*-
"""
External-sampling MCCFR trainer for Lite Hold'em.

This trainer is faster than the full CFRTrainer because:
- the traverser's actions are fully explored
- opponent actions are sampled
- initial deals are sampled through env.reset()

It uses the same infoset_builder system as CFRTrainer, so the trained nodes
can be used by the same CFRAgent.
"""

import pickle
import random

from lite_holdem_ai.cfr.node import ACTION_INDEX, CFRNode


class MCCFRTrainer:
    def __init__(
        self,
        infoset_builder,
        env_factory,
        seed: int | None = None,
    ):
        self.infoset_builder = infoset_builder
        self.env_factory = env_factory
        self.nodes = {}
        self.iterations_trained = 0

        self.rng = random.Random(seed)

    def get_node(self, info_set_key, legal_actions):
        if info_set_key not in self.nodes:
            node = CFRNode()
            node.legal_actions = legal_actions.copy()
            self.nodes[info_set_key] = node

        return self.nodes[info_set_key]

    def external_sampling_cfr(
        self,
        state,
        traverser: int,
        reach_traverser: float,
        reach_opponent: float,
    ):
        """
        External-sampling MCCFR recursion.

        traverser:
            The player currently being updated, either 0 or 1.

        reach_traverser:
            Probability of the traverser's own sampled/played sequence.

        reach_opponent:
            Probability of the opponent sampled sequence.

        Returns:
            Utility from the traverser's perspective.
        """
        if state.terminal:
            return state.payoffs[traverser]

        player = state.current_player
        legal_actions = state.legal_actions()

        if not legal_actions:
            raise RuntimeError("Non-terminal MCCFR state has no legal actions")

        info_key = self.infoset_builder.from_state(state, player)
        node = self.get_node(info_key, legal_actions)

        strategy = node.get_strategy(legal_actions)

        if player == traverser:
            return self._traverser_node(
                state=state,
                traverser=traverser,
                reach_traverser=reach_traverser,
                reach_opponent=reach_opponent,
                legal_actions=legal_actions,
                node=node,
                strategy=strategy,
            )

        return self._opponent_node(
            state=state,
            traverser=traverser,
            reach_traverser=reach_traverser,
            reach_opponent=reach_opponent,
            legal_actions=legal_actions,
            node=node,
            strategy=strategy,
        )

    def _traverser_node(
        self,
        state,
        traverser,
        reach_traverser,
        reach_opponent,
        legal_actions,
        node,
        strategy,
    ):
        """
        At traverser nodes, explore all legal actions and update regrets.
        """
        action_values = {}
        node_value = 0.0

        for action in legal_actions:
            idx = ACTION_INDEX[action]

            next_state = state.clone()
            next_state.apply_action(action)

            action_value = self.external_sampling_cfr(
                state=next_state,
                traverser=traverser,
                reach_traverser=reach_traverser * strategy[idx],
                reach_opponent=reach_opponent,
            )

            action_values[action] = action_value
            node_value += strategy[idx] * action_value

        for action in legal_actions:
            idx = ACTION_INDEX[action]
            regret = action_values[action] - node_value

            node.regret_sum[idx] += reach_opponent * regret
            node.strategy_sum[idx] += reach_traverser * strategy[idx]

        return node_value

    def _opponent_node(
        self,
        state,
        traverser,
        reach_traverser,
        reach_opponent,
        legal_actions,
        node,
        strategy,
    ):
        """
        At opponent nodes, sample one action from the current strategy.
        """
        sampled_action = self.sample_action(strategy, legal_actions)
        sampled_idx = ACTION_INDEX[sampled_action]

        for action in legal_actions:
            idx = ACTION_INDEX[action]
            node.strategy_sum[idx] += reach_opponent * strategy[idx]

        next_state = state.clone()
        next_state.apply_action(sampled_action)

        return self.external_sampling_cfr(
            state=next_state,
            traverser=traverser,
            reach_traverser=reach_traverser,
            reach_opponent=reach_opponent * strategy[sampled_idx],
        )

    def sample_action(self, strategy, legal_actions):
        if not legal_actions:
            raise ValueError("Cannot sample from empty legal_actions")

        r = self.rng.random()
        cumulative = 0.0

        for action in legal_actions:
            idx = ACTION_INDEX[action]
            cumulative += strategy[idx]

            if r <= cumulative:
                return action

        return legal_actions[-1]

    def train(
        self,
        iterations: int,
        path=None,
        load_checkpoint: bool = False,
        save_every: int | None = 1000,
        print_every: int | None = 100,
        update_both_players: bool = True,
    ):
        if load_checkpoint:
            self.load_checkpoint(path)

        utility_sum = 0.0
        utility_window = 0.0
        traversals = 0

        for iteration in range(1, iterations + 1):
            if update_both_players:
                traversers = [0, 1]
            else:
                traversers = [iteration % 2]

            for traverser in traversers:
                env = self.env_factory()
                env.reset()
                state = env.state

                utility = self.external_sampling_cfr(
                    state=state,
                    traverser=traverser,
                    reach_traverser=1.0,
                    reach_opponent=1.0,
                )

                utility_sum += utility
                utility_window += utility
                traversals += 1

            self.iterations_trained += 1

            if print_every is not None and iteration % print_every == 0:
                avg_total = utility_sum / max(traversals, 1)
                avg_window = utility_window / max(
                    print_every * len(traversers),
                    1,
                )

                print(
                    f"Iteration {self.iterations_trained} | "
                    f"infosets: {len(self.nodes)} | "
                    f"avg utility total: {avg_total:.4f} | "
                    f"avg utility window: {avg_window:.4f}"
                )

                utility_window = 0.0

            if path is not None and save_every is not None:
                if iteration % save_every == 0:
                    self.save_checkpoint(path)

        if path is not None:
            self.save_checkpoint(path)

    def average_strategy(self):
        strategy = {}

        for info_key, node in self.nodes.items():
            strategy[info_key] = node.average_strategy(node.legal_actions)

        return strategy

    def print_some_strategies(self, limit=20):
        count = 0

        for key, node in self.nodes.items():
            print(key)
            print("  regrets:", node.regret_sum)
            print("  strategy_sum:", node.strategy_sum)

            count += 1
            if count >= limit:
                break

    def print_strategies(self, limit=30):
        count = 0

        for key, node in self.nodes.items():
            avg = node.average_strategy(node.legal_actions)

            print(key)

            for action in node.legal_actions:
                idx = ACTION_INDEX[action]
                print(f"  {action.name}: {avg[idx]:.3f}")

            count += 1
            if count >= limit:
                break

    def save_checkpoint(self, path):
        data = {
            "nodes": self.nodes,
            "iterations_trained": self.iterations_trained,
            "infoset_builder_name": self.infoset_builder.name,
            "game": "LiteHoldem",
            "trainer_type": "ExternalSamplingMCCFR",
            "trainer_version": "mccfr_v1",
            "key_version": "equity_bucket_v1",
            "bet_sizes": [2, 4],
            "max_raises": 2,
        }

        with open(path, "wb") as f:
            pickle.dump(data, f)

    def load_checkpoint(self, path):
        with open(path, "rb") as f:
            data = pickle.load(f)

        checkpoint_builder_name = data.get("infoset_builder_name")

        if checkpoint_builder_name != self.infoset_builder.name:
            raise ValueError(
                f"Checkpoint was trained with {checkpoint_builder_name}, "
                f"but trainer is using {self.infoset_builder.name}"
            )

        self.nodes = data["nodes"]
        self.iterations_trained = data["iterations_trained"]