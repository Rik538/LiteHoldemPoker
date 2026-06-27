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
    def from_state(self, env, player):
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

    def from_state(self, env, player):
        private_cards = env.state.player_cards[player]
        public_cards = env.state.public_cards

        equity_bucket = self.bucket_provider.get_bucket(
            private_cards,
            public_cards,
        )

        position = 1 if player == env.state.button_player else 0
        facing_bet = env.amount_to_call(player) > 0
        street_history = self.encode_street_history(env.state.actions_this_round)

        return (
            player,
            env.state.street,
            equity_bucket,
            position,
            facing_bet,
            env.state.raises_this_round,
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
    
    def get_equity(self, private_cards, public_cards):
        result = self.equity_cache.get(private_cards, public_cards)
        return result["equity"]  
    
class MemoizedBucketProvider:
    """
    Wraps another bucket provider and caches bucket lookups in memory.

    This is useful for CFR/MCCFR because infoset generation calls get_bucket()
    very frequently.
    """

    def __init__(self, bucket_provider):
        self.bucket_provider = bucket_provider
        self.cache = {}
        self.hits = 0
        self.misses = 0

    def make_key(self, private_cards, public_cards):
        return (
            tuple(sorted(private_cards)),
            tuple(sorted(public_cards)),
        )

    def get_bucket(self, private_cards, public_cards):
        key = self.make_key(private_cards, public_cards)

        if key in self.cache:
            self.hits += 1
            return self.cache[key]

        self.misses += 1
        bucket = self.bucket_provider.get_bucket(private_cards, public_cards)
        self.cache[key] = bucket

        return bucket
    
    def get_equity(self, private_cards, public_cards):
        key = self.make_key(private_cards, public_cards)

        if key in self.cache:
            self.hits += 1
            return self.cache[key]

        self.misses += 1
        equity = self.bucket_provider.get_equity(private_cards, public_cards)
        self.cache[key] = equity

        return equity
    
    def stats(self):
        total = self.hits + self.misses

        if total == 0:
            hit_rate = 0.0
        else:
            hit_rate = self.hits / total

        return {
            "entries": len(self.cache),
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": hit_rate,
        }
    
    
class EquityPotBucketInfosetKeyBuilder(InfosetKeyBuilder):
    name = "equity_pot_bucket_v1"

    def __init__(self, bucket_provider):
        self.bucket_provider = bucket_provider

    def from_state(self, env, player):
        private_cards = env.state.player_cards[player]
        public_cards = env.state.public_cards

        equity_bucket = self.bucket_provider.get_bucket(
            private_cards,
            public_cards,
        )
        
        pot_bucket = self.pot_bucket(env.state.pot)

        position = 1 if player == env.state.button_player else 0
        facing_bet = env.amount_to_call(player) > 0
        street_history = self.encode_street_history(env.state.actions_this_round)

        return (
            player,
            env.state.street,
            equity_bucket,
            pot_bucket,
            position,
            facing_bet,
            env.state.raises_this_round,
            street_history,
        )

    def from_observation(self, observation):
        private_cards = observation["private_cards"]
        public_cards = observation["public_cards"]

        equity_bucket = self.bucket_provider.get_bucket(
            private_cards,
            public_cards,
        )
        
        pot_bucket = self.pot_bucket(observation["pot"])

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
            pot_bucket,
            position,
            facing_bet,
            raises_this_round,
            street_history,
        )   
    
    def pot_bucket(self, pot):
        if pot <= 4:
            return 0
        if pot <= 8:
            return 1
        if pot <= 16:
            return 2
        return 3


