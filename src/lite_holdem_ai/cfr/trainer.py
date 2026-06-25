# -*- coding: utf-8 -*-
"""
CFR trainer for Lite Hold'em.
"""

import pickle

from lite_holdem_ai.cfr.node import ACTION_INDEX, CFRNode


class CFRTrainer:
    def __init__(self, infoset_builder, env_factory):
        self.infoset_builder = infoset_builder
        self.env_factory = env_factory
        self.nodes = {}
        self.iterations_trained = 0

    def get_node(self, info_set_key, legal_actions):
        if info_set_key not in self.nodes:
            node = CFRNode()
            node.legal_actions = legal_actions.copy()
            self.nodes[info_set_key] = node

        return self.nodes[info_set_key]

    def cfr(self, state, env,reach0, reach1):
        if state.terminal:
            return state.payoffs[0]

        player = state.current_player
        legal_actions = env.legal_actions(state)

        if not legal_actions:
            raise RuntimeError("Non-terminal CFR state has no legal actions")

        info_key = self.infoset_builder.from_state(state, player)
        node = self.get_node(info_key, legal_actions)

        strategy = node.get_strategy(legal_actions)

        action_values = {}
        node_value = 0.0

        for action in legal_actions:
            idx = ACTION_INDEX[action]

            next_state = env.next_state(state,action)

            if player == 0:
                action_value = self.cfr(
                    next_state,
                    env,
                    reach0 * strategy[idx],
                    reach1,
                )
            else:
                action_value = self.cfr(
                    next_state,
                    env,
                    reach0,
                    reach1 * strategy[idx],
                )

            action_values[action] = action_value
            node_value += strategy[idx] * action_value

        for action in legal_actions:
            idx = ACTION_INDEX[action]

            if player == 0:
                regret = action_values[action] - node_value
                node.regret_sum[idx] += reach1 * regret
                node.strategy_sum[idx] += reach0 * strategy[idx]
            else:
                regret = node_value - action_values[action]
                node.regret_sum[idx] += reach0 * regret
                node.strategy_sum[idx] += reach1 * strategy[idx]

        return node_value

    def train(self, iterations, path=None, load_checkpoint=False):
        if load_checkpoint:
            self.load_checkpoint(path)

        for iteration in range(1, iterations + 1):
            env = self.env_factory()
            env.reset()
            state = env.state

            utility = self.cfr(state,env, 1.0, 1.0)

            self.iterations_trained += 1

            if iteration % 100 == 0:
                print(
                    f"Iteration {self.iterations_trained} | "
                    f"infosets: {len(self.nodes)} | "
                    f"utility: {utility:.4f}"
                )

            if path and iteration % 10 == 0:
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
            "trainer_version": "cfr_v1",
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