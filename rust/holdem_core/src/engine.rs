use crate::state::{GameState,Street, MAX_RAISES_THIS_ROUND, ActionRecord};
use crate::actions::Action;
use rand::Rng;
use crate::errors::GameError;
use crate::evaluator::{evaluate_hand,HandValue};
use crate::observed_state::ObservedState;

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

    fn is_round_over(&self) -> bool {
        if self.terminal {
            return true;
        }

        if self.actions_this_round.len() >= 2 && self.round_bets[0] == self.round_bets[1] {
            return true;
        }

        false
    }
}

//resetting/starting 
impl GameState {
    pub fn reset(&mut self) {
        let prev_hands = self.hand_number;
        *self = GameState::new();
        self.button_player = prev_hands % 2;
        self.hand_number = prev_hands;
    }

    pub fn start_hand<R: Rng + ?Sized>(&mut self, rng: &mut R) -> Result<(), GameError>{
        // Hand initialisation logic
        // reset state and shuffle
        self.reset();
        self.hand_number += 1;
        self.deck.shuffle(rng);



        let big_blind_player = 1- self.button_player;

        if self.deck.remaining() < 4 {
            return Err(GameError::DeckExhausted);
        }
        

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

        Ok(())

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

//applying move
impl GameState {
    pub fn apply_action(&mut self, action: Action) -> Result<(), GameError> {
        if self.terminal {
            return Err(GameError::GameAlreadyTerminal);
        }

        if !self.legal_actions().contains(&Some(action)) {
            return Err(GameError::IllegalAction(action));
        }

        let player = self.current_player;
        let street = self.street;
        let to_call = self.amount_to_call(player);

        self.actions_this_round.push(action);

        self.action_history.push(ActionRecord {
            player,
            street,
            action,
            to_call,
        });

        match action {
            Action::Check => {},
            Action::Fold => self.apply_fold(),
            Action::Call => self.apply_call(),
            Action::Bet => self.apply_bet(),
            Action::Raise => self.apply_raise(),
        }

        

        if self.terminal {
            return Ok(());
        }

        if self.is_round_over() {

            self.advance_round()?;
        } else {
            self.current_player = 1-self.current_player;
        }

        Ok(())

    }

    fn advance_round(&mut self) -> Result<(), GameError> {

        self.round_bets = [0,0];
        self.actions_this_round.clear();
        self.raises_this_round = 0;

        match self.street {
            Street::Preflop => {
                self.deal_flop()?;
                self.street = Street::Flop;
            }
            Street::Flop => {
                self.deal_turn()?;
                self.street = Street::Turn;
            }
            Street::Turn => {
                self.deal_river()?;
                self.street = Street::River;
            }
            Street::River => {
                self.resolve_showdown()?;
                return Ok(());
            }
        }

        self.current_player = 1 - self.button_player;

        Ok(())
    }

    fn apply_fold (&mut self) {

        let folded_player = self.current_player;
        self.folded_player = Some(folded_player);
        let opponent = 1 - folded_player;

        self.payoffs[opponent] = self.pot as f64 - self.player_contributions[opponent] as f64;
        self.payoffs[folded_player] = -(self.player_contributions[folded_player] as f64);

        self.terminal = true;
    }

    fn apply_bet (&mut self){

        let bet_amount = self.bet_size();
        let player = self.current_player;
        
        self.round_bets[player] += bet_amount;
        self.player_contributions[player] += bet_amount;

        self.pot += bet_amount;
        self.raises_this_round += 1;

    }

    fn apply_raise (&mut self){
        let player = self.current_player;
        let bet_amount = self.bet_size() + self.amount_to_call(player);
        
        self.round_bets[player] += bet_amount;
        self.player_contributions[player] += bet_amount;

        self.pot += bet_amount;
        self.raises_this_round += 1;

    }

    fn apply_call (&mut self) {
        let player = self.current_player;
        let bet_amount = self.amount_to_call(player);
        
        self.round_bets[player] += bet_amount;
        self.player_contributions[player] += bet_amount;

        self.pot += bet_amount;        
    }
}

//Card dealing
impl GameState {
    fn deal_flop(&mut self) -> Result<(), GameError>{

        if self.public_cards.len() != 0 { return Err(GameError::InvalidPublicCards(self.public_cards.len()));}

        if self.deck.remaining() < 3 {
            return Err(GameError::DeckExhausted);
        }

        for _ in 0..3 {
            let card = self.deck.draw().ok_or(GameError::DeckExhausted)?;
            self.public_cards.push(card);
        }

        Ok(())
    }

    fn deal_turn(&mut self) -> Result<(), GameError>{
        if self.public_cards.len() != 3 { return Err(GameError::InvalidPublicCards(self.public_cards.len()));}
        
        let card = self.deck.draw().ok_or(GameError::DeckExhausted)?;
        self.public_cards.push(card);
        Ok(())

    }

    fn deal_river(&mut self) -> Result<(), GameError>{
        if self.public_cards.len() != 4 { return Err(GameError::InvalidPublicCards(self.public_cards.len()));}
        
        let card = self.deck.draw().ok_or(GameError::DeckExhausted)?;
        self.public_cards.push(card);
        Ok(())

    }


}


impl GameState {
    pub fn resolve_showdown(&mut self) -> Result<(), GameError> {
        if self.public_cards.len() != 5 {
            return Err(GameError::InvalidPublicCards(self.public_cards.len()));
        }

        let public_cards: [crate::cards::Card; 5] = self.public_cards.as_slice().try_into().unwrap();

        let player0_cards = self.player_cards[0].ok_or(GameError::MissingPlayerCards(0))?;

        let player1_cards = self.player_cards[1].ok_or(GameError::MissingPlayerCards(1))?;

        let player0_hand: HandValue = evaluate_hand(
            player0_cards,
            public_cards,
        );

        let player1_hand: HandValue = evaluate_hand(
            player1_cards,
            public_cards,
        );

        match player0_hand.cmp(&player1_hand) {
            std::cmp::Ordering::Greater => {
                // Player 0 wins
                self.payoffs[0] = self.pot as f64 - self.player_contributions[0] as f64;
                self.payoffs[1] = -(self.player_contributions[1] as f64);

            }
            std::cmp::Ordering::Less => {
                // Player 1 wins
                self.payoffs[1] = self.pot as f64 - self.player_contributions[1] as f64;
                self.payoffs[0] = -(self.player_contributions[0] as f64);
            }
            std::cmp::Ordering::Equal => {
                let split_amount = self.pot as f64 / 2.0;

                self.payoffs[0] =
                    split_amount - self.player_contributions[0] as f64;

                self.payoffs[1] =
                    split_amount - self.player_contributions[1] as f64;
            }
        }

        self.terminal = true;

        Ok(())
    }
}



impl GameState {
    pub fn get_observation(&self, &player: &usize) -> Option<ObservedState<'_>> {
        let private_cards = *self.player_cards.get(player)?.as_ref()?;

        Some(ObservedState {
            current_player: self.current_player,
            player,
            private_cards,
            public_cards: &self.public_cards,
            street: self.street,
            pot: self.pot,
            button_player: self.button_player,
            amount_to_call: self.amount_to_call(player),
            raises_this_round: self.raises_this_round,
            legal_actions: if self.current_player == player {
                self.legal_actions()
            } else {
                [None, None, None]
            },
        })
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
    use crate::cards::{Card, Rank, Suit};

    fn started_hand() -> GameState {
        let mut rng = StdRng::seed_from_u64(42);
        let mut state = GameState::new();
        state.start_hand(&mut rng).unwrap();
        state
    }

    fn reach_flop(state: &mut GameState) {
        state.apply_action(Action::Call).unwrap();
        state.apply_action(Action::Check).unwrap();
    }

    #[test]
    fn integration_test() {
        let mut rng = StdRng::seed_from_u64(42);
        let mut state = GameState::new();

        state.start_hand(&mut rng).expect("failed to start hand");

        state.apply_action(Action::Call).expect("failed to call");

        state.apply_action(Action::Check).expect("failed to check");

        state.apply_action(Action::Check).expect("failed to check");

        state.apply_action(Action::Check).expect("failed to check");

        state.apply_action(Action::Check).expect("failed to check");

        state.apply_action(Action::Check).expect("failed to check");

        state.apply_action(Action::Check).expect("failed to check");

        state.apply_action(Action::Check).expect("failed to check");

        println!("{:?}",state);
    }




    #[test]
    fn test_start_hand_deals_cards() {
        let mut rng = StdRng::seed_from_u64(42);
        let mut state = GameState::new();

        state.start_hand(&mut rng).unwrap();

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

        state.start_hand(&mut rng).unwrap();

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

        state.start_hand(&mut rng).unwrap();

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

        state.start_hand(&mut rng).unwrap();

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
        state.start_hand(&mut rng).unwrap();

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

        state.start_hand(&mut rng).unwrap();

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

    #[test]
    fn test_illegal_action() {
        let mut state = GameState::new();

        // Calling is illegal when there is no outstanding bet
        let original_state = format!("{:?}", state);

        let result = state.apply_action(Action::Call);

        // Check correct error is returned
        assert_eq!(
            result,
            Err(GameError::IllegalAction(Action::Call))
        );

        // Check state hasn't changed
        assert_eq!(format!("{:?}", state), original_state);
    }

    #[test]
    fn test_action_when_terminal() {
        let mut state = GameState::new();

        // Create a state where calling would otherwise be legal
        state.round_bets = [1, 2];
        state.current_player = 0;
        state.terminal = true;

        let original_state = format!("{:?}", state);

        let result = state.apply_action(Action::Call);

        // Check terminal-state error takes priority
        assert_eq!(
            result,
            Err(GameError::GameAlreadyTerminal)
        );

        // Check state hasn't changed
        assert_eq!(format!("{:?}", state), original_state);
    }

    #[test]
    fn test_apply_fold() {
        let mut state = GameState::new();

        state.current_player = 0;
        state.pot = 15;
        state.player_contributions = [5, 10];

        state.apply_fold();

        assert!(state.terminal);
        assert_eq!(state.folded_player, Some(0));
        assert_eq!(state.payoffs, [-5.0, 5.0]);
        assert_eq!(state.payoffs.iter().sum::<f64>(), 0.0);
    }


    #[test]
    fn test_bet_size_by_street() {
        let mut state = GameState::new();

        for (street, expected) in [
            (Street::Preflop, 2),
            (Street::Flop, 2),
            (Street::Turn, 4),
            (Street::River, 4),
        ] {
            state.street = street;
            assert_eq!(state.bet_size(), expected);
        }
    }

    #[test]
    fn test_call_updates_state() {
        let mut state = started_hand();

        state.apply_action(Action::Call).unwrap();

        assert_eq!(state.pot, 4);
        assert_eq!(state.round_bets, [2, 2]);
        assert_eq!(state.player_contributions, [2, 2]);
        assert_eq!(state.current_player, 1);
        assert_eq!(state.raises_this_round, 0);
        assert_eq!(state.actions_this_round, vec![Action::Call]);

        assert_eq!(state.action_history.len(), 1);
        assert_eq!(state.action_history[0].player, 0);
        assert_eq!(state.action_history[0].street, Street::Preflop);
        assert_eq!(state.action_history[0].action, Action::Call);
        assert_eq!(state.action_history[0].to_call, 1);
    }

    #[test]
    fn test_raise_updates_state() {
        let mut state = started_hand();

        state.apply_action(Action::Raise).unwrap();

        // Small blind contributes 1 to call + 2 to raise
        assert_eq!(state.pot, 6);
        assert_eq!(state.round_bets, [4, 2]);
        assert_eq!(state.player_contributions, [4, 2]);
        assert_eq!(state.raises_this_round, 1);
        assert_eq!(state.current_player, 1);

        assert_eq!(state.action_history.len(), 1);
        assert_eq!(state.action_history[0].to_call, 1);
    }

    #[test]
    fn test_fold_through_apply_action() {
        let mut state = started_hand();

        state.apply_action(Action::Fold).unwrap();

        assert!(state.terminal);
        assert_eq!(state.folded_player, Some(0));
        assert_eq!(state.payoffs, [-1.0, 1.0]);
        assert_eq!(state.street, Street::Preflop);
        assert_eq!(state.deck.remaining(), 16);
        assert!(state.public_cards.is_empty());

        assert_eq!(state.action_history.len(), 1);
        assert_eq!(state.actions_this_round, vec![Action::Fold]);
    }

    #[test]
    fn test_player_one_folds_after_raise() {
        let mut state = started_hand();

        state.apply_action(Action::Raise).unwrap();
        state.apply_action(Action::Fold).unwrap();

        assert!(state.terminal);
        assert_eq!(state.folded_player, Some(1));
        assert_eq!(state.pot, 6);
        assert_eq!(state.payoffs, [2.0, -2.0]);
        assert_eq!(state.payoffs.iter().sum::<f64>(), 0.0);
        assert_eq!(state.street, Street::Preflop);
    }

    #[test]
    fn test_preflop_call_check_advances_to_flop() {
        let mut state = started_hand();

        reach_flop(&mut state);

        assert_eq!(state.street, Street::Flop);
        assert_eq!(state.public_cards.len(), 3);
        assert_eq!(state.deck.remaining(), 13);
        assert_eq!(state.pot, 4);
        assert_eq!(state.player_contributions, [2, 2]);
        assert_eq!(state.round_bets, [0, 0]);
        assert_eq!(state.raises_this_round, 0);
        assert_eq!(state.current_player, 1);

        assert!(state.actions_this_round.is_empty());
        assert_eq!(state.action_history.len(), 2);
        assert!(!state.terminal);
    }

    #[test]
    fn test_flop_check_check_advances_to_turn() {
        let mut state = started_hand();
        reach_flop(&mut state);

        state.apply_action(Action::Check).unwrap();
        state.apply_action(Action::Check).unwrap();

        assert_eq!(state.street, Street::Turn);
        assert_eq!(state.public_cards.len(), 4);
        assert_eq!(state.deck.remaining(), 12);
        assert_eq!(state.pot, 4);
        assert_eq!(state.current_player, 1);
        assert_eq!(state.action_history.len(), 4);
        assert!(state.actions_this_round.is_empty());
    }

    #[test]
    fn test_turn_check_check_advances_to_river() {
        let mut state = started_hand();
        reach_flop(&mut state);

        // Complete flop betting
        state.apply_action(Action::Check).unwrap();
        state.apply_action(Action::Check).unwrap();

        // Complete turn betting
        state.apply_action(Action::Check).unwrap();
        state.apply_action(Action::Check).unwrap();

        assert_eq!(state.street, Street::River);
        assert_eq!(state.public_cards.len(), 5);
        assert_eq!(state.deck.remaining(), 11);
        assert_eq!(state.pot, 4);
        assert_eq!(state.current_player, 1);
        assert_eq!(state.action_history.len(), 6);
        assert!(!state.terminal);
    }

    #[test]
    fn test_flop_bet_raise_call() {
        let mut state = started_hand();
        reach_flop(&mut state);

        // Player 1 opens betting
        state.apply_action(Action::Bet).unwrap();

        assert_eq!(state.pot, 6);
        assert_eq!(state.round_bets, [0, 2]);
        assert_eq!(state.raises_this_round, 1);
        assert_eq!(state.current_player, 0);

        // Player 0 raises
        state.apply_action(Action::Raise).unwrap();

        assert_eq!(state.pot, 10);
        assert_eq!(state.round_bets, [4, 2]);
        assert_eq!(state.raises_this_round, 2);
        assert_eq!(state.current_player, 1);

        // Raise cap reached
        assert_eq!(
            state.legal_actions(),
            [
                Some(Action::Fold),
                Some(Action::Call),
                None,
            ]
        );

        // Further raise must be rejected
        assert_eq!(
            state.apply_action(Action::Raise),
            Err(GameError::IllegalAction(Action::Raise))
        );

        // Player 1 calls and the game advances
        state.apply_action(Action::Call).unwrap();

        assert_eq!(state.pot, 12);
        assert_eq!(state.player_contributions, [6, 6]);
        assert_eq!(state.street, Street::Turn);
        assert_eq!(state.public_cards.len(), 4);
        assert_eq!(state.round_bets, [0, 0]);
        assert_eq!(state.raises_this_round, 0);
        assert_eq!(state.action_history.len(), 5);

        // Historical amounts before actions were applied
        assert_eq!(state.action_history[2].to_call, 0); // Bet
        assert_eq!(state.action_history[3].to_call, 2); // Raise
        assert_eq!(state.action_history[4].to_call, 2); // Call
    }

    #[test]
    fn test_invalid_community_card_counts() {
        let mut state = GameState::new();

        assert_eq!(
            state.deal_turn(),
            Err(GameError::InvalidPublicCards(0))
        );

        assert_eq!(
            state.deal_river(),
            Err(GameError::InvalidPublicCards(0))
        );

        assert!(state.public_cards.is_empty());
        assert_eq!(state.deck.remaining(), 20);
    }

    #[test]
    fn test_flop_deck_exhaustion() {
        let mut state = GameState::new();

        // Leave only two cards in the deck
        while state.deck.remaining() > 2 {
            state.deck.draw().unwrap();
        }

        let result = state.deal_flop();

        assert_eq!(result, Err(GameError::DeckExhausted));

        // No partial flop should have been dealt
        assert!(state.public_cards.is_empty());
        assert_eq!(state.deck.remaining(), 2);
    }

    #[test]
    fn test_button_player_one() {
        let mut rng = StdRng::seed_from_u64(42);
        let mut state = GameState::new();

        // Verify setup with player 1 holding the button
        state.hand_number = 1;
        state.start_hand(&mut rng).unwrap();

        assert_eq!(state.button_player, 1);
        assert_eq!(state.current_player, 1);
        assert_eq!(state.round_bets, [2, 1]);
        assert_eq!(state.player_contributions, [2, 1]);
        assert_eq!(state.pot, 3);
    }

    fn showdown_state() -> GameState {
    let mut state = GameState::new();

    state.street = Street::River;
    state.pot = 12;
    state.player_contributions = [6, 6];

    // Player 0: Three Aces, with two Queens on the board
    // Best hand: Full House (Aces over Queens)
    state.player_cards[0] = Some([
        Card { rank: Rank::Ace, suit: Suit::Heart },
        Card { rank: Rank::Ace, suit: Suit::Diamond },
    ]);

    // Player 1: Pair of Kings
    // Best hand: Ace-high Straight
    state.player_cards[1] = Some([
        Card { rank: Rank::King, suit: Suit::Spade },
        Card { rank: Rank::King, suit: Suit::Club },
    ]);

    state.public_cards = vec![
        Card { rank: Rank::Ace, suit: Suit::Spade },
        Card { rank: Rank::Queen, suit: Suit::Heart },
        Card { rank: Rank::Queen, suit: Suit::Diamond },
        Card { rank: Rank::Ten, suit: Suit::Club },
        Card { rank: Rank::Jack, suit: Suit::Spade },
    ];

    state
}

fn tied_showdown_state() -> GameState {
    let mut state = GameState::new();

    state.street = Street::River;
    state.pot = 12;
    state.player_contributions = [6, 6];

    state.player_cards[0] = Some([
        Card { rank: Rank::Ten, suit: Suit::Diamond },
        Card { rank: Rank::Jack, suit: Suit::Spade },
    ]);

    state.player_cards[1] = Some([
        Card { rank: Rank::Ten, suit: Suit::Spade },
        Card { rank: Rank::Jack, suit: Suit::Club },
    ]);

    // Straight on the board: both players tie
    state.public_cards = vec![
        Card { rank: Rank::Ten, suit: Suit::Heart },
        Card { rank: Rank::Jack, suit: Suit::Diamond },
        Card { rank: Rank::Queen, suit: Suit::Spade },
        Card { rank: Rank::King, suit: Suit::Club },
        Card { rank: Rank::Ace, suit: Suit::Heart },
    ];

    state
}


#[test]
fn test_showdown_player0_wins() {
    let mut state = showdown_state();

    state.resolve_showdown().unwrap();

    assert!(state.terminal);
    assert_eq!(state.folded_player, None);
    assert_eq!(state.payoffs, [6.0, -6.0]);
    assert_eq!(state.pot, 12);
    assert_eq!(state.payoffs.iter().sum::<f64>(), 0.0);
}

#[test]
fn test_showdown_player1_wins() {
    let mut state = showdown_state();

    // Swap the players' hole cards
    state.player_cards.swap(0, 1);

    state.resolve_showdown().unwrap();

    assert!(state.terminal);
    assert_eq!(state.folded_player, None);
    assert_eq!(state.payoffs, [-6.0, 6.0]);
    assert_eq!(state.payoffs.iter().sum::<f64>(), 0.0);
}

#[test]
fn test_showdown_tie() {
    let mut state = tied_showdown_state();

    state.resolve_showdown().unwrap();

    assert!(state.terminal);
    assert_eq!(state.folded_player, None);

    // Each player contributed 6 and receives 6 back
    assert_eq!(state.payoffs, [0.0, 0.0]);
    assert_eq!(state.payoffs.iter().sum::<f64>(), 0.0);
}

#[test]
fn test_showdown_invalid_public_cards() {
    let mut state = showdown_state();

    // Remove one community card
    state.public_cards.pop();

    let result = state.resolve_showdown();

    assert_eq!(
        result,
        Err(GameError::InvalidPublicCards(4))
    );

    // Failed showdown must not modify payouts
    assert!(!state.terminal);
    assert_eq!(state.payoffs, [0.0, 0.0]);
    assert_eq!(state.pot, 12);
}

#[test]
fn test_showdown_missing_player0_cards() {
    let mut state = showdown_state();

    state.player_cards[0] = None;

    let result = state.resolve_showdown();

    assert_eq!(
        result,
        Err(GameError::MissingPlayerCards(0))
    );

    assert!(!state.terminal);
    assert_eq!(state.payoffs, [0.0, 0.0]);
}

#[test]
fn test_showdown_missing_player1_cards() {
    let mut state = showdown_state();

    state.player_cards[1] = None;

    let result = state.resolve_showdown();

    assert_eq!(
        result,
        Err(GameError::MissingPlayerCards(1))
    );

    assert!(!state.terminal);
    assert_eq!(state.payoffs, [0.0, 0.0]);
}

#[test]
fn test_automatic_showdown_after_river() {
    let mut state = showdown_state();

    state.current_player = 1;
    state.button_player = 0;
    state.round_bets = [0, 0];

    // Both players check on the river
    state.apply_action(Action::Check).unwrap();
    state.apply_action(Action::Check).unwrap();

    // Showdown should have happened automatically
    assert!(state.terminal);

    assert_eq!(state.street, Street::River);
    assert_eq!(state.public_cards.len(), 5);
    assert_eq!(state.payoffs, [6.0, -6.0]);

    // Both checks should be recorded
    assert_eq!(state.action_history.len(), 2);

    // Terminal states have no legal actions
    assert_eq!(
        state.legal_actions(),
        [None, None, None]
    );

    // Further actions must be rejected
    assert_eq!(
        state.apply_action(Action::Check),
        Err(GameError::GameAlreadyTerminal)
    );
}


}