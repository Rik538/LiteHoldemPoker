# -*- coding: utf-8 -*-

import pickle

import pytest

from lite_holdem_ai.cfr.base_cfr_trainer import BaseCFRTrainer
from lite_holdem_ai.cfr.node import CFRNode
from lite_holdem_ai.game.actions import Action


class DummyInfosetBuilder:
    name = "dummy_infoset_v1"


class DummyTrainer(BaseCFRTrainer):
    trainer_type = "DummyCFR"
    trainer_version = "dummy_v1"

    def __init__(self):
        self.nodes = {}
        self.iterations_trained = 0
        self.infoset_builder = DummyInfosetBuilder()


def make_checkpoint_data(trainer, **overrides):
    data = {
        "nodes": {},
        "iterations_trained": 123,
        "infoset_builder_name": trainer.infoset_builder.name,
        "game": "LiteHoldem",
        "trainer_type": trainer.trainer_type,
        "trainer_version": trainer.trainer_version,
        "bet_sizes": [2, 4],
        "max_raises": 2,
    }

    data.update(overrides)
    return data


def write_checkpoint(path, data):
    with open(path, "wb") as f:
        pickle.dump(data, f)


def test_get_node_creates_node_with_legal_actions():
    trainer = DummyTrainer()
    key = ("P0", "test")

    node = trainer.get_node(
        key,
        [Action.CHECK_CALL, Action.BET_RAISE],
    )

    assert isinstance(node, CFRNode)
    assert key in trainer.nodes
    assert node.legal_actions == [Action.CHECK_CALL, Action.BET_RAISE]


def test_get_node_returns_existing_node_for_same_infoset_and_same_legal_actions():
    trainer = DummyTrainer()
    key = ("P0", "test")

    first = trainer.get_node(
        key,
        [Action.CHECK_CALL, Action.BET_RAISE],
    )
    second = trainer.get_node(
        key,
        [Action.CHECK_CALL, Action.BET_RAISE],
    )

    assert first is second


def test_get_node_allows_same_legal_action_set_in_different_order():
    trainer = DummyTrainer()
    key = ("P0", "test")

    first = trainer.get_node(
        key,
        [Action.CHECK_CALL, Action.BET_RAISE],
    )
    second = trainer.get_node(
        key,
        [Action.BET_RAISE, Action.CHECK_CALL],
    )

    assert first is second


def test_get_node_rejects_same_infoset_with_different_legal_actions():
    trainer = DummyTrainer()
    key = ("P0", "collision")

    trainer.get_node(
        key,
        [Action.CHECK_CALL, Action.BET_RAISE],
    )

    with pytest.raises(ValueError, match="Inconsistent legal actions"):
        trainer.get_node(
            key,
            [Action.FOLD, Action.CHECK_CALL],
        )


def test_save_and_load_checkpoint_round_trip(tmp_path):
    trainer = DummyTrainer()
    key = ("P0", "round_trip")

    trainer.get_node(
        key,
        [Action.CHECK_CALL, Action.BET_RAISE],
    )
    trainer.iterations_trained = 50

    path = tmp_path / "checkpoint.pkl"
    trainer.save_checkpoint(path)

    loaded = DummyTrainer()
    loaded.load_checkpoint(path)

    assert loaded.iterations_trained == 50
    assert key in loaded.nodes
    assert loaded.nodes[key].legal_actions == [
        Action.CHECK_CALL,
        Action.BET_RAISE,
    ]


@pytest.mark.parametrize(
    "field,bad_value",
    [
        ("game", "OtherGame"),
        ("bet_sizes", [1, 2]),
        ("max_raises", 99),
    ],
)
def test_load_checkpoint_rejects_incompatible_metadata(tmp_path, field, bad_value):
    trainer = DummyTrainer()
    path = tmp_path / "bad_checkpoint.pkl"

    data = make_checkpoint_data(
        trainer,
        **{field: bad_value},
    )
    write_checkpoint(path, data)

    with pytest.raises(ValueError, match=f"Incompatible checkpoint field {field}"):
        trainer.load_checkpoint(path)


@pytest.mark.parametrize(
    "missing_field",
    [
        "game",
        "bet_sizes",
        "max_raises",
    ],
)
def test_load_checkpoint_rejects_missing_required_metadata(tmp_path, missing_field):
    trainer = DummyTrainer()
    path = tmp_path / "missing_metadata_checkpoint.pkl"

    data = make_checkpoint_data(trainer)
    del data[missing_field]
    write_checkpoint(path, data)

    with pytest.raises(
        ValueError,
        match=f"Incompatible checkpoint field {missing_field}",
    ):
        trainer.load_checkpoint(path)


def test_load_checkpoint_rejects_wrong_infoset_builder(tmp_path):
    trainer = DummyTrainer()
    path = tmp_path / "wrong_builder_checkpoint.pkl"

    data = make_checkpoint_data(
        trainer,
        infoset_builder_name="different_builder_v1",
    )
    write_checkpoint(path, data)

    with pytest.raises(ValueError, match="Checkpoint was trained with"):
        trainer.load_checkpoint(path)