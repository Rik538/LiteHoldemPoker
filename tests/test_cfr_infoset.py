# -*- coding: utf-8 -*-
"""
Created on Sat Jun  6 23:04:13 2026

@author: Richard
"""

from lite_holdem_ai.cfr.infoset import (
    CachedEquityBucketProvider,
    EquityBucketInfosetKeyBuilder,
    MemoizedBucketProvider,
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


def test_memoized_provider_matches_cached_provider_interface():
    class FakeProvider:
        def get_bucket(self, private_cards, public_cards):
            return 3

        def get_equity(self, private_cards, public_cards):
            return 0.72

    provider = MemoizedBucketProvider(FakeProvider())

    assert provider.get_bucket([1, 2], [3, 4, 5]) == 3
    assert provider.get_equity([1, 2], [3, 4, 5]) == 0.72
    
    
def test_memoized_bucket_provider_keeps_equity_and_bucket_caches_separate_reverse_order():
    class FakeProvider:
        def get_bucket(self, private_cards, public_cards):
            return 3

        def get_equity(self, private_cards, public_cards):
            return 0.72

    provider = MemoizedBucketProvider(FakeProvider())

    private_cards = [1, 2]
    public_cards = [3, 4, 5]


    equity = provider.get_equity(private_cards, public_cards)
    bucket = provider.get_bucket(private_cards, public_cards)

    assert equity == 0.72
    assert bucket == 3