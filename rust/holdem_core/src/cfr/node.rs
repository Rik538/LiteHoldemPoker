
use crate::actions::Action;

use bincode::{Encode, Decode};

const NUM_ACTIONS: usize = 5;

pub fn action_index(action: &Action) -> usize {
    match action {
        Action::Fold => 0,
        Action::Check => 1,
        Action::Call => 2,
        Action::Bet => 3,
        Action::Raise => 4,
    }
}

#[derive(Debug,  PartialEq,Encode, Decode, Clone)]
pub struct CFRNode {
    pub regret_sum: [f64; NUM_ACTIONS],
    pub strategy_sum: [f64; NUM_ACTIONS],
}

impl CFRNode {

    pub fn new () -> CFRNode {
        CFRNode { regret_sum: [0.0;NUM_ACTIONS], strategy_sum: [0.0;NUM_ACTIONS] }
    }

    pub fn get_strategy(&mut self,legal_actions: &[Option<Action>; 3],reach_probability: f64, accumulate_strategy: bool) 
     -> [f64; 5] {

        let mut strategy = [0.0; 5];
        let mut total_regret = 0.0;
        let mut legal_count = 0;

        for action in legal_actions.iter().flatten() {
            let idx = action_index(action);
            strategy[idx] = self.regret_sum[idx].max(0.0);
            total_regret += strategy[idx];
            legal_count += 1;
        }

        assert!(
            legal_count > 0,
            "CFRNode::get_strategy called without legal actions"
        );

        if total_regret > 0.0 {
            for probability in &mut strategy {
                *probability /= total_regret;
            }
        } else if legal_count > 0 {
            let probability = 1.0 / legal_count as f64;

            for action in legal_actions.iter().flatten() {
                strategy[action_index(action)] = probability;
            }
        }
    
        if accumulate_strategy {
            for action in legal_actions.iter().flatten() {
                let idx = action_index(action);
                self.strategy_sum[idx] += reach_probability * strategy[idx]
            }
        }

        strategy

    }

    
    pub fn get_average_strategy(
        &self,
        legal_actions: &[Option<Action>; 3],
    ) -> [f64; 5] {
        let mut avg_strategy = [0.0; 5];
        let mut total_strategy = 0.0;
        let mut legal_count = 0;

        for action in legal_actions.iter().flatten() {
            let idx = action_index(action);

            total_strategy += self.strategy_sum[idx];
            legal_count += 1;
        }

        assert!(
            legal_count > 0,
            "CFRNode::get_average_strategy called without legal actions"
        );

        if total_strategy > 0.0 {
            for action in legal_actions.iter().flatten() {
                let idx = action_index(action);

                avg_strategy[idx] =
                    self.strategy_sum[idx] / total_strategy;
            }
        } else {
            let probability = 1.0 / legal_count as f64;

            for action in legal_actions.iter().flatten() {
                let idx = action_index(action);

                avg_strategy[idx] = probability;
            }
        }

        avg_strategy
    }

    
}



#[cfg(test)]
mod tests {
    use super::*;

    // Floating-point comparison helper.
    fn assert_close(actual: f64, expected: f64) {
        assert!(
            (actual - expected).abs() < 1e-12,
            "Expected {expected}, got {actual}"
        );
    }

    fn facing_bet_actions() -> [Option<Action>; 3] {
        [
            Some(Action::Fold),
            Some(Action::Call),
            Some(Action::Raise),
        ]
    }

    fn checking_actions() -> [Option<Action>; 3] {
        [
            Some(Action::Check),
            Some(Action::Bet),
            None,
        ]
    }

    #[test]
    fn test_new_node_has_zero_values() {
        let node = CFRNode::new();

        assert_eq!(node.regret_sum, [0.0; 5]);
        assert_eq!(node.strategy_sum, [0.0; 5]);
    }

    #[test]
    fn test_positive_regret_matching() {
        let mut node = CFRNode::new();

        // Fold, Check, Call, Bet, Raise
        node.regret_sum = [6.0, 0.0, 4.0, 0.0, -3.0];

        let strategy =
            node.get_strategy(&facing_bet_actions(), 1.0, false);

        assert_close(strategy[0], 0.6);
        assert_close(strategy[1], 0.0);
        assert_close(strategy[2], 0.4);
        assert_close(strategy[3], 0.0);
        assert_close(strategy[4], 0.0);

        assert_close(strategy.iter().sum(), 1.0);
    }

    #[test]
    fn test_negative_regrets_use_uniform_strategy() {
        let mut node = CFRNode::new();

        node.regret_sum = [-5.0, 0.0, -2.0, 0.0, -10.0];

        let strategy =
            node.get_strategy(&facing_bet_actions(), 1.0, false);

        assert_close(strategy[0], 1.0 / 3.0);
        assert_close(strategy[1], 0.0);
        assert_close(strategy[2], 1.0 / 3.0);
        assert_close(strategy[3], 0.0);
        assert_close(strategy[4], 1.0 / 3.0);

        assert_close(strategy.iter().sum(), 1.0);
    }

