use crate::evaluator::{evaluate_hand};
use crate::cards::{Card,Suit,Rank};



pub fn evaluate_python_hand(card_array: &[u8; 7]) -> (u8, [u8; 5]) {
    let suits = [Suit::Club, Suit::Diamond, Suit::Heart, Suit::Spade];
    let ranks = Rank::ALL;

    let cards: [Card; 7] = std::array::from_fn(|i| {
        let value = card_array[i] as usize;

        Card {
            suit: suits[value % suits.len()],
            rank: ranks[value / suits.len()],
        }
    });

    let private_cards: [Card; 2] = [cards[0], cards[1]];
    let public_cards: [Card; 5] =
        std::array::from_fn(|i| cards[i + 2]);

    let result = evaluate_hand(private_cards, public_cards);

    (result.category as u8, result.kickers)
}

pub fn evaluate_python_hand_from_csv(csv_path: &str) -> (usize, usize) {

    let mut reader = csv::Reader::from_path(csv_path).unwrap();

    let mut matches = 0;
    let mut mismatches = 0;

    for result in reader.records(){
        let record = result.unwrap();

        let card_ids: [u8; 7] =
        std::array::from_fn(|i| record[i].parse().unwrap());

        let python_category = record[7].parse::<u8>().unwrap();
        let python_kickers: [u8; 5] = std::array::from_fn(|i| record[8 + i].parse().unwrap());

        let evaluator_result = evaluate_python_hand(&card_ids);
        let evaluator_category = evaluator_result.0;
        let evaluator_kickers = evaluator_result.1;

        if python_category == evaluator_category && python_kickers == evaluator_kickers {
            matches += 1;
        } else {
            mismatches += 1;

            if mismatches <= 10 {
                println!("Mismatch for cards: {:?}", card_ids);
                println!(
                    "Python: {} {:?}",
                    python_category, python_kickers
                );
                println!(
                    "Rust:   {} {:?}",
                    evaluator_category, evaluator_kickers
                );
            }
        }


    }
    (matches, mismatches)
}

#[test]
fn test_python_evaluator_equivalence() {
    let (matches, mismatches) =
        evaluate_python_hand_from_csv("/home/richard.dunbar101/Projects/LiteHoldemPoker/benchmarks/evaluator_reference.csv");

    assert_eq!(matches, 77_520);
    assert_eq!(mismatches, 0);
}