class StreetSpecificEquityPotBucketInfosetKeyBuilder(InfosetKeyBuilder):
    name = "street_pot_bucket_v1"

    def __init__(self, bucket_provider):
        self.bucket_provider = bucket_provider

    def from_state(self, env, player):
        private_cards = env.state.player_cards[player]
        public_cards = env.state.public_cards

        equity = self.bucket_provider.get_equity(
            private_cards,
            public_cards,
        )
        
 
        
        equity_bucket = self.equity_bucket_for_street(equity,env.state.street)
        
        pot_bucket = self.pot_bucket(env.state.pot)

        position = 1 if player == env.state.button_player else 0
        facing_bet = env.amount_to_call(player,env.state) > 0
        street_history = self.encode_street_history(env.state.actions_this_round)

        return (
            player,
            env.state.street,
            equity_bucket,
            pot_bucket,
            position,
            facing_bet,
            env.state.raises_this_round,
            street_history,
        )

    def from_observation(self, observation):
        private_cards = observation["private_cards"]
        public_cards = observation["public_cards"]

        equity = self.bucket_provider.get_equity(
            private_cards,
            public_cards,
        )
        
       
        
        
        
        pot_bucket = self.pot_bucket(observation["pot"])

        player = observation["current_player"]
        street = observation["street"]
        
        equity_bucket = self.equity_bucket_for_street(equity,street)

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
            pot_bucket,
            position,
            facing_bet,
            raises_this_round,
            street_history,
        ) 
    
    def equity_bucket_for_street(self,equity, street):
        if street == 0:  # preflop
            thresholds = [0.35, 0.45, 0.55, 0.65]
        elif street == 1:  # flop
            thresholds = [0.25, 0.40, 0.55, 0.70]
        elif street == 2:  # turn
            thresholds = [0.20, 0.35, 0.55, 0.75]
        else:  # river
            thresholds = [0.10, 0.30, 0.50, 0.75]
    
        for bucket, threshold in enumerate(thresholds):
            if equity < threshold:
                return bucket
    
        return len(thresholds)
    
    def pot_bucket(self, pot):
        if pot <= 4:
            return 0
        if pot <= 8:
            return 1
        if pot <= 16:
            return 2
        return 3    
    
    
class StreetSpecificEquityBucketInfosetKeyBuilder(InfosetKeyBuilder):
    name = "street_specific_bucket_v1"

    def __init__(self, bucket_provider):
        self.bucket_provider = bucket_provider

    def from_state(self, env, player):
        private_cards = env.state.player_cards[player]
        public_cards = env.state.public_cards

        equity = self.bucket_provider.get_equity(
            private_cards,
            public_cards,
        )
        
 
        
        equity_bucket = self.equity_bucket_for_street(equity,env.state.street)
        

        position = 1 if player == env.state.button_player else 0
        facing_bet = env.amount_to_call(player,env.state) > 0
        street_history = self.encode_street_history(env.state.actions_this_round)

        return (
            player,
            env.state.street,
            equity_bucket,
            position,
            facing_bet,
            env.state.raises_this_round,
            street_history,
        )

    def from_observation(self, observation):
        private_cards = observation["private_cards"]
        public_cards = observation["public_cards"]

        equity = self.bucket_provider.get_equity(
            private_cards,
            public_cards,
        )
        


        player = observation["current_player"]
        street = observation["street"]
        
        equity_bucket = self.equity_bucket_for_street(equity,street)

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
    
    def equity_bucket_for_street(self,equity, street):
        if street == 0:  # preflop
            thresholds = [0.35, 0.45, 0.55, 0.65]
        elif street == 1:  # flop
            thresholds = [0.25, 0.40, 0.55, 0.70]
        elif street == 2:  # turn
            thresholds = [0.20, 0.35, 0.55, 0.75]
        else:  # river
            thresholds = [0.10, 0.30, 0.50, 0.75]
    
        for bucket, threshold in enumerate(thresholds):
            if equity < threshold:
                return bucket
    
        return len(thresholds)
    

