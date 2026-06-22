# -*- coding: utf-8 -*-
"""
Combine compatible MCCFR checkpoints by averaging strategy sums.
"""

import pickle
from copy import deepcopy


from lite_holdem_ai.cfr.node import CFRNode, NUM_ACTIONS


class CombineMCCFRStrategies():
    
    def load_checkpoint(self,path):
        with open(path, "rb") as f:
            return pickle.load(f)
    
    
    def save_checkpoint(self,data, path):
        with open(path, "wb") as f:
            pickle.dump(data, f)
    
    
    def assert_compatible(self,base_data, other_data):
        fields = [
            "infoset_builder_name",
            "game",
            "trainer_type",
            "bet_sizes",
            "max_raises",
        ]
    
        for field in fields:
            if base_data.get(field) != other_data.get(field):
                raise ValueError(
                    f"Incompatible checkpoints for field {field}: "
                    f"{base_data.get(field)} != {other_data.get(field)}"
                )
    
    
    def combine_nodes(self,checkpoint_datas):
        combined_nodes = {}
    
        for data in checkpoint_datas:
            for info_key, node in data["nodes"].items():
                if info_key not in combined_nodes:
                    new_node = CFRNode()
                    new_node.legal_actions = node.legal_actions.copy()
                    combined_nodes[info_key] = new_node
    
                combined_node = combined_nodes[info_key]
    
                for idx in range(NUM_ACTIONS):
                    combined_node.strategy_sum[idx] += node.strategy_sum[idx]
                    combined_node.regret_sum[idx] += node.regret_sum[idx]
    
        return combined_nodes
    
    
    def average_checkpoints(self,input_paths, output_path):
        if not input_paths:
            raise ValueError("No input checkpoints provided")
    
        checkpoint_datas = [self.load_checkpoint(path) for path in input_paths]
    
        base_data = deepcopy(checkpoint_datas[0])
    
        for data in checkpoint_datas[1:]:
            self.assert_compatible(base_data, data)
    
        combined_data = deepcopy(base_data)
        combined_data["nodes"] = self.combine_nodes(checkpoint_datas)
        combined_data["iterations_trained"] = sum(
            data.get("iterations_trained", 0)
            for data in checkpoint_datas
        )
        combined_data["trainer_type"] = base_data.get("trainer_type")
        combined_data["trainer_version"] = (
            base_data.get("trainer_version", "") + "_seed_averaged"
        )
        combined_data["averaged_from"] = [str(path) for path in input_paths]
    
        self.save_checkpoint(combined_data, output_path)
    
        return output_path


