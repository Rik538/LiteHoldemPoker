use crate::cards::{Card,Rank,Suit};

#[derive(Debug, Copy, Clone, PartialEq, Eq, PartialOrd, Ord)]
pub enum HandRank {
    HighCard = 0,
    OnePair = 1,
    TwoPair = 2,
    ThreeOfAKind = 3,
    Straight = 4,
    Flush = 5,
    FullHouse = 6,
    FourOfAKind = 7,
    StraightFlush = 8,
}

#[derive(Debug, Copy, Clone, PartialEq, Eq, PartialOrd, Ord)]
pub struct HandValue {
    pub category: HandRank,
    pub kickers: [u8; 5],
}

pub struct HandContext {
    pub ranks: [u8; 5],
    pub suits: [u8; 4],
}

pub fn evaluate_hand(private_cards: [Card;2], public_cards: [Card;5]) -> HandValue {
  
    let cards: [Card; 7] = std::array::from_fn(|i| {
        if i < private_cards.len() {
            private_cards[i]
        } else {
            public_cards[i - private_cards.len()]
        }
    });

    let context = build_context(cards);

    // Straight Flush
    if context.suits.iter().any(|&count| count == 5) {
        return HandValue {
            category: HandRank::StraightFlush,
            kickers: [14, 0, 0, 0, 0],
        };
    }

    // Four of a Kind
    if let Some(four_kind) = context.ranks.iter().rposition(|&count| count == 4) {
        let kicker = (0..context.ranks.len())
            .rev()
            .find(|&i| i != four_kind && context.ranks[i] > 0)
            .unwrap();

        return HandValue {
            category: HandRank::FourOfAKind,
            kickers: [four_kind as u8 + 10, kicker as u8 + 10, 0, 0, 0],
        };
    }

    // Full House
    if let Some(three_kind) = context.ranks.iter().rposition(|&count| count == 3) {

        let pair = (0..context.ranks.len())
            .rev()
            .find(|&i| i != three_kind && context.ranks[i] >= 2);

        if let Some(pair) = pair {
            return HandValue {
                category: HandRank::FullHouse,
                kickers: [three_kind as u8 + 10, pair as u8 + 10, 0, 0, 0],
            };
        }
    }
    
    //straight
    if context.ranks.iter().all(|&count| count >= 1) {
        return HandValue {
            category: HandRank::Straight,
            kickers: [14, 0, 0, 0, 0],
        };
    }

    // Two Pair
    if let Some(first_pair) = context.ranks.iter().rposition(|&count| count == 2) {
        if let Some(second_pair) = (0..first_pair).rev().find(|&i| context.ranks[i] == 2) {
            let kicker = (0..context.ranks.len())
                .rev()
                .find(|&i| i != first_pair && i != second_pair && context.ranks[i] > 0)
                .unwrap();

            return HandValue {
                category: HandRank::TwoPair,
                kickers: [first_pair as u8 + 10, second_pair as u8 + 10, kicker as u8 + 10, 0, 0],
            };
        }
    }

    HandValue {
        category: HandRank::HighCard,
        kickers: [0; 5],
    }
}

fn build_context(cards: [Card; 7]) -> HandContext {
    let mut rank_counts = [0u8; 5];
    let mut suit_counts = [0u8; 4];

    for card in cards {
        let rank_index = match card.rank {
            Rank::Ten => 0,
            Rank::Jack => 1,
            Rank::Queen => 2,
            Rank::King => 3,
            Rank::Ace => 4,
        };

        let suit_index = match card.suit {
            Suit::Heart => 0,
            Suit::Diamond => 1,
            Suit::Spade => 2,
            Suit::Club => 3,
        };

        rank_counts[rank_index] += 1;
        suit_counts[suit_index] += 1;
    }

    HandContext { ranks: rank_counts, suits: suit_counts }
}








#[cfg(test)]
mod tests {
    use super::*;
    use crate::cards::{Card, Rank, Suit};

    fn evaluate_valid(
        private: [Card; 2],
        public: [Card; 5],
    ) -> HandValue {
        use std::collections::HashSet;

        let unique: HashSet<_> = private
            .iter()
            .chain(public.iter())
            .copied()
            .collect();

        assert_eq!(unique.len(), 7, "Duplicate cards in test");

        evaluate_hand(private, public)
    }

