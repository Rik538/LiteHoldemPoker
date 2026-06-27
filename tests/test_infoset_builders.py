# -*- coding: utf-8 -*-

import pytest

from lite_holdem_ai.cfr.infoset import (
    EquityBucketInfosetKeyBuilder,
    EquityPotBucketInfosetKeyBuilder,
    MemoizedBucketProvider,
    StreetAwarePotBucket7InfosetKeyBuilder,
    StreetAwarePotBucketNoHistoryInfosetKeyBuilder,
    StreetSpecificEquityBucketInfosetKeyBuilder,
    StreetSpecificEquityPotBucketInfosetKeyBuilder,
)
from lite_holdem_ai.game.actions import Action


DEFAULT_STREET_THRESHOLDS = {
    0: [0.35, 0.45, 0.55, 0.65],
    1: [0.25, 0.40, 0.55, 0.70],
    2: [0.20, 0.35, 0.55, 0.75],
    3: [0.10, 0.30, 0.50, 0.75],
}


SEVEN_BUCKET_STREET_THRESHOLDS = {
    0: [0.30, 0.38, 0.46, 0.54, 0.62, 0.70],
    1: [0.18, 0.30, 0.42, 0.55, 0.68, 0.80],
    2: [0.12, 0.25, 0.40, 0.55, 0.72, 0.85],
    3: [0.05, 0.20, 0.35, 0.50, 0.70, 0.88],
}

class FakeBucketProvider:
    def __init__(self, bucket=2, equity=0.64):
        self.bucket = bucket
        self.equity = equity
        self.bucket_calls = 0
        self.equity_calls = 0

    def get_bucket(self, private_cards, public_cards):
        self.bucket_calls += 1
        return self.bucket

    def get_equity(self, private_cards, public_cards):
        self.equity_calls += 1
        return self.equity


def make_observation(**overrides):
    observation = {
        "player": 0,
        "private_cards": [1, 2],
        "public_cards": [3, 4, 5],
        "street": 1,
        "pot": 10,
        "button_player": 0,
        "amount_to_call": 2,
        "raises_this_round": 1,
        "actions_this_round": [
            Action.BET_RAISE,
            Action.CHECK_CALL,
        ],
        "action_history": [
            (0, 1, Action.BET_RAISE, 0),
            (1, 1, Action.CHECK_CALL, 2),
        ],
    }

    observation.update(overrides)
    return observation


def test_equity_bucket_builder_name_is_stable():
    builder = EquityBucketInfosetKeyBuilder(FakeBucketProvider())

    assert builder.name == "equity_bucket_v1"


def test_equity_bucket_builder_key_shape_is_stable():
    provider = FakeBucketProvider(bucket=2)
    builder = EquityBucketInfosetKeyBuilder(provider)

    key = builder.from_observation(make_observation())

    assert key == (
        0,                          # player
        1,                          # street
        2,                          # equity bucket
        1,                          # position: player is button
        True,                       # facing bet
        1,                          # raises this round
        "BET_RAISE-CHECK_CALL",     # street history
    )

    assert provider.bucket_calls == 1
    assert provider.equity_calls == 0


def test_equity_bucket_builder_position_for_non_button_player():
    provider = FakeBucketProvider(bucket=2)
    builder = EquityBucketInfosetKeyBuilder(provider)

    key = builder.from_observation(
        make_observation(
            player=1,
            button_player=0,
        )
    )

    assert key[3] == 0


def test_equity_bucket_builder_facing_bet_false_when_amount_to_call_zero():
    provider = FakeBucketProvider(bucket=2)
    builder = EquityBucketInfosetKeyBuilder(provider)

    key = builder.from_observation(
        make_observation(
            amount_to_call=0,
        )
    )

    assert key[4] is False


def test_encode_street_history_handles_raw_actions():
    builder = EquityBucketInfosetKeyBuilder(FakeBucketProvider())

    history = builder.encode_street_history(
        [
            Action.CHECK_CALL,
            Action.BET_RAISE,
            Action.CHECK_CALL,
        ]
    )

    assert history == "CHECK_CALL-BET_RAISE-CHECK_CALL"


