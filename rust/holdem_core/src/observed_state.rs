use crate::cards::{Card,Rank,Suit};
use crate::state::Street;
use crate::actions::Action;

pub struct ObservedState<'a> {
    pub current_player: usize,
    pub player: usize,
    pub private_cards: [Card; 2],
    pub public_cards: &'a [Card],
    pub street: Street,
    pub pot: i64,
    pub button_player: usize,
    pub amount_to_call: i64,
    pub raises_this_round: usize,
    pub legal_actions: [Option<Action>; 3],
}

impl ObservedState<'static> {
    pub fn test_state() -> Self {
        Self {
            current_player: 0,
            player: 0,
            private_cards: [
                Card { rank: Rank::Ace, suit: Suit::Heart },
                Card { rank: Rank::King, suit: Suit::Diamond },
            ],
            public_cards: &[],
            street: Street::Preflop,
            pot: 3,
            button_player: 0,
            amount_to_call: 1,
            raises_this_round: 0,
            legal_actions: [
                Some(Action::Fold),
                Some(Action::Call),
                Some(Action::Raise),
            ],
        }
    }
}


#[cfg(test)]
mod tests {
    use crate::state::GameState;
    use crate::cards::create_deck;

    use rand::rngs::StdRng;
    use rand::SeedableRng;

    // Create a reproducible game with cards dealt.
    fn setup_game() -> GameState {
        let mut state = GameState::new();
        let mut rng = StdRng::seed_from_u64(42);

        state.start_hand(&mut rng).unwrap();

        state
    }

    #[test]
    fn test_observation_player_cards() {
        let state = setup_game();

        let obs_0 = state.get_observation(&0).unwrap();
        let obs_1 = state.get_observation(&1).unwrap();

        assert_eq!(
            obs_0.private_cards,
            state.player_cards[0].unwrap()
        );

        assert_eq!(
            obs_1.private_cards,
            state.player_cards[1].unwrap()
        );

        // Players must have different private cards.
        assert_ne!(obs_0.private_cards, obs_1.private_cards);
    }

    #[test]
    fn test_observation_player_identity() {
        let state = setup_game();

        for player in 0..2 {
            let obs = state.get_observation(&player).unwrap();

            assert_eq!(obs.player, player);
            assert_eq!(obs.current_player, state.current_player);
            assert_eq!(obs.button_player, state.button_player);
        }
    }

    #[test]
    fn test_observation_public_information() {
        let state = setup_game();

        for player in 0..2 {
            let obs = state.get_observation(&player).unwrap();

            assert_eq!(obs.street, state.street);
            assert_eq!(obs.pot, state.pot);
            assert_eq!(
                obs.raises_this_round,
                state.raises_this_round
            );
            assert_eq!(
                obs.public_cards,
                state.public_cards.as_slice()
            );
        }
    }

    #[test]
    fn test_observation_amount_to_call() {
        let state = setup_game();

        for player in 0..2 {
            let obs = state.get_observation(&player).unwrap();

            assert_eq!(
                obs.amount_to_call,
                state.amount_to_call(player)
            );
        }
    }

    #[test]
    fn test_current_player_has_legal_actions() {
        let state = setup_game();

        let obs = state
            .get_observation(&state.current_player)
            .unwrap();

        assert_eq!(obs.legal_actions, state.legal_actions());

        assert!(
            obs.legal_actions.iter().any(|action| action.is_some())
        );
    }

    #[test]
    fn test_inactive_player_has_no_legal_actions() {
        let state = setup_game();

        let inactive_player = 1 - state.current_player;

        let obs = state.get_observation(&inactive_player).unwrap();

        assert_eq!(obs.legal_actions, [None, None, None]);
    }

    #[test]
    fn test_invalid_player_returns_none() {
        let state = setup_game();

        assert!(state.get_observation(&2).is_none());
        assert!(state.get_observation(&100).is_none());
    }

    #[test]
    fn test_observation_before_hand_returns_none() {
        let state = GameState::new();

        assert!(state.get_observation(&0).is_none());
        assert!(state.get_observation(&1).is_none());
    }

    #[test]
    fn test_public_cards_are_borrowed_not_cloned() {
        let mut state = setup_game();

        // Create a valid three-card public board.
        let private_0 = state.player_cards[0].unwrap();
        let private_1 = state.player_cards[1].unwrap();

        state.public_cards = create_deck()
            .into_iter()
            .filter(|card| {
                !private_0.contains(card) && !private_1.contains(card)
            })
            .take(3)
            .collect();

        let obs = state.get_observation(&0).unwrap();

        // Contents should match.
        assert_eq!(
            obs.public_cards,
            state.public_cards.as_slice()
        );

        // Both slices must point to the same memory.
        assert_eq!(
            obs.public_cards.as_ptr(),
            state.public_cards.as_ptr()
        );

        assert_eq!(obs.public_cards.len(), 3);
    }
}