    #[test]
    fn test_straight() {

        let private_cards = [
            Card { rank: Rank::Ace, suit: Suit::Heart },
            Card { rank: Rank::King, suit: Suit::Spade },];
            
        let public_cards = [
            
            Card { rank: Rank::Queen, suit: Suit::Heart },
            Card { rank: Rank::Queen, suit: Suit::Spade },
            Card { rank: Rank::Jack, suit: Suit::Heart },
            Card { rank: Rank::Ten, suit: Suit::Spade },
            Card { rank: Rank::King, suit: Suit::Club },
        ];

        let result = evaluate_hand(private_cards, public_cards);

        assert_eq!(
            result,
            HandValue {
                category: HandRank::Straight,
                kickers: [14, 0, 0, 0, 0],
            }
        );
    }

    #[test]
    fn test_two_pair() {

        let private_cards = [
            Card { rank: Rank::Ace, suit: Suit::Heart },
            Card { rank: Rank::Ace, suit: Suit::Spade },];
            
        let public_cards = [
            
            Card { rank: Rank::Queen, suit: Suit::Heart },
            Card { rank: Rank::Queen, suit: Suit::Spade },
            Card { rank: Rank::Ten, suit: Suit::Heart },
            Card { rank: Rank::Ten, suit: Suit::Spade },
            Card { rank: Rank::King, suit: Suit::Club },
        ];

        let result = evaluate_hand(private_cards, public_cards);

        assert_eq!(
            result,
            HandValue {
                category: HandRank::TwoPair,
                kickers: [14, 12, 13, 0, 0],
            }
        );
    }

    #[test]
    fn test_full_house() {

        let private_cards = [
            Card { rank: Rank::Ace, suit: Suit::Heart },
            Card { rank: Rank::Ace, suit: Suit::Spade },];
            
        let public_cards = [
            
            Card { rank: Rank::Ace, suit: Suit::Club },
            Card { rank: Rank::Queen, suit: Suit::Spade },
            Card { rank: Rank::Ten, suit: Suit::Heart },
            Card { rank: Rank::Ten, suit: Suit::Spade },
            Card { rank: Rank::King, suit: Suit::Club },
        ];

        let result = evaluate_hand(private_cards, public_cards);

        assert_eq!(
            result,
            HandValue {
                category: HandRank::FullHouse,
                kickers: [14, 10, 0, 0, 0],
            }
        );
    }

    #[test]
    fn test_four_kind() {

        let private_cards = [
            Card { rank: Rank::Queen, suit: Suit::Heart },
            Card { rank: Rank::Queen, suit: Suit::Spade },];
            
        let public_cards = [
            
            Card { rank: Rank::Queen, suit: Suit::Diamond },
            Card { rank: Rank::Queen, suit: Suit::Club },
            Card { rank: Rank::Ten, suit: Suit::Heart },
            Card { rank: Rank::Ten, suit: Suit::Spade },
            Card { rank: Rank::King, suit: Suit::Club },
        ];

        let result = evaluate_hand(private_cards, public_cards);

        assert_eq!(
            result,
            HandValue {
                category: HandRank::FourOfAKind,
                kickers: [12, 13, 0, 0, 0],
            }
        );
    }

    #[test]
    fn test_straight_flush() {

        let private_cards = [
            Card { rank: Rank::Ace, suit: Suit::Heart },
            Card { rank: Rank::King, suit: Suit::Heart },];
            
        let public_cards = [
            
            Card { rank: Rank::Queen, suit: Suit::Heart },
            Card { rank: Rank::Jack, suit: Suit::Heart },
            Card { rank: Rank::Ten, suit: Suit::Heart },
            Card { rank: Rank::Ten, suit: Suit::Spade },
            Card { rank: Rank::King, suit: Suit::Club },
        ];

        let result = evaluate_hand(private_cards, public_cards);

        assert_eq!(
            result,
            HandValue {
                category: HandRank::StraightFlush,
                kickers: [14, 0, 0, 0, 0],
            }
        );
    }

    #[test]
    fn test_two_three_of_a_kind() {
        let private = [
            Card { rank: Rank::Ace, suit: Suit::Heart },
            Card { rank: Rank::Ace, suit: Suit::Spade },
        ];

        let public = [
            Card { rank: Rank::Ace, suit: Suit::Diamond },
            Card { rank: Rank::King, suit: Suit::Heart },
            Card { rank: Rank::King, suit: Suit::Spade },
            Card { rank: Rank::King, suit: Suit::Diamond },
            Card { rank: Rank::Queen, suit: Suit::Club },
        ];

        assert_eq!(
            evaluate_valid(private, public),
            HandValue {
                category: HandRank::FullHouse,
                kickers: [14, 13, 0, 0, 0],
            }
        );
    }