def test_encode_street_history_handles_action_history_tuples():
    builder = EquityBucketInfosetKeyBuilder(FakeBucketProvider())

    history = builder.encode_street_history(
        [
            (0, 1, Action.BET_RAISE, 0),
            (1, 1, Action.CHECK_CALL, 2),
        ]
    )

    assert history == "BET_RAISE-CHECK_CALL"


def test_encode_street_history_returns_empty_string_for_no_actions():
    builder = EquityBucketInfosetKeyBuilder(FakeBucketProvider())

    assert builder.encode_street_history([]) == ""


def test_equity_pot_bucket_builder_name_is_stable():
    builder = EquityPotBucketInfosetKeyBuilder(FakeBucketProvider())

    assert builder.name == "equity_pot_bucket_v1"


@pytest.mark.parametrize(
    "pot, expected_bucket",
    [
        (0, 0),
        (4, 0),
        (5, 1),
        (8, 1),
        (9, 2),
        (16, 2),
        (17, 3),
    ],
)
def test_equity_pot_bucket_boundaries(pot, expected_bucket):
    builder = EquityPotBucketInfosetKeyBuilder(FakeBucketProvider())

    assert builder._pot_bucket(pot) == expected_bucket


def test_equity_pot_bucket_builder_key_shape_is_stable():
    provider = FakeBucketProvider(bucket=2)
    builder = EquityPotBucketInfosetKeyBuilder(provider)

    key = builder.from_observation(make_observation(pot=10))

    assert key == (
        0,                          # player
        1,                          # street
        2,                          # equity bucket
        2,                          # pot bucket: 10 -> bucket 2
        1,                          # position
        True,                       # facing bet
        1,                          # raises this round
        "BET_RAISE-CHECK_CALL",     # street history
    )

    assert provider.bucket_calls == 1
    assert provider.equity_calls == 0


def test_street_specific_equity_pot_bucket_builder_name_is_stable():
    builder = StreetSpecificEquityPotBucketInfosetKeyBuilder(FakeBucketProvider())

    assert builder.name == "street_pot_bucket_v1"


@pytest.mark.parametrize(
    "street, equity, expected_bucket",
    [
        # Preflop thresholds: [0.35, 0.45, 0.55, 0.65]
        (0, 0.34, 0),
        (0, 0.35, 1),
        (0, 0.44, 1),
        (0, 0.45, 2),
        (0, 0.54, 2),
        (0, 0.55, 3),
        (0, 0.64, 3),
        (0, 0.65, 4),

        # Flop thresholds: [0.25, 0.40, 0.55, 0.70]
        (1, 0.24, 0),
        (1, 0.25, 1),
        (1, 0.39, 1),
        (1, 0.40, 2),
        (1, 0.54, 2),
        (1, 0.55, 3),
        (1, 0.69, 3),
        (1, 0.70, 4),

        # Turn thresholds: [0.20, 0.35, 0.55, 0.75]
        (2, 0.19, 0),
        (2, 0.20, 1),
        (2, 0.34, 1),
        (2, 0.35, 2),
        (2, 0.54, 2),
        (2, 0.55, 3),
        (2, 0.74, 3),
        (2, 0.75, 4),

        # River thresholds: [0.10, 0.30, 0.50, 0.75]
        (3, 0.09, 0),
        (3, 0.10, 1),
        (3, 0.29, 1),
        (3, 0.30, 2),
        (3, 0.49, 2),
        (3, 0.50, 3),
        (3, 0.74, 3),
        (3, 0.75, 4),
    ],
)
def test_street_specific_equity_pot_bucket_thresholds(
    street,
    equity,
    expected_bucket,
):
    builder = StreetSpecificEquityPotBucketInfosetKeyBuilder(
        FakeBucketProvider(equity=equity)
    )

    assert builder._equity_bucket_for_street(equity, street,DEFAULT_STREET_THRESHOLDS) == expected_bucket


def test_street_specific_equity_pot_bucket_builder_key_shape_is_stable():
    provider = FakeBucketProvider(equity=0.64)
    builder = StreetSpecificEquityPotBucketInfosetKeyBuilder(provider)

    key = builder.from_observation(make_observation(street=1, pot=10))

    assert key == (
        0,                          # player
        1,                          # street
        3,                          # flop street-specific equity bucket
        2,                          # pot bucket
        1,                          # position
        True,                       # facing bet
        1,                          # raises this round
        "BET_RAISE-CHECK_CALL",     # street history
    )

    assert provider.bucket_calls == 0
    assert provider.equity_calls == 1