    #[test]
    fn test_two_legal_actions() {
        let mut node = CFRNode::new();

        let strategy =
            node.get_strategy(&checking_actions(), 1.0, false);

        // Only Check and Bet are legal.
        assert_close(strategy[0], 0.0);
        assert_close(strategy[1], 0.5);
        assert_close(strategy[2], 0.0);
        assert_close(strategy[3], 0.5);
        assert_close(strategy[4], 0.0);

        assert_close(strategy.iter().sum(), 1.0);
    }

    #[test]
    fn test_illegal_actions_are_ignored() {
        let mut node = CFRNode::new();

        // Check and Bet have large positive regrets,
        // but they're illegal when facing a bet.
        node.regret_sum = [2.0, 100.0, 3.0, 100.0, 5.0];

        let strategy =
            node.get_strategy(&facing_bet_actions(), 1.0, false);

        assert_close(strategy[0], 0.2);
        assert_close(strategy[1], 0.0);
        assert_close(strategy[2], 0.3);
        assert_close(strategy[3], 0.0);
        assert_close(strategy[4], 0.5);

        assert_close(strategy.iter().sum(), 1.0);
    }

    #[test]
    fn test_strategy_accumulation_with_reach_probability() {
        let mut node = CFRNode::new();

        node.regret_sum = [3.0, 0.0, 1.0, 0.0, 0.0];

        let strategy =
            node.get_strategy(&facing_bet_actions(), 0.4, true);

        // Current strategy:
        // Fold = 0.75
        // Call = 0.25
        // Raise = 0.0

        assert_close(strategy[0], 0.75);
        assert_close(strategy[2], 0.25);

        // Accumulated strategy = reach * probability
        assert_close(node.strategy_sum[0], 0.4 * 0.75);
        assert_close(node.strategy_sum[1], 0.0);
        assert_close(node.strategy_sum[2], 0.4 * 0.25);
        assert_close(node.strategy_sum[3], 0.0);
        assert_close(node.strategy_sum[4], 0.0);

        assert_close(node.strategy_sum.iter().sum(), 0.4);
    }

    #[test]
    fn test_strategy_not_accumulated_when_disabled() {
        let mut node = CFRNode::new();

        node.regret_sum = [5.0, 0.0, 5.0, 0.0, 0.0];

        node.get_strategy(&facing_bet_actions(), 0.5, false);

        assert_eq!(node.strategy_sum, [0.0; 5]);
    }

    #[test]
    fn test_repeated_strategy_accumulation() {
        let mut node = CFRNode::new();

        // Uniform strategy across three legal actions.
        node.get_strategy(&facing_bet_actions(), 0.6, true);
        node.get_strategy(&facing_bet_actions(), 0.3, true);

        // Total reach weight = 0.9
        // Each action receives 0.9 / 3 = 0.3

        assert_close(node.strategy_sum[0], 0.3);
        assert_close(node.strategy_sum[1], 0.0);
        assert_close(node.strategy_sum[2], 0.3);
        assert_close(node.strategy_sum[3], 0.0);
        assert_close(node.strategy_sum[4], 0.3);

        assert_close(node.strategy_sum.iter().sum(), 0.9);
    }

    #[test]
    fn test_average_strategy_normalisation() {
        let mut node = CFRNode::new();

        // Fold, Check, Call, Bet, Raise
        node.strategy_sum = [20.0, 0.0, 60.0, 0.0, 20.0];

        let average =
            node.get_average_strategy(&facing_bet_actions());

        assert_close(average[0], 0.2);
        assert_close(average[1], 0.0);
        assert_close(average[2], 0.6);
        assert_close(average[3], 0.0);
        assert_close(average[4], 0.2);

        assert_close(average.iter().sum(), 1.0);
    }

    #[test]
    fn test_average_strategy_ignores_illegal_actions() {
        let mut node = CFRNode::new();

        node.strategy_sum = [10.0, 100.0, 30.0, 100.0, 10.0];

        let average =
            node.get_average_strategy(&facing_bet_actions());

        // Only Fold, Call and Raise are included.
        // Their total strategy weight is 50.

        assert_close(average[0], 0.2);
        assert_close(average[1], 0.0);
        assert_close(average[2], 0.6);
        assert_close(average[3], 0.0);
        assert_close(average[4], 0.2);

        assert_close(average.iter().sum(), 1.0);
    }

    #[test]
    fn test_average_strategy_uniform_fallback() {
        let node = CFRNode::new();

        let average =
            node.get_average_strategy(&checking_actions());

        // No accumulated strategy yet.
        // Only Check and Bet are legal.

        assert_close(average[0], 0.0);
        assert_close(average[1], 0.5);
        assert_close(average[2], 0.0);
        assert_close(average[3], 0.5);
        assert_close(average[4], 0.0);

        assert_close(average.iter().sum(), 1.0);
    }

    #[test]
    #[should_panic(expected = "called without legal actions")]
    fn test_average_strategy_rejects_no_legal_actions() {
        let node = CFRNode::new();

        node.get_average_strategy(&[None, None, None]);
    }
}