class StreetAwarePotBucketNoHistoryInfosetKeyBuilder(InfosetKeyBuilder):
    name = "street_aware_pot_bucket_no_history_v1"

    def __init__(self, bucket_provider):
        self.bucket_provider = bucket_provider

    def from_state(self, env, player):
        private_cards = env.state.player_cards[player]
        public_cards = env.state.public_cards

        equity = self.bucket_provider.get_equity(
            private_cards,
            public_cards,
        )
        
 
        
        equity_bucket = self.equity_bucket_for_street(equity,env.state.street)
        
        pot_bucket = self.pot_bucket(env.state.pot)

        position = 1 if player == env.state.button_player else 0
        facing_bet = env.amount_to_call(player,env.state) > 0

        return (
            player,
            env.state.street,
            equity_bucket,
            pot_bucket,
            position,
            facing_bet,
            env.state.raises_this_round,
        )

    def from_observation(self, observation):
        private_cards = observation["private_cards"]
        public_cards = observation["public_cards"]

        equity = self.bucket_provider.get_equity(
            private_cards,
            public_cards,
        )
        
       
        
        
        
        pot_bucket = self.pot_bucket(observation["pot"])

        player = observation["current_player"]
        street = observation["street"]
        
        equity_bucket = self.equity_bucket_for_street(equity,street)

        # These should be added to observation if not already present.
        button_player = observation["button_player"]
        raises_this_round = observation["raises_this_round"]
        amount_to_call = observation["amount_to_call"]

        position = 1 if player == button_player else 0
        facing_bet = amount_to_call > 0

        return (
            player,
            street,
            equity_bucket,
            pot_bucket,
            position,
            facing_bet,
            raises_this_round,
        ) 
    
    def equity_bucket_for_street(self,equity, street):
        if street == 0:  # preflop
            thresholds = [0.35, 0.45, 0.55, 0.65]
        elif street == 1:  # flop
            thresholds = [0.25, 0.40, 0.55, 0.70]
        elif street == 2:  # turn
            thresholds = [0.20, 0.35, 0.55, 0.75]
        else:  # river
            thresholds = [0.10, 0.30, 0.50, 0.75]
    
        for bucket, threshold in enumerate(thresholds):
            if equity < threshold:
                return bucket
    
        return len(thresholds)
    
    def pot_bucket(self, pot):
        if pot <= 4:
            return 0
        if pot <= 8:
            return 1
        if pot <= 16:
            return 2
        return 3    
  

class StreetAwarePotBucket7InfosetKeyBuilder(InfosetKeyBuilder):
    name = "street_aware_pot_bucket_no_history_7_buckets_v1"

    def __init__(self, bucket_provider):
        self.bucket_provider = bucket_provider

    def from_state(self, env, player):
        private_cards = env.state.player_cards[player]
        public_cards = env.state.public_cards

        equity = self.bucket_provider.get_equity(
            private_cards,
            public_cards,
        )
        
 
        
        equity_bucket = self.equity_bucket_for_street(equity,env.state.street)
        
        pot_bucket = self.pot_bucket(env.state.pot)

        position = 1 if player == env.state.button_player else 0
        facing_bet = env.amount_to_call(player,env.state) > 0

        return (
            player,
            env.state.street,
            equity_bucket,
            pot_bucket,
            position,
            facing_bet,
            env.state.raises_this_round,
        )

    def from_observation(self, observation):
        private_cards = observation["private_cards"]
        public_cards = observation["public_cards"]

        equity = self.bucket_provider.get_equity(
            private_cards,
            public_cards,
        )
        
        
        pot_bucket = self.pot_bucket(observation["pot"])

        player = observation["current_player"]
        street = observation["street"]
        
        equity_bucket = self.equity_bucket_for_street(equity,street)

        # These should be added to observation if not already present.
        button_player = observation["button_player"]
        raises_this_round = observation["raises_this_round"]
        amount_to_call = observation["amount_to_call"]

        position = 1 if player == button_player else 0
        facing_bet = amount_to_call > 0

        return (
            player,
            street,
            equity_bucket,
            pot_bucket,
            position,
            facing_bet,
            raises_this_round,
        ) 
    
    def equity_bucket_for_street(self, equity, street):
        if street == 0:  # preflop
            thresholds = [0.30, 0.38, 0.46, 0.54, 0.62, 0.70]
        elif street == 1:  # flop
            thresholds = [0.18, 0.30, 0.42, 0.55, 0.68, 0.80]
        elif street == 2:  # turn
            thresholds = [0.12, 0.25, 0.40, 0.55, 0.72, 0.85]
        else:  # river
            thresholds = [0.05, 0.20, 0.35, 0.50, 0.70, 0.88]
    
        for bucket, threshold in enumerate(thresholds):
            if equity < threshold:
                return bucket
    
        return len(thresholds)
    
    def pot_bucket(self, pot):
        if pot <= 4:
            return 0
        if pot <= 8:
            return 1
        if pot <= 16:
            return 2
        return 3    
        
  
    