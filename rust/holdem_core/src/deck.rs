use rand::seq::SliceRandom;
use rand::Rng;

use crate::cards::Card;
use crate::cards::create_deck;

#[derive(Debug, Copy, Clone, PartialEq, Eq, Hash)]
pub struct Deck {
    cards: [Card; 20],
    next_card: usize,
}

impl Deck {
    pub fn new() -> Deck {
        Deck {
            cards: create_deck(),
            next_card: 0,
        }
    }
}

impl Deck {
    pub fn draw(&mut self) -> Option<Card> {
        if self.next_card >= self.cards.len() {
            return None;
        }

        let drawn_card = self.cards[self.next_card];
        self.next_card += 1;

        Some(drawn_card)
    }
}


impl Deck {
    pub fn shuffle<R: Rng + ?Sized>(&mut self, rng: &mut R) {
        self.cards.shuffle(rng);
        self.next_card = 0;
    }
}

impl Deck {
    pub fn remaining(&self) -> usize {
        self.cards.len() - self.next_card
    }
}


#[cfg(test)]
mod tests {
    use super::*;
    use std::collections::HashSet;
    use rand::rngs::StdRng;
    use rand::SeedableRng;

    

    #[test]
    fn test_deck_size() {
        let deck = Deck::new();

        assert_eq!(deck.cards.len(), 20);
        assert_eq!(deck.remaining(),20);
    }

    #[test]
    fn test_shuffled_deck_size() {
        
        let mut deck = Deck::new();
        
        let mut rng = StdRng::seed_from_u64(42);
        deck.shuffle(&mut rng);

        assert_eq!(deck.cards.len(), 20);
    }

    #[test]
    fn test_draw() {
        let mut deck = Deck::new();
        
        assert!(deck.draw().is_some());
        assert_eq!(deck.remaining(),19)

    }

    

    #[test]
    fn test_draw_all() {
        let mut deck = Deck::new();

        let len = deck.cards.len();

        let mut drawn_cards: [Option<Card>; 20] = [None; 20];

        for idx in 0..len {
            drawn_cards[idx] = deck.draw();
        }

        assert_eq!(deck.remaining(),0);

        assert_eq!(drawn_cards.len(), deck.cards.len());

    }

    #[test]
    fn test_shuffled_draw_all() {
        let mut deck = Deck::new();

        let mut rng = StdRng::seed_from_u64(42);
        deck.shuffle(&mut rng);

        let len = deck.cards.len();

        let mut drawn_cards: [Option<Card>; 20] = [None; 20];

        for idx in 0..len {
            drawn_cards[idx] = deck.draw();
        }

        assert_eq!(drawn_cards.len(), deck.cards.len());

    }

    #[test]
    fn test_draw_exhausted() {
        let mut deck = Deck::new();

        let len = deck.cards.len();

        for _ in 0..len {
            assert!(deck.draw().is_some());
        }

        assert_eq!(deck.remaining(),0);

        assert!(deck.draw().is_none());

        assert_eq!(deck.remaining(),0);
    }
    
    #[test]
    fn test_no_duplicate_draws() {
        let mut deck = Deck::new();

        let len = deck.cards.len();
        let mut drawn_cards: Vec<Option<Card>> = Vec::with_capacity(len);

        for _ in 0..len {
            drawn_cards.push(deck.draw());
        }

        let unique_cards: HashSet<_> = drawn_cards.iter().cloned().collect();

        assert_eq!(unique_cards.len(), len);
    }
    
    #[test]
    fn test_shuffled_no_duplicate_draws() {
        let mut deck = Deck::new();

        let mut rng = StdRng::seed_from_u64(42);
        deck.shuffle(&mut rng);

        let len = deck.cards.len();
        let mut drawn_cards: Vec<Option<Card>> = Vec::with_capacity(len);

        for _ in 0..len {
            drawn_cards.push(deck.draw());
        }

        let unique_cards: HashSet<_> = drawn_cards.iter().cloned().collect();

        assert_eq!(unique_cards.len(), len);
    }

    #[test]
    fn test_seeded_shuffle() {
        let mut deck1 = Deck::new();
        let mut deck2 = Deck::new();

        let mut rng = StdRng::seed_from_u64(42);
        deck1.shuffle(&mut rng);

        let mut rng = StdRng::seed_from_u64(42);
        deck2.shuffle(&mut rng);

        assert_eq!(deck1.cards, deck2.cards);
    }

}