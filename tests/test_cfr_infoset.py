# -*- coding: utf-8 -*-
"""
Created on Sat Jun  6 23:04:13 2026

@author: Richard
"""

from lite_holdem_ai.cfr.infoset import (
    CachedEquityBucketProvider,
    EquityBucketInfosetKeyBuilder,
)
from lite_holdem_ai.equity.cache import EquityCache
from lite_holdem_ai.game.environment import LiteHoldemEnv


def add_cache_entry(cache, private_cards, public_cards, bucket=3):
    result = {
        "wins": 1,
        "losses": 1,
        "splits": 0,
        "total": 2,
        "equity": 0.5,
    }

    cache.set(
        private_cards=private_cards,
        public_cards=public_cards,
        result=result,
        bucket=bucket,
    )


def test_infoset_key_from_state_matches_observation(tmp_path):
    cache_path = tmp_path / "equity_cache.sqlite"

    env = LiteHoldemEnv()
    observation = env.reset()
    state = env.state
    player = env.current_player

    private_cards = state.player_cards[player]
    public_cards = state.public_cards

    with EquityCache(cache_path) as cache:
        add_cache_entry(cache, private_cards, public_cards, bucket=3)

        bucket_provider = CachedEquityBucketProvider(cache)
        builder = EquityBucketInfosetKeyBuilder(bucket_provider)

        key_from_state = builder.from_state(env, player)
        key_from_observation = builder.from_observation(observation)

        assert key_from_state == key_from_observation