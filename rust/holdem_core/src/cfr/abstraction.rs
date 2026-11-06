use crate::cards::Card;
use crate::state::Street;
use crate::evaluator::{build_context,HandContext};


const DEFAULT_STREET_THRESHOLDS: [[f64;4];4] = [
    [0.35, 0.45, 0.55, 0.65],
    [0.25, 0.40, 0.55, 0.70],
    [0.20, 0.35, 0.55, 0.75],
    [0.10, 0.30, 0.50, 0.75],
];


pub fn street_aware_equity_bucket(equity: f64,street:Street) -> u8 {
    equity_bucket(equity, DEFAULT_STREET_THRESHOLDS[street as usize])
}

pub fn equity_bucket(equity: f64, thresholds: [f64; 4]) -> u8 {
    // Port the exact Python equity thresholds
    for bucket in 0..thresholds.len() {
        if equity <= thresholds[bucket] {
            return bucket as u8;
        }
    }

    thresholds.len() as u8
}

pub fn pot_bucket(pot: i64) -> u8 {
    if pot <= 4{return 0
    } else if  pot <= 8{ return 1
    } else if  pot <= 16 { return 2
    } else { return 3}
}

pub fn texture_bucket(board_cards: &[Card]) -> u8 {
    if board_cards.len() < 3 {
        return 0;
    }

    let ctx : HandContext = build_context(&board_cards);
    

    let paired_board: u8 = ctx.ranks.iter().any(|&count|count >= 2) as u8;

    let flush_pressure: u8 = ctx.suits.iter().any(|&count| count >= 3) as u8;


    let straight_pressure: u8 = (ctx.ranks.iter().filter(|&&count| count > 0).count() >= 3) as u8;

    return paired_board + 2 * flush_pressure + 4 * straight_pressure
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::cards::{Rank,Suit,Card};

    #[test]
    fn test_equity_bucket() {

        let equity: f64 = 0.47;
        let thresholds: [f64; 4] = [0.35, 0.45, 0.55, 0.65];

        let bucket = equity_bucket(equity, thresholds);

        assert_eq!(bucket,2);

    }
    
    #[test]
    fn test_pot_bucket() {
        let pot = 6;

        let bucket = pot_bucket(pot);
        
        assert_eq!(bucket,1);

    }

    #[test]
    fn test_street_equity_bucket() {
        let equity = 0.42;
        let street = Street::Turn;

        let mut bucket = street_aware_equity_bucket(equity, street);

        assert_eq!(bucket,2);

        bucket = street_aware_equity_bucket(equity, Street::Preflop);


        assert_eq!(bucket,1)
    }

    #[test]
    fn test_board_texture() {

        //3 different ranks
        let mut board_cards = [
            Card {
                rank: Rank::Jack,
                suit: Suit::Heart,
            },
            Card {
                rank: Rank::Queen,
                suit: Suit::Spade,
            },
            Card {
                rank: Rank::Ace,
                suit: Suit::Spade,
            },
        ];

        assert_eq!(texture_bucket(&board_cards),4);

        //Pair
        board_cards = [
            Card {
                rank: Rank::Jack,
                suit: Suit::Heart,
            },
            Card {
                rank: Rank::Jack,
                suit: Suit::Spade,
            },
            Card {
                rank: Rank::Ace,
                suit: Suit::Spade,
            },
        ];

        assert_eq!(texture_bucket(&board_cards),1);
        
        //Flush potential and 3 different ranks
        board_cards = [
            Card {
                rank: Rank::Ten,
                suit: Suit::Spade,
            },
            Card {
                rank: Rank::Jack,
                suit: Suit::Spade,
            },
            Card {
                rank: Rank::Ace,
                suit: Suit::Spade,
            },
        ];

        assert_eq!(texture_bucket(&board_cards),6);




    }

}