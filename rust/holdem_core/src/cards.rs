
pub fn create_deck() -> [Card; 20] {

    let ranks: [Rank; 5] = Rank::ALL;

    core::array::from_fn(|index| {
        let suit = Suit::ALL[index / ranks.len()];
        let rank = ranks[index % ranks.len()];

        Card { suit, rank }
    })
}

#[derive(Debug, Copy, Clone, PartialEq, Eq, Hash)]
pub enum Suit {
    Heart,
    Diamond,
    Spade,
    Club,
}

impl Suit {
    pub const ALL: [Suit; 4] = [
        Suit::Heart,
        Suit::Diamond,
        Suit::Spade,
        Suit::Club,
    ];
}

#[derive(Debug, Copy, Clone, PartialEq, Eq, Hash)]
#[repr(u8)]
pub enum Rank {
    Ten = 10,
    Jack = 11,
    Queen = 12,
    King = 13,
    Ace = 14,
}

#[allow(dead_code)]
impl Rank {
    pub const ALL: [Rank; 5] = [
        Rank::Ten,
        Rank::Jack,
        Rank::Queen,
        Rank::King,
        Rank::Ace,
    ];
}


#[allow(dead_code)]
#[derive(Debug, Copy, Clone, PartialEq, Eq, Hash)]
pub struct Card {
    pub(crate) suit: Suit,
    pub(crate) rank: Rank,
}

impl Card {
    pub fn new(suit: Suit, rank: Rank) -> Self {
        Self { suit, rank }
    }
}



pub fn card_to_bit(card: Card) -> u32 {
    let suit_index = match card.suit {
        Suit::Heart => 0,
        Suit::Diamond => 1,
        Suit::Spade => 2,
        Suit::Club => 3,
    };

    let rank_index = match card.rank {
        Rank::Ten => 0,
        Rank::Jack => 1,
        Rank::Queen => 2,
        Rank::King => 3,
        Rank::Ace => 4,
    };

    let pos = suit_index * 5 + rank_index;

    1u32 << pos
}

pub fn bit_to_card(bit: u32) -> Option<Card> {
    if !bit.is_power_of_two() {
        return None;
    }

    let pos = bit.trailing_zeros() as usize;

    if pos >= 20 {
        return None;
    }

    let suits = Suit::ALL;

    let ranks = Rank::ALL;

    Some(Card {
        suit: suits[pos / 5],
        rank: ranks[pos % 5],
    })
}

pub fn cards_to_mask(cards: &[Card]) -> u32 {
    let mut mask: u32 = 0;
    for card in cards {
        mask |= card_to_bit(*card);
    }
    mask
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::collections::HashSet;


    #[test]
    fn test_deck_size() {
        let deck = create_deck();

        assert_eq!(deck.len(), 20);
    }
    
    #[test]
    fn test_unique_cards() {
        let deck = create_deck();

        let unique_cards: HashSet<_> = deck.iter().collect();

        assert_eq!(unique_cards.len(), deck.len());
    }

    #[test]
    fn test_suit_quantity() {
        
        let deck: [Card; 20] = create_deck();

        for suit in Suit::ALL {
            let count: usize = deck.iter()
                .filter(|card: &&Card| card.suit == suit)
                .count();

            assert_eq!(count, 5);
        }
    }

    #[test]
    fn test_card_to_bit(){

        let card = Card {suit: Suit::Diamond, rank: Rank::Queen};

        let card_bit = card_to_bit(card);

        assert_eq!(card_bit,128);

    }

    #[test]
    fn test_bit_to_card(){


        let card = bit_to_card(128);

        assert_eq!(card,Some(Card {suit: Suit::Diamond, rank: Rank::Queen}));


    }

    #[test]
    fn test_all_card_bit_conversions() {
        let deck = create_deck();
        let mut used_bits: u32 = 0;

        for card in deck{
            let bit = card_to_bit(card);

            // Each card must occupy exactly one bit
            assert!(bit.is_power_of_two());

            // No two cards should share the same bit
            assert_eq!(used_bits & bit, 0);

            // Converting back must recover the original card
            assert_eq!(bit_to_card(bit), Some(card));

            used_bits |= bit;
        }

        // Exactly 20 unique bits should be used
        assert_eq!(used_bits.count_ones(), 20);
    }

    #[test]
    fn test_cards_to_mask() {
        let cards = [
            Card { suit: Suit::Heart, rank: Rank::Ten },      // Bit 0 = 1
            Card { suit: Suit::Diamond, rank: Rank::Queen },  // Bit 7 = 128
            Card { suit: Suit::Spade, rank: Rank::Ace },      // Bit 14 = 16384
        ];

        let mask = cards_to_mask(&cards);

        // Check expected combined mask
        assert_eq!(mask, 16513);

        // Exactly three bits should be set
        assert_eq!(mask.count_ones(), 3);

        // Card order should not affect the mask
        let reversed = [cards[2], cards[1], cards[0]];
        assert_eq!(cards_to_mask(&reversed), mask);

        // Empty collection should produce zero
        assert_eq!(cards_to_mask(&[]), 0);
    }

    


}