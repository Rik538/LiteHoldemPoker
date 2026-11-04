
pub fn create_deck() -> [Card; 20] {

    let ranks: [Rank; 5] = [
        Rank::Ten,
        Rank::Jack,
        Rank::Queen,
        Rank::King,
        Rank::Ace,
    ];

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


}