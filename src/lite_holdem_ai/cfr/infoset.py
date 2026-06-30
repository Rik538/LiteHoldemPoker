# -*- coding: utf-8 -*-
"""
Information-set key builders for Lite Hold'em CFR.

The goal is to keep abstraction logic separate from CFR training and CFR agents,
so different infoset designs can be swapped in easily.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass

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

class InfosetKeyBuilder(ABC):
    name = "base"
    

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
    
    
    def _pot_bucket(self,pot):
        if pot <= 4:
            return 0
        if pot <= 8:
            return 1
        if pot <= 16:
            return 2
        return 3
    
    
    def _bucket_from_thresholds(self,equity, thresholds):
        for bucket, threshold in enumerate(thresholds):
            if equity < threshold:
                return bucket
    
        return len(thresholds)
    
    
    def _equity_bucket_for_street(self,equity, street, thresholds_by_street):
        thresholds = thresholds_by_street.get(street)
    
        if thresholds is None:
            raise ValueError(f"Unknown street for equity bucket: {street}")
    
        return self._bucket_from_thresholds(equity, thresholds)
    
    def _card_rank(self,card: int):
        return card // 4


    def _card_suit(self,card: int):
        return card % 4
    
    def _board_texture_bucket(self,public_cards):
        if len(public_cards) < 3:
            return 0
    
        ranks = [self._card_rank(card) for card in public_cards]
        suits = [self._card_suit(card) for card in public_cards]
    
        rank_counts = {}
        for rank in ranks:
            rank_counts[rank] = rank_counts.get(rank, 0) + 1
    
        suit_counts = {}
        for suit in suits:
            suit_counts[suit] = suit_counts.get(suit, 0) + 1
    
        paired_board = any(count >= 2 for count in rank_counts.values())
    
        # In 20-card hold'em, 3+ public cards of one suit is already meaningful.
        flush_pressure = any(count >= 3 for count in suit_counts.values())
    
        # Since ranks are only 0-4, straight pressure is mostly about how many
        # distinct ranks are visible.
        straight_pressure = len(set(ranks)) >= 3
    
        return (
            int(paired_board)
            + 2 * int(flush_pressure)
            + 4 * int(straight_pressure)
        )
    
@dataclass(frozen=True)
class InfosetContext:
    private_cards: tuple[int, ...]
    public_cards: tuple[int, ...]
    player: int
    street: int
    pot: int
    button_player: int
    position: int
    amount_to_call: int
    facing_bet: bool
    raises_this_round: int
    actions_this_round: tuple
    action_history: tuple


def build_infoset_context(observation) -> InfosetContext:
    player = observation["player"]
    button_player = observation["button_player"]
    amount_to_call = observation["amount_to_call"]

    return InfosetContext(
        private_cards=tuple(observation["private_cards"]),
        public_cards=tuple(observation["public_cards"]),
        player=player,
        street=observation["street"],
        pot=observation["pot"],
        button_player=button_player,
        position=1 if player == button_player else 0,
        amount_to_call=amount_to_call,
        facing_bet=amount_to_call > 0,
        raises_this_round=observation["raises_this_round"],
        actions_this_round=tuple(observation["actions_this_round"]),
        action_history=tuple(observation["action_history"]),
    )
    
class EquityBucketInfosetKeyBuilder(InfosetKeyBuilder):
    name = "equity_bucket_v1"

    def __init__(self, bucket_provider):
        self.bucket_provider = bucket_provider

   
    def from_observation(self, observation):
        ctx = build_infoset_context(observation)

        equity_bucket = self.bucket_provider.get_bucket(
            ctx.private_cards,
            ctx.public_cards,
        )


        return (
            ctx.player,
            ctx.street,
            equity_bucket,
            ctx.position,
            ctx.facing_bet,
            ctx.raises_this_round,
            self.encode_street_history(ctx.actions_this_round),
        )    
    
class CachedEquityBucketProvider:
    def __init__(self, equity_cache):
        self.equity_cache = equity_cache

    def get_bucket(self, private_cards, public_cards):
        result = self.equity_cache.get(private_cards, public_cards)
        return result["bucket"] 
    
    def get_equity(self, private_cards, public_cards):
        result = self.equity_cache.get(private_cards, public_cards)
        return result["equity"]  
    
class MemoizedBucketProvider:
    def __init__(self, bucket_provider):
        self.bucket_provider = bucket_provider
        self.bucket_cache = {}
        self.equity_cache = {}

    def make_key(self, private_cards, public_cards):
        return (
            tuple(sorted(private_cards)),
            tuple(sorted(public_cards)),
        )
    
    def get_bucket(self, private_cards, public_cards):
        key = self.make_key(private_cards, public_cards)
    
        if key not in self.bucket_cache:
            self.bucket_cache[key] = self.bucket_provider.get_bucket(
                private_cards,
                public_cards,
            )
    
        return self.bucket_cache[key]
    
    def get_equity(self, private_cards, public_cards):
        key = self.make_key(private_cards, public_cards)
    
        if key not in self.equity_cache:
            self.equity_cache[key] = self.bucket_provider.get_equity(
                private_cards,
                public_cards,
            )
    
        return self.equity_cache[key]
    
    
class EquityPotBucketInfosetKeyBuilder(InfosetKeyBuilder):
    name = "equity_pot_bucket_v1"

    def __init__(self, bucket_provider):
        self.bucket_provider = bucket_provider

    

    def from_observation(self, observation):
        ctx = build_infoset_context(observation)

        equity_bucket = self.bucket_provider.get_bucket(
            ctx.private_cards,
            ctx.public_cards,
        )
        
        pot_bucket = self._pot_bucket(ctx.pot)

        return (
            ctx.player,
            ctx.street,
            equity_bucket,
            pot_bucket,
            ctx.position,
            ctx.facing_bet,
            ctx.raises_this_round,
            self.encode_street_history(ctx.actions_this_round),
        )   
    
class StreetSpecificEquityPotBucketInfosetKeyBuilder(InfosetKeyBuilder):
    name = "street_pot_bucket_v1"

    def __init__(self, bucket_provider):
        self.bucket_provider = bucket_provider

    

    def from_observation(self, observation):
        ctx = build_infoset_context(observation)

        
        equity = self.bucket_provider.get_equity(
            ctx.private_cards,
            ctx.public_cards,
        )
        
        pot_bucket = self._pot_bucket(ctx.pot)
      
        equity_bucket = self._equity_bucket_for_street(equity,ctx.street,DEFAULT_STREET_THRESHOLDS)

        return (
            ctx.player,
            ctx.street,
            equity_bucket,
            pot_bucket,
            ctx.position,
            ctx.facing_bet,
            ctx.raises_this_round,
            self.encode_street_history(ctx.actions_this_round),
        ) 

class StreetSpecificEquityBucketInfosetKeyBuilder(InfosetKeyBuilder):
    name = "street_specific_bucket_v1"

    def __init__(self, bucket_provider):
        self.bucket_provider = bucket_provider

    

    def from_observation(self, observation):
        ctx = build_infoset_context(observation)

        
        equity = self.bucket_provider.get_equity(
            ctx.private_cards,
            ctx.public_cards,
        )
        
        equity_bucket = self._equity_bucket_for_street(equity,ctx.street,DEFAULT_STREET_THRESHOLDS)

        return (
            ctx.player,
            ctx.street,
            equity_bucket,
            ctx.position,
            ctx.facing_bet,
            ctx.raises_this_round,
            self.encode_street_history(ctx.actions_this_round),
        ) 

class StreetAwarePotBucketNoHistoryInfosetKeyBuilder(InfosetKeyBuilder):
    name = "street_aware_pot_bucket_no_history_v1"

    def __init__(self, bucket_provider):
        self.bucket_provider = bucket_provider

   

    def from_observation(self, observation):
        ctx = build_infoset_context(observation)

        
        equity = self.bucket_provider.get_equity(
            ctx.private_cards,
            ctx.public_cards,
        )
        
        equity_bucket = self._equity_bucket_for_street(equity,ctx.street,DEFAULT_STREET_THRESHOLDS)
        
        
        pot_bucket = self._pot_bucket(ctx.pot)

        return (
            ctx.player,
            ctx.street,
            equity_bucket,
            pot_bucket,
            ctx.position,
            ctx.facing_bet,
            ctx.raises_this_round,
        ) 

class StreetAwarePotBucket7InfosetKeyBuilder(InfosetKeyBuilder):
    name = "street_aware_pot_bucket_no_history_7_buckets_v1"

    def __init__(self, bucket_provider):
        self.bucket_provider = bucket_provider

    

    def from_observation(self, observation):
        ctx = build_infoset_context(observation)

        
        equity = self.bucket_provider.get_equity(
            ctx.private_cards,
            ctx.public_cards,
        )
        
        equity_bucket = self._equity_bucket_for_street(equity,ctx.street,SEVEN_BUCKET_STREET_THRESHOLDS)
        
        
        pot_bucket = self._pot_bucket(ctx.pot)
       
        return (
            ctx.player,
            ctx.street,
            equity_bucket,
            pot_bucket,
            ctx.position,
            ctx.facing_bet,
            ctx.raises_this_round,
        ) 
    
class StreetAwarePotBucketTextureNoHistoryInfosetKeyBuilder(InfosetKeyBuilder):
    name = "street_aware_pot_bucket_no_history_v1"

    def __init__(self, bucket_provider):
        self.bucket_provider = bucket_provider

   

    def from_observation(self, observation):
        ctx = build_infoset_context(observation)

        
        equity = self.bucket_provider.get_equity(
            ctx.private_cards,
            ctx.public_cards,
        )
        
        equity_bucket = self._equity_bucket_for_street(equity,ctx.street,DEFAULT_STREET_THRESHOLDS)
        
        
        pot_bucket = self._pot_bucket(ctx.pot)

        return (
            ctx.player,
            ctx.street,
            equity_bucket,
            pot_bucket,
            self._board_texture_bucket(ctx.public_cards),
            ctx.position,
            ctx.facing_bet,
            ctx.raises_this_round,
        )
    

    
