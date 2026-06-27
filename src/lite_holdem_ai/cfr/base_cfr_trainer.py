# -*- coding: utf-8 -*-
"""
Created on Sat Jun 27 13:20:01 2026

@author: Richard
"""

from lite_holdem_ai.cfr.node import ACTION_INDEX, CFRNode
import pickle

class BaseCFRTrainer():
    
    def get_node(self, info_set_key, legal_actions):
        if info_set_key not in self.nodes:
            node = CFRNode()
            node.legal_actions = legal_actions.copy()
            self.nodes[info_set_key] = node

        return self.nodes[info_set_key]
    
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