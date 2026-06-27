# -*- coding: utf-8 -*-
"""
CFR trainer for Lite Hold'em.
"""



from lite_holdem_ai.cfr.base_cfr_trainer import BaseCFRTrainer, ACTION_INDEX


class CFRTrainer(BaseCFRTrainer):
    trainer_type = "CFR"
    trainer_version = "cfr_v1"
    
    def __init__(self, infoset_builder, env_factory):
        self.infoset_builder = infoset_builder
        self.env_factory = env_factory
        self.nodes = {}
        self.iterations_trained = 0

    def cfr(self, state, env,reach0, reach1):
        if state.terminal:
            return state.payoffs[0]

        player = state.current_player
        legal_actions = env.legal_actions(state)

        if not legal_actions:
            raise RuntimeError("Non-terminal CFR state has no legal actions")

        info_key = self.infoset_builder.from_observation(
            env.observe(player, state)
        )
        node = self.get_node(info_key, legal_actions)

        strategy = node.get_strategy(
            legal_actions,
            accumulate_strategy=False,
        )

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

    