use crate::state::{GameState,Street, MAX_RAISES_THIS_ROUND};
use crate::actions::Action;
use rand::Rng;

//small helpers
impl GameState {
    pub fn amount_to_call(&self, player:usize) -> i64 {
        self.round_bets[0].max(self.round_bets[1])- self.round_bets[player]
    }

    pub fn bet_size(&self) -> i64 {
        match self.street{
            Street::Preflop => 2,
            Street::Flop => 2,
            Street::River => 4,
            Street::Turn => 4,
        }
        
    }
}

//resetting/starting 
impl GameState {
    pub fn reset(&mut self) {
        *self = GameState::new();
    }

    pub fn start_hand<R: Rng + ?Sized>(&mut self, rng: &mut R) {
        // Hand initialisation logic
        // reset state and shuffle
        self.reset();
        self.deck.shuffle(rng);

        let big_blind_player = 1- self.button_player;
        

        // deal 2 cards to each player
        for player in [0, 1] {
            let hand = [
                self.deck.draw().unwrap(),
                self.deck.draw().unwrap(),
            ];
            self.player_cards[player] = Some(hand);
        }

        self.round_bets[self.button_player] += self.small_blind;
        self.round_bets[big_blind_player] += self.big_blind;

        self.player_contributions[self.button_player] += self.small_blind;
        self.player_contributions[big_blind_player] += self.big_blind;

        self.pot = self.big_blind + self.small_blind;

        self.current_player = self.button_player;

    }
}


//getting legal moves
impl GameState {
    pub fn legal_actions(&self) -> [Option<Action>; 3] {
        if self.terminal {
            return [None, None, None];
        }

        let to_call = self.amount_to_call(self.current_player);
        let can_raise = self.raises_this_round < MAX_RAISES_THIS_ROUND;

        if to_call > 0 {
            if can_raise {
                [Some(Action::Fold), Some(Action::Call), Some(Action::Raise)]
            } else {
                [Some(Action::Fold), Some(Action::Call), None]
            }
        } else {
            if can_raise {
                [Some(Action::Check), Some(Action::Bet), None]
            } else {
                [Some(Action::Check), None, None]
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::actions::Action;
    use crate::state::{Street, ActionRecord};
    use rand::rngs::StdRng;
    use rand::SeedableRng;
    use std::collections::HashSet;


    #[test]
    fn test_start_hand_deals_cards() {
        let mut rng = StdRng::seed_from_u64(42);
        let mut state = GameState::new();

        state.start_hand(&mut rng);

        // Both players have two cards
        assert!(state.player_cards[0].is_some());
        assert!(state.player_cards[1].is_some());

        // Four cards dealt, sixteen remaining
        assert_eq!(state.deck.remaining(), 16);

        // No community cards yet
        assert!(state.public_cards.is_empty());

        assert_eq!(state.street, Street::Preflop);
    }

    #[test]
    fn test_start_hand_unique_cards() {
        let mut rng = StdRng::seed_from_u64(42);
        let mut state = GameState::new();

        state.start_hand(&mut rng);

        let unique_cards: HashSet<_> = state.player_cards
            .iter()
            .flatten()
            .flat_map(|hand| hand.iter().copied())
            .collect();

        // All four dealt cards must be different
        assert_eq!(unique_cards.len(), 4);
    }

    #[test]
    fn test_start_hand_blinds() {
        let mut rng = StdRng::seed_from_u64(42);
        let mut state = GameState::new();

        state.start_hand(&mut rng);

        // Pot contains both blinds
        assert_eq!(
            state.pot,
            state.small_blind + state.big_blind
        );

        // The button posts the small blind
        let expected_bets = if state.button_player == 0 {
            [state.small_blind, state.big_blind]
        } else {
            [state.big_blind, state.small_blind]
        };

        assert_eq!(state.player_contributions, expected_bets);
        assert_eq!(state.round_bets, expected_bets);

        // In heads-up poker, button acts first preflop
        assert_eq!(state.current_player, state.button_player);
    }

    #[test]
    fn test_start_hand_reset() {
        let mut rng = StdRng::seed_from_u64(42);
        let mut state = GameState::new();

        state.start_hand(&mut rng);

        // Simulate state left over from a previous hand
        state.pot = 100;
        state.player_contributions = [50, 50];
        state.round_bets = [20, 20];
        state.raises_this_round = 2;
        state.terminal = true;
        state.folded_player = Some(0);
        state.payoffs = [-50.0, 50.0];

        state.actions_this_round.push(Action::Check);

        state.action_history.push(ActionRecord {
            player: 0,
            street: Street::Preflop,
            action: Action::Check,
            to_call: 0,
        });

        state.public_cards.push(
            state.player_cards[0].unwrap()[0]
        );

        // Start another hand
        state.start_hand(&mut rng);

        // Check the old state was cleared
        assert!(!state.terminal);
        assert_eq!(state.folded_player, None);
        assert_eq!(state.raises_this_round, 0);
        assert!(state.action_history.is_empty());
        assert!(state.actions_this_round.is_empty());
        assert!(state.public_cards.is_empty());
        assert_eq!(state.payoffs, [0.0, 0.0]);

        // Check that a fresh hand was dealt
        assert!(state.player_cards.iter().all(Option::is_some));
        assert_eq!(state.deck.remaining(), 16);

        // Check the blinds were posted again
        assert_eq!(
            state.pot,
            state.small_blind + state.big_blind
        );

        assert_eq!(
            state.player_contributions,
            state.round_bets
        );
    }

    #[test]
    fn test_amount_to_call() {
        let mut state = GameState::new();

        state.round_bets = [2, 4];

        let mut player:usize = 0;
        assert_eq!(state.amount_to_call(player), 2);

        player = 1;
        assert_eq!(state.amount_to_call(player), 0);
    }

    #[test]
    fn test_legal_actions_preflop() {
        let mut rng = StdRng::seed_from_u64(42);
        let mut state = GameState::new();

        state.start_hand(&mut rng);

        // Small blind must call, raise or fold
        assert_eq!(
            state.legal_actions(),
            [
                Some(Action::Fold),
                Some(Action::Call),
                Some(Action::Raise),
            ]
        );
    }

    #[test]
    fn test_legal_actions_no_bet() {
        let mut state = GameState::new();

        state.round_bets = [0, 0];
        state.raises_this_round = 0;

        assert_eq!(
            state.legal_actions(),
            [
                Some(Action::Check),
                Some(Action::Bet),
                None,
            ]
        );
    }

    #[test]
    fn test_legal_actions_raise_limit() {
        let mut state = GameState::new();

        state.round_bets = [2, 4];
        state.current_player = 0;
        state.raises_this_round = MAX_RAISES_THIS_ROUND;

        assert_eq!(
            state.legal_actions(),
            [
                Some(Action::Fold),
                Some(Action::Call),
                None,
            ]
        );
    }

    #[test]
    fn test_legal_actions_no_bet_raise_limit() {
        let mut state = GameState::new();

        state.round_bets = [0, 0];
        state.raises_this_round = MAX_RAISES_THIS_ROUND;

        assert_eq!(
            state.legal_actions(),
            [
                Some(Action::Check),
                None,
                None,
            ]
        );
    }

    #[test]
    fn test_legal_actions_terminal() {
        let mut state = GameState::new();

        state.terminal = true;

        assert_eq!(
            state.legal_actions(),
            [None, None, None]
        );
    }
}