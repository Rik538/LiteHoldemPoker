use crate::cards::Card;
use crate::evaluator::{evaluate_hand,HandValue};
use crate::deck::Deck;

#[derive(Debug, Default, Clone, Copy, PartialEq, Eq)]
pub struct EquityResult {
    pub(crate) wins: u32,
    pub(crate) losses: u32,
    pub(crate) splits: u32,
    pub(crate) total: u32,
}

impl EquityResult {
    pub fn equity(&self) -> f64 {
        if self.total == 0 {
            return 0.0;
        }

        (self.wins as f64 + self.splits as f64 * 0.5)
            / self.total as f64
    }
}

impl EquityResult {
    pub fn counts(&self) -> (u32, u32, u32, u32) {
        (self.wins, self.losses, self.splits, self.total)
    }
}

pub fn calculate_equity(player_cards: &[Card], public_cards: &[Card]) -> f64 {
    // Implementation for calculating equity



    let player_cards_arr: [Card; 2] = player_cards
            .try_into()
            .expect("player_cards must contain exactly 2 cards");


    let result: EquityResult = match public_cards.len() {
        0 => preflop_equity(&player_cards_arr),
        3 => flop_equity(&player_cards_arr, &public_cards.try_into().unwrap()),
        4 => turn_equity(&player_cards_arr, &public_cards.try_into().unwrap()),
        5 => river_equity(&player_cards_arr, &public_cards.try_into().unwrap(), None),
        _ => panic!("Invalid number of public cards"),
    };

    result.equity()
}

pub fn calculate_equity_result(player_cards: &[Card], public_cards: &[Card]) -> EquityResult {
    // Implementation for calculating equity



    let player_cards_arr: [Card; 2] = player_cards
            .try_into()
            .expect("player_cards must contain exactly 2 cards");


    let result: EquityResult = match public_cards.len() {
        0 => preflop_equity(&player_cards_arr),
        3 => flop_equity(&player_cards_arr, &public_cards.try_into().unwrap()),
        4 => turn_equity(&player_cards_arr, &public_cards.try_into().unwrap()),
        5 => river_equity(&player_cards_arr, &public_cards.try_into().unwrap(), None),
        _ => panic!("Invalid number of public cards"),
    };

    result

}



pub fn preflop_equity(player_cards: &[Card; 2],
) -> EquityResult {
    // Implementation for calculating turn equity
    // This function should calculate the equity of the player's hand given their cards and the public cards on the turn.

    
    let known_cards: [Card; 2] = [
        player_cards[0],
        player_cards[1],
    ];

    let mut preflop_equity_result = EquityResult::default();

    let remaining_deck: [Card; 18] = get_remaining_cards(known_cards).unwrap();

    for i in 0..remaining_deck.len() {
        for j in (i + 1)..remaining_deck.len() {
            for k in (j + 1)..remaining_deck.len() {
                for l in (k + 1)..remaining_deck.len() {
                    for m in (l + 1)..remaining_deck.len() {
                        let turn_public_cards = [
                            remaining_deck[i],
                            remaining_deck[j],
                            remaining_deck[k],
                            remaining_deck[l],
                            remaining_deck[m],
                        ];

                        // Evaluate both hands
                        let previous_result = preflop_equity_result;
                        preflop_equity_result = river_equity(player_cards, &turn_public_cards, Some(previous_result));
                    }
                }
            }
        }
    }


    

    preflop_equity_result
}


pub fn flop_equity(player_cards: &[Card; 2],
    public_cards: &[Card; 3],
) -> EquityResult {
    // Implementation for calculating turn equity
    // This function should calculate the equity of the player's hand given their cards and the public cards on the turn.

    let known_cards: [Card; 5] = [
        player_cards[0],
        player_cards[1],
        public_cards[0],
        public_cards[1],
        public_cards[2],
    ];

    let mut flop_equity_result = EquityResult::default();

    let remaining_deck: [Card; 15] = get_remaining_cards(known_cards).unwrap();

    for i in 0..remaining_deck.len() {
        for j in (i + 1)..remaining_deck.len() {
            // Evaluate one completed board
            let turn_public_cards: [Card; 5] = [
            public_cards[0],
            public_cards[1],
            public_cards[2],
            remaining_deck[i],
            remaining_deck[j],
        ];

        let previous_result = flop_equity_result;
        flop_equity_result = river_equity(player_cards, &turn_public_cards, Some(previous_result));
        }
    }


    

    flop_equity_result
}




