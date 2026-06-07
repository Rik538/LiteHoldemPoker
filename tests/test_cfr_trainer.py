# -*- coding: utf-8 -*-
"""
Created on Sun Jun  7 12:43:07 2026

@author: Richard
"""

import pytest

from lite_holdem_ai.cfr.infoset import EquityBucketInfosetKeyBuilder
from lite_holdem_ai.cfr.trainer import CFRTrainer
from lite_holdem_ai.game.environment import LiteHoldemEnv


class ConstantBucketProvider:
    def __init__(self, bucket=2):
        self.bucket = bucket

    def get_bucket(self, private_cards, public_cards):
        return self.bucket


def make_trainer(bucket=2):
    bucket_provider = ConstantBucketProvider(bucket=bucket)
    infoset_builder = EquityBucketInfosetKeyBuilder(bucket_provider)

    return CFRTrainer(
        infoset_builder=infoset_builder,
        env_factory=lambda: LiteHoldemEnv(),
    )


def test_cfr_trainer_can_be_constructed():
    trainer = make_trainer()

    assert trainer is not None
    assert trainer.nodes == {}
    assert trainer.iterations_trained == 0
    assert trainer.infoset_builder.name == "equity_bucket_v1"


def test_cfr_trainer_get_node_creates_node():
    from lite_holdem_ai.game.actions import Action

    trainer = make_trainer()

    key = ("test",)
    legal_actions = [Action.CHECK_CALL, Action.BET_RAISE]

    node = trainer.get_node(key, legal_actions)

    assert key in trainer.nodes
    assert trainer.nodes[key] is node
    assert node.legal_actions == legal_actions


def test_cfr_trainer_get_node_reuses_existing_node():
    from lite_holdem_ai.game.actions import Action

    trainer = make_trainer()

    key = ("test",)
    legal_actions = [Action.CHECK_CALL, Action.BET_RAISE]

    node_a = trainer.get_node(key, legal_actions)
    node_b = trainer.get_node(key, legal_actions)

    assert node_a is node_b
    assert len(trainer.nodes) == 1


def test_cfr_trainer_can_run_one_iteration():
    trainer = make_trainer()

    trainer.train(iterations=1)

    assert trainer.iterations_trained == 1
    assert len(trainer.nodes) > 0


def test_cfr_trainer_average_strategy_after_training():
    trainer = make_trainer()

    trainer.train(iterations=1)

    avg_strategy = trainer.average_strategy()

    assert isinstance(avg_strategy, dict)
    assert len(avg_strategy) == len(trainer.nodes)

    for info_key, strategy in avg_strategy.items():
        assert info_key in trainer.nodes
        assert len(strategy) == 3

        node = trainer.nodes[info_key]
        legal_probability_sum = 0.0

        for action in node.legal_actions:
            from lite_holdem_ai.cfr.node import ACTION_INDEX

            legal_probability_sum += strategy[ACTION_INDEX[action]]

        assert legal_probability_sum == pytest.approx(1.0)


def test_cfr_trainer_checkpoint_round_trip(tmp_path):
    trainer = make_trainer()

    trainer.train(iterations=1)

    path = tmp_path / "cfr_checkpoint.pkl"
    trainer.save_checkpoint(path)

    loaded = make_trainer()
    loaded.load_checkpoint(path)

    assert loaded.iterations_trained == trainer.iterations_trained
    assert len(loaded.nodes) == len(trainer.nodes)
    assert loaded.average_strategy().keys() == trainer.average_strategy().keys()


def test_cfr_trainer_rejects_checkpoint_with_wrong_infoset_builder(tmp_path):
    trainer = make_trainer()

    trainer.train(iterations=1)

    path = tmp_path / "cfr_checkpoint.pkl"
    trainer.save_checkpoint(path)

    class OtherInfosetBuilder:
        name = "different_infoset"

        def from_state(self, state, player):
            return ("other",)

        def from_observation(self, observation):
            return ("other",)

    loaded = CFRTrainer(
        infoset_builder=OtherInfosetBuilder(),
        env_factory=lambda: LiteHoldemEnv(),
    )

    with pytest.raises(ValueError):
        loaded.load_checkpoint(path)


def test_cfr_terminal_state_returns_player_zero_payoff():
    trainer = make_trainer()

    env = LiteHoldemEnv()
    env.reset()

    state = env.state

    # Force a terminal fold state through legal actions.
    if state.terminal:
        pytest.skip("State unexpectedly terminal after reset")

    legal_actions = state.legal_actions()

    if len(legal_actions) == 0:
        pytest.skip("No legal actions after reset")

    # Create a terminal state by betting then folding where possible.
    if not state.terminal:
        from lite_holdem_ai.game.actions import Action

        if Action.BET_RAISE in state.legal_actions():
            state.apply_action(Action.BET_RAISE)

        if Action.FOLD in state.legal_actions():
            state.apply_action(Action.FOLD)

    if not state.terminal:
        pytest.skip("Could not create terminal state through simple bet/fold sequence")

    value = trainer.cfr(state, 1.0, 1.0)

    assert value == state.payoffs[0]
    assert sum(state.payoffs) == 0