    #[test]
    fn test_four_kind_kicker_comparison() {
        let queens = [
            Card { rank: Rank::Queen, suit: Suit::Heart },
            Card { rank: Rank::Queen, suit: Suit::Spade },
        ];

        let with_ace = [
            Card { rank: Rank::Queen, suit: Suit::Diamond },
            Card { rank: Rank::Queen, suit: Suit::Club },
            Card { rank: Rank::Ace, suit: Suit::Heart },
            Card { rank: Rank::King, suit: Suit::Spade },
            Card { rank: Rank::Jack, suit: Suit::Diamond },
        ];

        let with_king = [
            Card { rank: Rank::Queen, suit: Suit::Diamond },
            Card { rank: Rank::Queen, suit: Suit::Club },
            Card { rank: Rank::King, suit: Suit::Heart },
            Card { rank: Rank::Jack, suit: Suit::Spade },
            Card { rank: Rank::Ten, suit: Suit::Diamond },
        ];

        let ace_kicker = evaluate_valid(queens, with_ace);
        let king_kicker = evaluate_valid(queens, with_king);

        assert_eq!(ace_kicker.kickers, [12, 14, 0, 0, 0]);
        assert_eq!(king_kicker.kickers, [12, 13, 0, 0, 0]);

        assert!(ace_kicker > king_kicker);
    }

    #[test]
    fn test_three_pairs() {
        let private = [
            Card { rank: Rank::Ace, suit: Suit::Heart },
            Card { rank: Rank::Ace, suit: Suit::Spade },
        ];

        let public = [
            Card { rank: Rank::King, suit: Suit::Heart },
            Card { rank: Rank::King, suit: Suit::Spade },
            Card { rank: Rank::Queen, suit: Suit::Heart },
            Card { rank: Rank::Queen, suit: Suit::Spade },
            Card { rank: Rank::Jack, suit: Suit::Club },
        ];

        assert_eq!(
            evaluate_valid(private, public),
            HandValue {
                category: HandRank::TwoPair,
                kickers: [14, 13, 12, 0, 0],
            }
        );
    }

    #[test]
    fn test_full_house_beats_straight() {
        let full_house = evaluate_valid(
            [
                Card { rank: Rank::Ace, suit: Suit::Heart },
                Card { rank: Rank::Ace, suit: Suit::Spade },
            ],
            [
                Card { rank: Rank::Ace, suit: Suit::Diamond },
                Card { rank: Rank::King, suit: Suit::Heart },
                Card { rank: Rank::King, suit: Suit::Spade },
                Card { rank: Rank::Queen, suit: Suit::Club },
                Card { rank: Rank::Jack, suit: Suit::Club },
            ],
        );

        let straight = evaluate_valid(
            [
                Card { rank: Rank::Ace, suit: Suit::Heart },
                Card { rank: Rank::King, suit: Suit::Spade },
            ],
            [
                Card { rank: Rank::Queen, suit: Suit::Diamond },
                Card { rank: Rank::Jack, suit: Suit::Club },
                Card { rank: Rank::Ten, suit: Suit::Heart },
                Card { rank: Rank::Ace, suit: Suit::Spade },
                Card { rank: Rank::King, suit: Suit::Heart },
            ],
        );

        assert_eq!(full_house.category, HandRank::FullHouse);
        assert_eq!(straight.category, HandRank::Straight);

        assert!(full_house > straight);
    }

    #[test]
    fn test_tied_hands() {
        let public = [
            Card { rank: Rank::Ten, suit: Suit::Heart },
            Card { rank: Rank::Jack, suit: Suit::Diamond },
            Card { rank: Rank::Queen, suit: Suit::Spade },
            Card { rank: Rank::King, suit: Suit::Club },
            Card { rank: Rank::Ace, suit: Suit::Heart },
        ];

        let player_0 = [
            Card { rank: Rank::Ten, suit: Suit::Diamond },
            Card { rank: Rank::Jack, suit: Suit::Spade },
        ];

        let player_1 = [
            Card { rank: Rank::Ten, suit: Suit::Spade },
            Card { rank: Rank::Jack, suit: Suit::Club },
        ];

        let value_0 = evaluate_valid(player_0, public);
        let value_1 = evaluate_valid(player_1, public);

        assert_eq!(value_0, value_1);

        assert_eq!(
            value_0,
            HandValue {
                category: HandRank::Straight,
                kickers: [14, 0, 0, 0, 0],
            }
        );
    }
}