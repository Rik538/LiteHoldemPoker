# -*- coding: utf-8 -*-
"""
Created on Sun Jun  7 16:04:41 2026

@author: Richard
"""

import pytest

from lite_holdem_ai.cfr.infoset import EquityBucketInfosetKeyBuilder
from lite_holdem_ai.cfr.mccfr_trainer import MCCFRTrainer
from lite_holdem_ai.cfr.node import ACTION_INDEX
from lite_holdem_ai.game.actions import Action
from lite_holdem_ai.game.environment import LiteHoldemEnv


class ConstantBucketProvider:
    def __init__(self, bucket=2):
        self.bucket = bucket

    def get_bucket(self, private_cards, public_cards):
        return self.bucket


def make_trainer(bucket=2, seed=1):
    bucket_provider = ConstantBucketProvider(bucket=bucket)
    infoset_builder = EquityBucketInfosetKeyBuilder(bucket_provider)

    return MCCFRTrainer(
        infoset_builder=infoset_builder,
        env_factory=lambda: LiteHoldemEnv(),
        seed=seed,
    )


def test_mccfr_trainer_can_be_constructed():
    trainer = make_trainer()

    assert trainer is not None
    assert trainer.nodes == {}
    assert trainer.iterations_trained == 0
    assert trainer.infoset_builder.name == "equity_bucket_v1"


def test_mccfr_trainer_get_node_creates_node():
    trainer = make_trainer()

    key = ("test",)
    legal_actions = [Action.CHECK_CALL, Action.BET_RAISE]

    node = trainer.get_node(key, legal_actions)

    assert key in trainer.nodes
    assert trainer.nodes[key] is node
    assert node.legal_actions == legal_actions


def test_mccfr_trainer_get_node_reuses_existing_node():
    trainer = make_trainer()

    key = ("test",)
    legal_actions = [Action.CHECK_CALL, Action.BET_RAISE]

    node_a = trainer.get_node(key, legal_actions)
    node_b = trainer.get_node(key, legal_actions)

    assert node_a is node_b
    assert len(trainer.nodes) == 1


def test_mccfr_sample_action_is_seeded():
    legal_actions = [Action.CHECK_CALL, Action.BET_RAISE]

    strategy = [0.0, 0.5, 0.5]

    trainer_a = make_trainer(seed=123)
    trainer_b = make_trainer(seed=123)

    actions_a = [
        trainer_a.sample_action(strategy, legal_actions)
        for _ in range(20)
    ]

    actions_b = [
        trainer_b.sample_action(strategy, legal_actions)
        for _ in range(20)
    ]

    assert actions_a == actions_b


def test_mccfr_sample_action_rejects_empty_actions():
    trainer = make_trainer()

    with pytest.raises(ValueError):
        trainer.sample_action([0.0, 0.5, 0.5], [])


def test_mccfr_external_sampling_cfr_direct_call():
    trainer = make_trainer(seed=1)

    env = LiteHoldemEnv()
    env.reset()

    value = trainer.external_sampling_cfr(
        state=env.state,
        traverser=0,
        reach_traverser=1.0,
        reach_opponent=1.0,
    )

    assert isinstance(value, float)
    assert len(trainer.nodes) > 0


def test_mccfr_trainer_can_run_one_iteration_update_both_players():
    trainer = make_trainer(seed=1)

    trainer.train(
        iterations=1,
        print_every=None,
        save_every=None,
        update_both_players=True,
    )

    assert trainer.iterations_trained == 1
    assert len(trainer.nodes) > 0


def test_mccfr_trainer_can_run_one_iteration_single_player_update():
    trainer = make_trainer(seed=1)

    trainer.train(
        iterations=1,
        print_every=None,
        save_every=None,
        update_both_players=False,
    )

    assert trainer.iterations_trained == 1
    assert len(trainer.nodes) > 0


def test_mccfr_trainer_average_strategy_after_training():
    trainer = make_trainer(seed=1)

    trainer.train(
        iterations=2,
        print_every=None,
        save_every=None,
        update_both_players=True,
    )

    avg_strategy = trainer.average_strategy()

    assert isinstance(avg_strategy, dict)
    assert len(avg_strategy) == len(trainer.nodes)

    for info_key, strategy in avg_strategy.items():
        assert info_key in trainer.nodes
        assert len(strategy) == 3

        node = trainer.nodes[info_key]

        legal_probability_sum = 0.0

        for action in node.legal_actions:
            legal_probability_sum += strategy[ACTION_INDEX[action]]

        assert legal_probability_sum == pytest.approx(1.0)


def test_mccfr_checkpoint_round_trip(tmp_path):
    trainer = make_trainer(seed=1)

    trainer.train(
        iterations=2,
        print_every=None,
        save_every=None,
        update_both_players=True,
    )

    path = tmp_path / "mccfr_checkpoint.pkl"
    trainer.save_checkpoint(path)

    loaded = make_trainer(seed=2)
    loaded.load_checkpoint(path)

    assert loaded.iterations_trained == trainer.iterations_trained
    assert len(loaded.nodes) == len(trainer.nodes)
    assert loaded.average_strategy().keys() == trainer.average_strategy().keys()


def test_mccfr_rejects_checkpoint_with_wrong_infoset_builder(tmp_path):
    trainer = make_trainer(seed=1)

    trainer.train(
        iterations=1,
        print_every=None,
        save_every=None,
        update_both_players=True,
    )

    path = tmp_path / "mccfr_checkpoint.pkl"
    trainer.save_checkpoint(path)

    class OtherInfosetBuilder:
        name = "different_infoset"

        def from_state(self, state, player):
            return ("other",)

        def from_observation(self, observation):
            return ("other",)

    loaded = MCCFRTrainer(
        infoset_builder=OtherInfosetBuilder(),
        env_factory=lambda: LiteHoldemEnv(),
        seed=1,
    )

    with pytest.raises(ValueError):
        loaded.load_checkpoint(path)


def test_mccfr_terminal_state_returns_traverser_payoff():
    trainer = make_trainer(seed=1)

    env = LiteHoldemEnv()
    env.reset()
    state = env.state

    if Action.BET_RAISE in state.legal_actions():
        state.apply_action(Action.BET_RAISE)

    if Action.FOLD in state.legal_actions():
        state.apply_action(Action.FOLD)

    if not state.terminal:
        pytest.skip("Could not create terminal state through simple bet/fold sequence")

    value_p0 = trainer.external_sampling_cfr(
        state=state,
        traverser=0,
        reach_traverser=1.0,
        reach_opponent=1.0,
    )

    value_p1 = trainer.external_sampling_cfr(
        state=state,
        traverser=1,
        reach_traverser=1.0,
        reach_opponent=1.0,
    )

    assert value_p0 == state.payoffs[0]
    assert value_p1 == state.payoffs[1]
    assert value_p0 == -value_p1