pub fn turn_equity(player_cards: &[Card; 2],
    public_cards: &[Card; 4],
) -> EquityResult {
    // Implementation for calculating turn equity
    // This function should calculate the equity of the player's hand given their cards and the public cards on the turn.

    let known_cards: [Card; 6] = [
        player_cards[0],
        player_cards[1],
        public_cards[0],
        public_cards[1],
        public_cards[2],
        public_cards[3],
    ];

    let mut turn_equity_result = EquityResult::default();

    let remaining_deck: [Card; 14] = get_remaining_cards(known_cards).unwrap();

    for i in 0..remaining_deck.len() {
        let turn_public_cards: [Card; 5] = [
            public_cards[0],
            public_cards[1],
            public_cards[2],
            public_cards[3],
            remaining_deck[i],
        ];

        let previous_result = turn_equity_result;
        turn_equity_result = river_equity(player_cards, &turn_public_cards, Some(previous_result));
    }

    

    turn_equity_result
}


pub fn river_equity(
    player_cards: &[Card; 2],
    public_cards: &[Card; 5],
    previous_result: Option<EquityResult>,
) -> EquityResult {

    let known_cards: [Card; 7] = [
        player_cards[0],
        player_cards[1],
        public_cards[0],
        public_cards[1],
        public_cards[2],
        public_cards[3],
        public_cards[4],
    ];

    let mut river_equity_result = previous_result.unwrap_or_default();

    let remaining_deck: [Card; 13] = get_remaining_cards(known_cards).unwrap();

    let own_hand: HandValue = evaluate_hand(
            *player_cards,
            *public_cards,
        );

    for i in 0..remaining_deck.len() {
        for j in (i + 1)..remaining_deck.len() {
            let opponent_cards = [
                remaining_deck[i],
                remaining_deck[j],
            ];

            // Compare the two hands
            resolve_showdown(own_hand, *public_cards, opponent_cards, &mut river_equity_result);
        }
    }

    river_equity_result
}

pub fn get_remaining_cards<const M: usize, const K: usize>(
    known_cards: [Card; M],
) -> Option<[Card; K]> {
    let full_deck = Deck::new().cards;

    if full_deck.len().checked_sub(M) != Some(K) {
        return None;
    }

    let mut removed = [false; 20];

    for value in known_cards {
        let index = full_deck
            .iter()
            .enumerate()
            .position(|(i, x)| !removed[i] && *x == value)?;

        removed[index] = true;
    }

    let mut index = 0;

    Some(std::array::from_fn(|_| {
        while removed[index] {
            index += 1;
        }

        let card = full_deck[index];
        index += 1;
        card
    }))
}


pub fn resolve_showdown(own_hand: HandValue, 
                        public_cards: [Card; 5], 
                        opponent_cards: [Card; 2],
                        river_equity_result: &mut EquityResult) 
    {



        let opponent_hand: HandValue = evaluate_hand(
            opponent_cards,
            public_cards,
        );

        match own_hand.cmp(&opponent_hand) {
            std::cmp::Ordering::Greater => {
                // Player wins
                river_equity_result.wins += 1;

            }
            std::cmp::Ordering::Less => {
                // Opponent wins
                river_equity_result.losses += 1;

            }
            std::cmp::Ordering::Equal => {
                // It's a tie
                river_equity_result.splits += 1;
            }
        }

        river_equity_result.total += 1;



}






















#[cfg(test)]
mod tests {
    use super::*;
    use crate::cards::{Card, Rank, Suit};


    #[test]
    fn test_get_remaining_cards() {
        let known_cards = [
            Card {
                rank: Rank::Ace,
                suit: Suit::Heart,
            },
            Card {
                rank: Rank::King,
                suit: Suit::Diamond,
            },
        ];

        let remaining_cards: [Card; 18] = get_remaining_cards(known_cards).unwrap();

        assert_eq!(remaining_cards.len(), 18);
        assert!(!remaining_cards.contains(&known_cards[0]));
        assert!(!remaining_cards.contains(&known_cards[1]));
    }

    #[test]
    fn test_river_equity() {
        let player_cards = [
            Card {
                rank: Rank::Ace,
                suit: Suit::Heart,
            },
            Card {
                rank: Rank::King,
                suit: Suit::Diamond,
            },
        ];

        let public_cards = [
            Card {
                rank: Rank::Queen,
                suit: Suit::Spade,
            },
            Card {
                rank: Rank::Jack,
                suit: Suit::Club,
            },
            Card {
                rank: Rank::Ten,
                suit: Suit::Heart,
            },
            Card {
                rank: Rank::Ten,
                suit: Suit::Diamond,
            },
            Card {
                rank: Rank::Ace,
                suit: Suit::Spade,
            },
        ];

        let equity_result = river_equity(&player_cards, &public_cards, None);



        assert_eq!(equity_result.wins, 21);
        assert_eq!(equity_result.losses, 24);
        assert_eq!(equity_result.splits, 33);
        assert_eq!(equity_result.total, 78);
    }

