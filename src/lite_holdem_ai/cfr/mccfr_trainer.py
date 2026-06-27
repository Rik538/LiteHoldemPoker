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


import random


from lite_holdem_ai.cfr.base_cfr_trainer import BaseCFRTrainer, ACTION_INDEX


class MCCFRTrainer(BaseCFRTrainer):
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
    
    def sample_action(self, legal_actions, strategy):
        if not legal_actions:
            raise ValueError("Cannot sample action from empty legal_actions")
    
        roll = self.rng.random()
        cumulative = 0.0
    
        for action in legal_actions:
            idx = ACTION_INDEX[action]
            cumulative += strategy[idx]
    
            if roll <= cumulative:
                return action
    
        # Fallback for floating point rounding
        return legal_actions[-1]

    def external_sampling_cfr(
        self,
        state,
        env,
        traverser: int,
        reach_traverser: float,
        reach_opponent: float,
        average_strategy: bool = True,
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
        legal_actions = env.legal_actions(state)

        if not legal_actions:
            raise RuntimeError("Non-terminal MCCFR state has no legal actions")

        info_key = self.infoset_builder.from_state(env, player)
        node = self.get_node(info_key, legal_actions)

        strategy = node.get_strategy(legal_actions,average_strategy)

        if player == traverser:
            strategy = node.get_strategy(
                legal_actions=legal_actions,
                reach_probability=reach_traverser,
                accumulate_strategy=average_strategy,
            )
    
            return self._traverser_node(
                state=state,
                env=env,
                traverser=traverser,
                reach_traverser=reach_traverser,
                reach_opponent=reach_opponent,
                legal_actions=legal_actions,
                node=node,
                strategy=strategy,
                average_strategy=average_strategy,
            )
    
        strategy = node.get_strategy(
            legal_actions=legal_actions,
            reach_probability=reach_opponent,
            accumulate_strategy=average_strategy,
        )
    
        return self._opponent_node(
            state=state,
            env=env,
            traverser=traverser,
            reach_traverser=reach_traverser,
            reach_opponent=reach_opponent,
            legal_actions=legal_actions,
            node=node,
            strategy=strategy,
            average_strategy=average_strategy,
        )

    def _traverser_node(
        self,
        state,
        env,
        traverser,
        reach_traverser,
        reach_opponent,
        legal_actions,
        node,
        strategy,
        average_strategy,
    ):
        """
        At traverser nodes, explore all legal actions and update regrets.
        """
        action_values = {}
        node_value = 0.0
    
        for action in legal_actions:
            idx = ACTION_INDEX[action]
    
            next_state = env.next_state(state,action)
    
            action_value = self.external_sampling_cfr(
                state=next_state,
                env=env,
                traverser=traverser,
                reach_traverser=reach_traverser * strategy[idx],
                reach_opponent=reach_opponent,
                average_strategy=average_strategy,
            )
    
            action_values[action] = action_value
            node_value += strategy[idx] * action_value
    
        for action in legal_actions:
            idx = ACTION_INDEX[action]
            regret = action_values[action] - node_value
            node.regret_sum[idx] += reach_opponent * regret

        return node_value

    def _opponent_node(
        self,
        state,
        env,
        traverser,
        reach_traverser,
        reach_opponent,
        legal_actions,
        node,
        strategy,
        average_strategy,
    ):
        """
        At opponent nodes, sample one action from the current strategy.
        """
        sampled_action = self.sample_action(legal_actions,strategy)
        sampled_idx = ACTION_INDEX[sampled_action]
    
        next_state = env.next_state(state,sampled_action)
    
        return self.external_sampling_cfr(
            state=next_state,
            env=env,
            traverser=traverser,
            reach_traverser=reach_traverser,
            reach_opponent=reach_opponent * strategy[sampled_idx],
            average_strategy=average_strategy,
        )

    def train(
        self,
        iterations: int,
        path=None,
        load_checkpoint: bool = False,
        save_every: int | None = 1000,
        print_every: int | None = 100,
        update_both_players: bool = True,
        averaging_start_iteration: int = 0,
    ):
        if load_checkpoint:
            self.load_checkpoint(path)

        utility_sum = 0.0
        utility_window = 0.0
        traversals = 0
       

        for iteration in range(1, iterations + 1):
            env = self.env_factory()
            env.reset()
            initial_state = env.state
            
            average_strategy = iteration >= averaging_start_iteration
        
            if update_both_players:
                traversers = [0, 1]
            else:
                traversers = [iteration % 2]
        
            for traverser in traversers:
                state = initial_state.clone()
        
                utility = self.external_sampling_cfr(
                    state=state,
                    env=env,
                    traverser=traverser,
                    reach_traverser=1.0,
                    reach_opponent=1.0,
                    average_strategy= average_strategy
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

   