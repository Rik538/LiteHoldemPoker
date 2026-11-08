
use crate::state::Street;
use crate::cfr::abstraction::{street_aware_equity_bucket,pot_bucket,texture_bucket};
use crate::observed_state::ObservedState;
use crate::equity_cache_access::MemoryCache;

use bincode::{Encode, Decode};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Encode, Decode)]
pub struct InfoSet {
    pub player: u8,
    pub street: Street,
    pub equity_bucket: u8,
    pub pot_bucket: u8,
    pub texture_bucket: u8,
    pub position: u8,
    pub facing_bet: bool,
    pub raises_this_round: u8,
}

impl InfoSet {

    pub fn from_observation(observation: &ObservedState<'_>, memory_cache:&MemoryCache) -> Option<Self> {
        let player_cards = observation.private_cards;
        let board_cards = observation.public_cards;

        let equity = memory_cache
            .get_equity_score(&player_cards, board_cards)?;

        Some( Self {
            player: observation.player as u8,
            street: observation.street,
            equity_bucket: street_aware_equity_bucket(equity, observation.street),
            pot_bucket: pot_bucket(observation.pot),
            texture_bucket: texture_bucket(board_cards),
            position: (observation.player == observation.button_player) as u8,
            facing_bet: observation.amount_to_call > 0,
            raises_this_round: observation.raises_this_round as u8,
        })

    }
    
}


#[cfg(test)]
mod tests {
    use super::*;

    use crate::cards::{Card, create_deck};
    use crate::state::{GameState, Street};
    use crate::equity_cache_access::MemoryCache;
    use crate::equity_builder::EquityResult;

    use rand::rngs::StdRng;
    use rand::SeedableRng;

    use std::collections::HashMap;
    use std::sync::OnceLock;

    fn setup_game() -> GameState {
        let mut state = GameState::new();
        let mut rng = StdRng::seed_from_u64(42);

        state.start_hand(&mut rng).unwrap();

        state
    }

    // Find three available community cards of the same suit.
    // This guarantees a flush-pressure texture.
    fn suited_flop(state: &GameState) -> Vec<Card> {
        let hand_0 = state.player_cards[0].unwrap();
        let hand_1 = state.player_cards[1].unwrap();
        let deck = create_deck();

        for card in deck.iter() {
            let board: Vec<Card> = deck
                .iter()
                .copied()
                .filter(|candidate| {
                    candidate.suit == card.suit
                        && !hand_0.contains(candidate)
                        && !hand_1.contains(candidate)
                })
                .take(3)
                .collect();

            if board.len() == 3 {
                return board;
            }
        }

        panic!("Could not generate a suited flop");
    }

    // Share one cache across the tests.
    // Useful because your MemoryCache::new() currently
    // preallocates capacity for the full equity database.
    fn test_cache() -> &'static MemoryCache {
        static CACHE: OnceLock<MemoryCache> = OnceLock::new();

