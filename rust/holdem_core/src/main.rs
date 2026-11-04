use rand::rngs::StdRng;
use rand::SeedableRng;
use holdem_core::actions::Action;

fn main() {


    use holdem_core::state::GameState;

    use holdem_core::python_evaluator::{evaluate_python_hand, evaluate_python_hand_from_csv};

    let cards = [0, 1, 2, 3, 4, 5, 6];

    evaluate_python_hand(&cards);
    let (matches, mismatches) = evaluate_python_hand_from_csv("/home/richard.dunbar101/Projects/LiteHoldemPoker/benchmarks/evaluator_reference.csv");
    println!("Matches: {}", matches);
    println!("Mismatches: {}", mismatches);

    







}
