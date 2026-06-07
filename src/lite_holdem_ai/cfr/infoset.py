# -*- coding: utf-8 -*-
"""
Information-set key builders for Lite Hold'em CFR.

The goal is to keep abstraction logic separate from CFR training and CFR agents,
so different infoset designs can be swapped in easily.
"""

from abc import ABC, abstractmethod


class InfosetKeyBuilder(ABC):
    name = "base"

    @abstractmethod
    def from_state(self, state, player):
        raise NotImplementedError

    @abstractmethod
    def from_observation(self, observation):
        raise NotImplementedError

    def encode_street_history(self, actions_this_round):
        """
        Encodes the current street betting history.

        Expects action entries shaped like:
            (player, street, action, amount_to_call)

        If your action history contains raw Action values, this also handles that.
        """
        if not actions_this_round:
            return ""

        encoded = []

        for item in actions_this_round:
            if isinstance(item, tuple):
                action = item[2]
            else:
                action = item

            encoded.append(action.name)

        return "-".join(encoded)
    
class EquityBucketInfosetKeyBuilder(InfosetKeyBuilder):
    name = "equity_bucket_v1"

    def __init__(self, bucket_provider):
        self.bucket_provider = bucket_provider

    def from_state(self, state, player):
        private_cards = state.player_cards[player]
        public_cards = state.public_cards

        equity_bucket = self.bucket_provider.get_bucket(
            private_cards,
            public_cards,
        )

        position = 1 if player == state.button_player else 0
        facing_bet = state.amount_to_call(player) > 0
        street_history = self.encode_street_history(state.actions_this_round)

        return (
            player,
            state.street,
            equity_bucket,
            position,
            facing_bet,
            state.raises_this_round,
            street_history,
        )

    def from_observation(self, observation):
        private_cards = observation["private_cards"]
        public_cards = observation["public_cards"]

        equity_bucket = self.bucket_provider.get_bucket(
            private_cards,
            public_cards,
        )

        player = observation["current_player"]
        street = observation["street"]

        # These should be added to observation if not already present.
        button_player = observation["button_player"]
        raises_this_round = observation["raises_this_round"]
        amount_to_call = observation["amount_to_call"]
        actions_this_round = observation["actions_this_round"]

        position = 1 if player == button_player else 0
        facing_bet = amount_to_call > 0
        street_history = self.encode_street_history(actions_this_round)

        return (
            player,
            street,
            equity_bucket,
            position,
            facing_bet,
            raises_this_round,
            street_history,
        )    
    
class CachedEquityBucketProvider:
    def __init__(self, equity_cache):
        self.equity_cache = equity_cache

    def get_bucket(self, private_cards, public_cards):
        result = self.equity_cache.get(private_cards, public_cards)
        return result["bucket"]  
    
    
    
    
    
    
    
    
    