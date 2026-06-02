# -*- coding: utf-8 -*-
"""
Created on Thu May 14 15:28:51 2026

@author: Richard
"""

# -*- coding: utf-8 -*-
"""
Created on Thu Mar  5 14:41:01 2026

@author: Richard
"""


from lite_holdem_ai.game.deck import Deck
from lite_holdem_ai.game.state import GameState
from lite_holdem_ai.game.actions import Action
from .base import Agent


class HeuristicAgent(Agent):
    name = "Heuristic"
    
    def __init__(self, seed: int | None = None, name: str | None = None):
        self.name = name if name is not None else "Heuristic"

        
        # You can tune these later
        self.strong_threshold = 70
        self.medium_threshold = 45
        self.weak_call_threshold = 25


    
    def select_action(self, observation, legal_actions):
        if not legal_actions:
            raise ValueError("HeuristicAgent received no legal actions")
        
        private_cards = observation["private_cards"]
        public_cards = observation["public_cards"]
        pot = observation["pot"]
        amount_to_call = observation["amount_to_call"]
        street = observation["street"]

        strength = self.hand_strength_score(private_cards, public_cards, street)

        if amount_to_call == 0:
            return self.act_when_free(strength, legal_actions)

        return self.act_facing_bet(strength, pot, amount_to_call, legal_actions)

    def act_when_free(self, strength, legal_actions):
        """
        No bet to call:
        CHECK_CALL means check.
        BET_RAISE means bet.
        """
        if Action.BET_RAISE in legal_actions and strength >= self.medium_threshold:
            return Action.BET_RAISE

        if Action.CHECK_CALL in legal_actions:
            return Action.CHECK_CALL

        return legal_actions[0]

    def act_facing_bet(self, strength, pot, amount_to_call, legal_actions):
        """
        Facing a bet:
        FOLD means fold.
        CHECK_CALL means call.
        BET_RAISE means raise.
        """
        pot_odds = self.pot_odds(pot, amount_to_call)

        if Action.BET_RAISE in legal_actions and strength >= self.strong_threshold:
            return Action.BET_RAISE

        # Convert strength score to rough 0-1 confidence.
        confidence = strength / 100

        if Action.CHECK_CALL in legal_actions and confidence >= pot_odds:
            return Action.CHECK_CALL

        if Action.CHECK_CALL in legal_actions and strength >= self.weak_call_threshold:
            return Action.CHECK_CALL

        if Action.FOLD in legal_actions:
            return Action.FOLD

        return legal_actions[0]

    def pot_odds(self, pot, amount_to_call):
        if amount_to_call <= 0:
            return 0.0

        return amount_to_call / (pot + amount_to_call)

    def hand_strength_score(self, private_cards, public_cards, street):
        """
        Returns rough hand strength from 0 to 100.

        This is not exact equity. It is a fast heuristic based on:
        - private card quality
        - pairs/trips/quads
        - made straights/flushes
        - board texture
        - current street
        """
        all_cards = private_cards + public_cards

        private_ranks = [self.card_rank(c) for c in private_cards]
        public_ranks = [self.card_rank(c) for c in public_cards]
        all_ranks = [self.card_rank(c) for c in all_cards]
        all_suits = [self.card_suit(c) for c in all_cards]

        rank_counts = self.counts(all_ranks)
        suit_counts = self.counts(all_suits)

        score = 0

        # ------------------------------------------------------------------
        # Preflop logic
        # ------------------------------------------------------------------
        if len(public_cards) == 0:
            r1, r2 = sorted(private_ranks, reverse=True)

            # Pocket pair
            if r1 == r2:
                score += 45 + r1 * 8
            else:
                # High-card strength
                score += r1 * 8 + r2 * 4

                # Connected cards are better in this tiny deck
                if abs(r1 - r2) == 1:
                    score += 8

                # Broad high-card bonus
                if r1 >= 3:
                    score += 8
                if r2 >= 2:
                    score += 5

            # Suited bonus
            if self.card_suit(private_cards[0]) == self.card_suit(private_cards[1]):
                score += 6

            return self.clamp(score, 0, 100)

        # ------------------------------------------------------------------
        # Made hand logic
        # ------------------------------------------------------------------
        counts_sorted = sorted(rank_counts.values(), reverse=True)

        has_straight = self.has_straight(all_ranks)
        has_flush = any(count >= 5 for count in suit_counts.values())
        has_straight_flush = self.has_straight_flush(all_cards)

        quads = self.ranks_with_count(rank_counts, 4)
        trips = self.ranks_with_count(rank_counts, 3)
        pairs = self.ranks_with_count(rank_counts, 2)

        if has_straight_flush:
            score += 100
        elif quads:
            score += 95 + max(quads)
        elif self.has_full_house(rank_counts):
            score += 88
        elif has_flush:
            score += 80 + self.best_flush_rank(all_cards)
        elif has_straight:
            score += 74
        elif trips:
            score += 62 + max(trips) * 3
        elif len(pairs) >= 2:
            best_two = sorted(pairs, reverse=True)[:2]
            score += 50 + best_two[0] * 4 + best_two[1] * 2
        elif len(pairs) == 1:
            pair_rank = pairs[0]
            score += 32 + pair_rank * 6
        else:
            score += self.high_card_score(all_ranks)

        # ------------------------------------------------------------------
        # Private-card involvement bonus
        # ------------------------------------------------------------------
        # Hands are more valuable if our private cards actually contribute.
        score += self.private_involvement_bonus(private_cards, public_cards, rank_counts)

        # ------------------------------------------------------------------
        # Draw / texture bonuses
        # ------------------------------------------------------------------
        if len(public_cards) in (3, 4):
            score += self.draw_bonus(private_cards, public_cards)

        # ------------------------------------------------------------------
        # Street adjustment
        # ------------------------------------------------------------------
        # On later streets, weak made hands are less exciting.
        if len(public_cards) == 5:
            if score < 45:
                score -= 8
            elif score >= 70:
                score += 5

        return self.clamp(score, 0, 100)

    def card_rank(self, card):
        return card // 4

    def card_suit(self, card):
        return card % 4

    def counts(self, values):
        result = {}

        for value in values:
            result[value] = result.get(value, 0) + 1

        return result

    def ranks_with_count(self, rank_counts, target_count):
        return [
            rank for rank, count in rank_counts.items()
            if count == target_count
        ]

    def has_straight(self, ranks):
        return set(ranks) == {0, 1, 2, 3, 4} or {0, 1, 2, 3, 4}.issubset(set(ranks))

    def has_straight_flush(self, cards):
        ranks_by_suit = {
            0: [],
            1: [],
            2: [],
            3: [],
        }

        for card in cards:
            suit = self.card_suit(card)
            rank = self.card_rank(card)
            ranks_by_suit[suit].append(rank)

        needed = {0, 1, 2, 3, 4}

        for ranks in ranks_by_suit.values():
            if needed.issubset(set(ranks)):
                return True

        return False

    def has_full_house(self, rank_counts):
        trips = [
            rank for rank, count in rank_counts.items()
            if count >= 3
        ]

        pairs_or_better = [
            rank for rank, count in rank_counts.items()
            if count >= 2
        ]

        if not trips:
            return False

        best_trip = max(trips)

        for rank in pairs_or_better:
            if rank != best_trip:
                return True

        return False

    def best_flush_rank(self, cards):
        ranks_by_suit = {
            0: [],
            1: [],
            2: [],
            3: [],
        }

        for card in cards:
            suit = self.card_suit(card)
            rank = self.card_rank(card)
            ranks_by_suit[suit].append(rank)

        best = 0

        for ranks in ranks_by_suit.values():
            if len(ranks) >= 5:
                best = max(best, max(ranks))

        return best

    def high_card_score(self, ranks):
        unique = sorted(set(ranks), reverse=True)

        score = 0

        if len(unique) > 0:
            score += unique[0] * 5
        if len(unique) > 1:
            score += unique[1] * 3
        if len(unique) > 2:
            score += unique[2] * 2

        return score

    def private_involvement_bonus(self, private_cards, public_cards, rank_counts):
        if not public_cards:
            return 0

        private_ranks = [self.card_rank(c) for c in private_cards]
        public_ranks = [self.card_rank(c) for c in public_cards]

        bonus = 0

        for rank in private_ranks:
            count = rank_counts.get(rank, 0)

            if count >= 4:
                bonus += 18
            elif count == 3:
                bonus += 12
            elif count == 2:
                bonus += 7

        # Penalise cases where the board alone is doing most of the work.
        public_rank_counts = self.counts(public_ranks)

        board_pairs = any(count >= 2 for count in public_rank_counts.values())
        private_pairs_board = any(rank in public_ranks for rank in private_ranks)

        if board_pairs and not private_pairs_board:
            bonus -= 6

        return bonus

    def draw_bonus(self, private_cards, public_cards):
        """
        Small bonus for hands that are close to flushes/straights.
        In this 20-card deck, straight draws are unusual because there is only
        one possible straight: T-J-Q-K-A.
        """
        all_cards = private_cards + public_cards
        all_ranks = [self.card_rank(c) for c in all_cards]
        all_suits = [self.card_suit(c) for c in all_cards]

        rank_set = set(all_ranks)
        suit_counts = self.counts(all_suits)

        bonus = 0

        # Four cards to the only straight
        if len(rank_set) == 4:
            bonus += 8

        # Flush draw
        if any(count == 4 for count in suit_counts.values()):
            bonus += 10
        elif any(count == 3 for count in suit_counts.values()) and len(public_cards) == 3:
            bonus += 4

        return bonus

    def clamp(self, value, low, high):
        return max(low, min(high, value))
            
        
            
        

    
    