def test_street_specific_equity_bucket_builder_name_is_stable():
    builder = StreetSpecificEquityBucketInfosetKeyBuilder(FakeBucketProvider())

    assert builder.name == "street_specific_bucket_v1"


def test_street_specific_equity_bucket_builder_key_shape_is_stable():
    provider = FakeBucketProvider(equity=0.64)
    builder = StreetSpecificEquityBucketInfosetKeyBuilder(provider)

    key = builder.from_observation(make_observation(street=1))

    assert key == (
        0,                          # player
        1,                          # street
        3,                          # flop street-specific equity bucket
        1,                          # position
        True,                       # facing bet
        1,                          # raises this round
        "BET_RAISE-CHECK_CALL",     # street history
    )

    assert provider.bucket_calls == 0
    assert provider.equity_calls == 1


def test_street_aware_pot_bucket_no_history_builder_name_is_stable():
    builder = StreetAwarePotBucketNoHistoryInfosetKeyBuilder(FakeBucketProvider())

    assert builder.name == "street_aware_pot_bucket_no_history_v1"


def test_street_aware_pot_bucket_no_history_key_shape_is_stable():
    provider = FakeBucketProvider(equity=0.64)
    builder = StreetAwarePotBucketNoHistoryInfosetKeyBuilder(provider)

    key = builder.from_observation(make_observation(street=1, pot=10))

    assert key == (
        0,      # player
        1,      # street
        3,      # flop street-specific equity bucket
        2,      # pot bucket
        1,      # position
        True,   # facing bet
        1,      # raises this round
    )

    assert provider.bucket_calls == 0
    assert provider.equity_calls == 1


def test_street_aware_pot_bucket_no_history_ignores_street_history():
    provider = FakeBucketProvider(equity=0.64)
    builder = StreetAwarePotBucketNoHistoryInfosetKeyBuilder(provider)

    key_a = builder.from_observation(
        make_observation(
            actions_this_round=[Action.BET_RAISE],
        )
    )
    key_b = builder.from_observation(
        make_observation(
            actions_this_round=[
                Action.CHECK_CALL,
                Action.BET_RAISE,
                Action.CHECK_CALL,
            ],
        )
    )

    assert key_a == key_b


def test_street_aware_pot_bucket_7_builder_name_is_stable():
    builder = StreetAwarePotBucket7InfosetKeyBuilder(FakeBucketProvider())

    assert builder.name == "street_aware_pot_bucket_no_history_7_buckets_v1"


@pytest.mark.parametrize(
    "street, equity, expected_bucket",
    [
        # Preflop thresholds: [0.30, 0.38, 0.46, 0.54, 0.62, 0.70]
        (0, 0.29, 0),
        (0, 0.30, 1),
        (0, 0.37, 1),
        (0, 0.38, 2),
        (0, 0.45, 2),
        (0, 0.46, 3),
        (0, 0.53, 3),
        (0, 0.54, 4),
        (0, 0.61, 4),
        (0, 0.62, 5),
        (0, 0.69, 5),
        (0, 0.70, 6),

        # Flop thresholds: [0.18, 0.30, 0.42, 0.55, 0.68, 0.80]
        (1, 0.17, 0),
        (1, 0.18, 1),
        (1, 0.29, 1),
        (1, 0.30, 2),
        (1, 0.41, 2),
        (1, 0.42, 3),
        (1, 0.54, 3),
        (1, 0.55, 4),
        (1, 0.67, 4),
        (1, 0.68, 5),
        (1, 0.79, 5),
        (1, 0.80, 6),

        # Turn thresholds: [0.12, 0.25, 0.40, 0.55, 0.72, 0.85]
        (2, 0.11, 0),
        (2, 0.12, 1),
        (2, 0.24, 1),
        (2, 0.25, 2),
        (2, 0.39, 2),
        (2, 0.40, 3),
        (2, 0.54, 3),
        (2, 0.55, 4),
        (2, 0.71, 4),
        (2, 0.72, 5),
        (2, 0.84, 5),
        (2, 0.85, 6),

        # River thresholds: [0.05, 0.20, 0.35, 0.50, 0.70, 0.88]
        (3, 0.04, 0),
        (3, 0.05, 1),
        (3, 0.19, 1),
        (3, 0.20, 2),
        (3, 0.34, 2),
        (3, 0.35, 3),
        (3, 0.49, 3),
        (3, 0.50, 4),
        (3, 0.69, 4),
        (3, 0.70, 5),
        (3, 0.87, 5),
        (3, 0.88, 6),
    ],
)
def test_street_aware_pot_bucket_7_thresholds(
    street,
    equity,
    expected_bucket,
):
    builder = StreetAwarePotBucket7InfosetKeyBuilder(
        FakeBucketProvider(equity=equity)
    )

    assert builder._equity_bucket_for_street(equity, street,SEVEN_BUCKET_STREET_THRESHOLDS) == expected_bucket