        CACHE.get_or_init(|| {
            let state = setup_game();
            let mut cache = MemoryCache::new();

            let hand_0 = state.player_cards[0].unwrap();
            let hand_1 = state.player_cards[1].unwrap();

            // Player 0: 10% equity
            cache.insert(
                &hand_0,
                &[],
                EquityResult {
                    wins: 10,
                    losses: 90,
                    splits: 0,
                    total: 100,
                },
            );

            // Player 1: 90% equity
            cache.insert(
                &hand_1,
                &[],
                EquityResult {
                    wins: 90,
                    losses: 10,
                    splits: 0,
                    total: 100,
                },
            );

            // Player 0: a known flop equity
            let board = suited_flop(&state);

            cache.insert(
                &hand_0,
                &board,
                EquityResult {
                    wins: 60,
                    losses: 40,
                    splits: 0,
                    total: 100,
                },
            );

            cache
        })
    }

    #[test]
    fn test_identical_observations_produce_identical_infosets() {
        let state = setup_game();
        let cache = test_cache();

        let observation = state.get_observation(&0).unwrap();

        let infoset_1 =
            InfoSet::from_observation(&observation, cache).unwrap();

        let infoset_2 =
            InfoSet::from_observation(&observation, cache).unwrap();

        assert_eq!(infoset_1, infoset_2);
    }

    #[test]
    fn test_infoset_can_be_used_as_hashmap_key() {
        let state = setup_game();
        let cache = test_cache();

        let observation = state.get_observation(&0).unwrap();

        let infoset =
            InfoSet::from_observation(&observation, cache).unwrap();

        let mut table: HashMap<InfoSet, usize> = HashMap::new();

        table.insert(infoset, 100);

        let same_infoset =
            InfoSet::from_observation(&observation, cache).unwrap();

        assert_eq!(table.get(&same_infoset), Some(&100));
        assert_eq!(table.len(), 1);
    }

    #[test]
    fn test_equity_buckets() {
        let state = setup_game();
        let cache = test_cache();

        let obs_0 = state.get_observation(&0).unwrap();
        let obs_1 = state.get_observation(&1).unwrap();

        let infoset_0 =
            InfoSet::from_observation(&obs_0, cache).unwrap();

        let infoset_1 =
            InfoSet::from_observation(&obs_1, cache).unwrap();

        // Preflop thresholds:
        // [0.35, 0.45, 0.55, 0.65]

        assert_eq!(infoset_0.equity_bucket, 0);
        assert_eq!(infoset_1.equity_bucket, 4);

        assert_ne!(
            infoset_0.equity_bucket,
            infoset_1.equity_bucket
        );
    }

    #[test]
    fn test_position_changes_with_button() {
        let mut state = setup_game();
        let cache = test_cache();

        state.button_player = 0;

        let button_infoset = {
            let obs = state.get_observation(&0).unwrap();
            InfoSet::from_observation(&obs, cache).unwrap()
        };

        state.button_player = 1;

        let non_button_infoset = {
            let obs = state.get_observation(&0).unwrap();
            InfoSet::from_observation(&obs, cache).unwrap()
        };

        assert_eq!(button_infoset.position, 1);
        assert_eq!(non_button_infoset.position, 0);
    }

    #[test]
    fn test_pot_bucket_changes() {
        let mut state = setup_game();
        let cache = test_cache();

        state.pot = 4;

        let small_pot = {
            let obs = state.get_observation(&0).unwrap();
            InfoSet::from_observation(&obs, cache).unwrap()
        };

        state.pot = 5;

        let larger_pot = {
            let obs = state.get_observation(&0).unwrap();
            InfoSet::from_observation(&obs, cache).unwrap()
        };

        assert_eq!(small_pot.pot_bucket, 0);
        assert_eq!(larger_pot.pot_bucket, 1);

        assert_ne!(small_pot, larger_pot);
    }

    #[test]
    fn test_facing_bet() {
        let mut state = setup_game();
        let cache = test_cache();

        state.current_player = 0;
        state.round_bets = [0, 0];

        let no_bet = {
            let obs = state.get_observation(&0).unwrap();
            InfoSet::from_observation(&obs, cache).unwrap()
        };

        state.round_bets = [0, 2];

        let facing_bet = {
            let obs = state.get_observation(&0).unwrap();
            InfoSet::from_observation(&obs, cache).unwrap()
        };

        assert!(!no_bet.facing_bet);
        assert!(facing_bet.facing_bet);
    }

    #[test]
    fn test_board_texture_and_missing_equity() {
        let mut state = setup_game();
        let cache = test_cache();

        // Preflop: no public cards.
        let preflop_infoset = {
            let obs = state.get_observation(&0).unwrap();
            InfoSet::from_observation(&obs, cache).unwrap()
        };

        assert_eq!(preflop_infoset.texture_bucket, 0);

        // Flop: three distinct ranks of the same suit.
        state.public_cards = suited_flop(&state);
        state.street = Street::Flop;

        let flop_infoset = {
            let obs = state.get_observation(&0).unwrap();
            InfoSet::from_observation(&obs, cache).unwrap()
        };

        // Flush pressure (2) + straight pressure (4)
        assert_eq!(flop_infoset.texture_bucket, 6);
        assert_eq!(flop_infoset.street, Street::Flop);

        // Add another valid card to create an uncached turn.
        let hand_0 = state.player_cards[0].unwrap();
        let hand_1 = state.player_cards[1].unwrap();

        let next_card = create_deck()
            .into_iter()
            .find(|card| {
                !hand_0.contains(card)
                    && !hand_1.contains(card)
                    && !state.public_cards.contains(card)
            })
            .unwrap();

        state.public_cards.push(next_card);
        state.street = Street::Turn;

        let obs = state.get_observation(&0).unwrap();

        // No turn entry was inserted into our test cache.
        assert!(
            InfoSet::from_observation(&obs, cache).is_none()
        );
    }
}