    #[test]
    fn test_river_equity_score() {
        let player_cards = [
            Card {
                rank: Rank::Ace,
                suit: Suit::Heart,
            },
            Card {
                rank: Rank::King,
                suit: Suit::Diamond,
            },
        ];

        let public_cards = [
            Card {
                rank: Rank::Queen,
                suit: Suit::Spade,
            },
            Card {
                rank: Rank::Jack,
                suit: Suit::Club,
            },
            Card {
                rank: Rank::Ten,
                suit: Suit::Heart,
            },
            Card {
                rank: Rank::Ten,
                suit: Suit::Diamond,
            },
            Card {
                rank: Rank::Ace,
                suit: Suit::Spade,
            },
        ];

        let equity_result = calculate_equity(&player_cards, &public_cards);

        assert_eq!((equity_result * 10_000.0).round() / 10_000.0, 0.4808);
    }

    #[test]
    fn test_turn_equity() {
        let player_cards = [
            Card {
                rank: Rank::Ace,
                suit: Suit::Heart,
            },
            Card {
                rank: Rank::King,
                suit: Suit::Diamond,
            },
        ];

        let public_cards = [
            Card {
                rank: Rank::Queen,
                suit: Suit::Spade,
            },
            Card {
                rank: Rank::Jack,
                suit: Suit::Club,
            },
            Card {
                rank: Rank::Ten,
                suit: Suit::Heart,
            },
            Card {
                rank: Rank::Ten,
                suit: Suit::Diamond,
            },
        ];

        let equity_result = turn_equity(&player_cards, &public_cards);

        assert_eq!(equity_result.wins, 270);
        assert_eq!(equity_result.losses, 552);
        assert_eq!(equity_result.splits, 270);
        assert_eq!(equity_result.total, 1092);

    }

    #[test]
    fn test_turn_equity_score() {
        let player_cards = [
            Card {
                rank: Rank::Ace,
                suit: Suit::Heart,
            },
            Card {
                rank: Rank::King,
                suit: Suit::Diamond,
            },
        ];

        let public_cards = [
            Card {
                rank: Rank::Queen,
                suit: Suit::Spade,
            },
            Card {
                rank: Rank::Jack,
                suit: Suit::Club,
            },
            Card {
                rank: Rank::Ten,
                suit: Suit::Heart,
            },
            Card {
                rank: Rank::Ten,
                suit: Suit::Diamond,
            },
        ];

        let equity_result = calculate_equity(&player_cards, &public_cards);

        assert_eq!((equity_result * 10_000.0).round() / 10_000.0, 0.3709);
    }


    #[test]
    fn test_flop_equity() {
        let player_cards = [
            Card {
                rank: Rank::Ace,
                suit: Suit::Heart,
            },
            Card {
                rank: Rank::King,
                suit: Suit::Diamond,
            },
        ];

        let public_cards = [
            Card {
                rank: Rank::Queen,
                suit: Suit::Spade,
            },
            Card {
                rank: Rank::Jack,
                suit: Suit::Club,
            },
            Card {
                rank: Rank::Ten,
                suit: Suit::Heart,
            },
        ];

        let equity_result = flop_equity(&player_cards, &public_cards);

        assert_eq!(equity_result.wins, 1944);
        assert_eq!(equity_result.losses, 3252);
        assert_eq!(equity_result.splits, 2994);
        assert_eq!(equity_result.total, 8190);


    }

    #[test]
    fn test_flop_equity_score() {
        let player_cards = [
            Card {
                rank: Rank::Ace,
                suit: Suit::Heart,
            },
            Card {
                rank: Rank::King,
                suit: Suit::Diamond,
            },
        ];

        let public_cards = [
            Card {
                rank: Rank::Queen,
                suit: Suit::Spade,
            },
            Card {
                rank: Rank::Jack,
                suit: Suit::Club,
            },
            Card {
                rank: Rank::Ten,
                suit: Suit::Heart,
            },
        ];

        let equity_result = calculate_equity(&player_cards, &public_cards);

        assert_eq!((equity_result * 10_000.0).round() / 10_000.0, 0.4201);
    }


    #[test]
    fn test_preflop_equity() {
        let player_cards = [
            Card {
                rank: Rank::Ace,
                suit: Suit::Heart,
            },
            Card {
                rank: Rank::King,
                suit: Suit::Diamond,
            },
        ];


        let equity_result = preflop_equity(&player_cards);



        assert_eq!(equity_result.wins, 286899);
        assert_eq!(equity_result.losses, 219102);
        assert_eq!(equity_result.splits, 162303);
        assert_eq!(equity_result.total, 668304);

    }
    
    #[test]
    fn test_preflop_equity_score() {
        let player_cards = [
            Card {
                rank: Rank::Ace,
                suit: Suit::Heart,
            },
            Card {
                rank: Rank::King,
                suit: Suit::Diamond,
            },
        ];

        

        let equity_result = calculate_equity(&player_cards, &[]);

        assert_eq!((equity_result * 10_000.0).round() / 10_000.0, 0.5507);
    }


}