def test_street_aware_pot_bucket_7_key_shape_is_stable():
    provider = FakeBucketProvider(equity=0.64)
    builder = StreetAwarePotBucket7InfosetKeyBuilder(provider)

    key = builder.from_observation(make_observation(street=1, pot=10))

    assert key == (
        0,      # player
        1,      # street
        4,      # flop 7-bucket street-aware equity bucket
        2,      # pot bucket
        1,      # position
        True,   # facing bet
        1,      # raises this round
    )

    assert provider.bucket_calls == 0
    assert provider.equity_calls == 1


def test_street_aware_pot_bucket_7_ignores_street_history():
    provider = FakeBucketProvider(equity=0.64)
    builder = StreetAwarePotBucket7InfosetKeyBuilder(provider)

    key_a = builder.from_observation(
        make_observation(
            actions_this_round=[Action.BET_RAISE],
        )
    )
    key_b = builder.from_observation(
        make_observation(
            actions_this_round=[
                Action.CHECK_CALL,
                Action.BET_RAISE,
                Action.CHECK_CALL,
            ],
        )
    )

    assert key_a == key_b


def test_memoized_bucket_provider_caches_bucket_calls():
    raw_provider = FakeBucketProvider(bucket=3, equity=0.72)
    provider = MemoizedBucketProvider(raw_provider)

    private_cards = [2, 1]
    public_cards = [5, 4, 3]

    first = provider.get_bucket(private_cards, public_cards)
    second = provider.get_bucket([1, 2], [3, 4, 5])

    assert first == 3
    assert second == 3
    assert raw_provider.bucket_calls == 1
    assert raw_provider.equity_calls == 0


def test_memoized_bucket_provider_caches_equity_calls():
    raw_provider = FakeBucketProvider(bucket=3, equity=0.72)
    provider = MemoizedBucketProvider(raw_provider)

    private_cards = [2, 1]
    public_cards = [5, 4, 3]

    first = provider.get_equity(private_cards, public_cards)
    second = provider.get_equity([1, 2], [3, 4, 5])

    assert first == 0.72
    assert second == 0.72
    assert raw_provider.bucket_calls == 0
    assert raw_provider.equity_calls == 1


def test_memoized_bucket_provider_keeps_bucket_and_equity_caches_separate():
    raw_provider = FakeBucketProvider(bucket=3, equity=0.72)
    provider = MemoizedBucketProvider(raw_provider)

    private_cards = [1, 2]
    public_cards = [3, 4, 5]

    bucket = provider.get_bucket(private_cards, public_cards)
    equity = provider.get_equity(private_cards, public_cards)

    assert bucket == 3
    assert equity == 0.72
    assert raw_provider.bucket_calls == 1
    assert raw_provider.equity_calls == 1


def test_memoized_bucket_provider_keeps_equity_and_bucket_caches_separate_reverse_order():
    raw_provider = FakeBucketProvider(bucket=3, equity=0.72)
    provider = MemoizedBucketProvider(raw_provider)

    private_cards = [1, 2]
    public_cards = [3, 4, 5]

    equity = provider.get_equity(private_cards, public_cards)
    bucket = provider.get_bucket(private_cards, public_cards)

    assert equity == 0.72
    assert bucket == 3
    assert raw_provider.bucket_calls == 1
    assert raw_provider.equity_calls == 1