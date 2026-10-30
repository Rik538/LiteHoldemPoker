use crate::deck::Deck;
use crate::cards::Card;
use crate::actions::Action;

#[derive(Debug, Copy, Clone, PartialEq, Eq)]
pub enum Street {
    Preflop,
    Flop,
    Turn,
    River,
}

#[derive(Debug, Copy, Clone, PartialEq, Eq)]
pub struct ActionRecord {
    pub player: usize,
    pub street: Street,
    pub action: Action,
    pub to_call: i64,
}

#[derive(Debug, Clone,  PartialEq)]
pub struct GameState {
    pub(crate) deck: Deck,

    pub(crate) player_cards: [Option<[Card; 2]>; 2],
    pub(crate) public_cards: Vec<Card>,

    pub(crate) pot: i64,
    pub(crate) player_contributions: [i64;2],

    pub(crate) round_bets: [i64;2],

    pub(crate) terminal: bool,
    pub(crate) folded_player: Option<usize>,

    pub(crate) action_history: Vec<ActionRecord>,
    pub(crate) raises_this_round: usize,
    pub(crate) actions_this_round: Vec<Action>,

    pub(crate) payoffs: [f64;2],

    pub(crate) button_player: usize,
    pub(crate) small_blind: i64,
    pub(crate) big_blind: i64,

    pub(crate) hand_number: usize,

    pub(crate) current_player: usize,
    pub(crate) street: Street,
}

pub const MAX_RAISES_THIS_ROUND: usize = 2;

impl GameState {
    pub fn new() -> Self {
        GameState {
            deck: Deck::new(),
            player_cards: [None; 2],
            public_cards: Vec::new(),
            pot: 0,
            player_contributions: [0; 2],
            round_bets: [0; 2],
            terminal: false,
            folded_player: None,
            action_history: Vec::new(),
            raises_this_round: 0,
            actions_this_round: Vec::new(),
            payoffs: [0.0; 2],
            button_player: 0,
            small_blind: 1,
            big_blind: 2,
            hand_number: 0,
            current_player: 0,
            street: Street::Preflop,
        }
    }
}




#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_initial_game_state() {
        let state = GameState::new();

        // Deck
        assert_eq!(state.deck.remaining(), 20);

        // Player cards
        assert_eq!(state.player_cards, [None; 2]);
        assert!(state.public_cards.is_empty());

        // Pot and contributions
        assert_eq!(state.pot, 0);
        assert_eq!(state.player_contributions, [0; 2]);
        assert_eq!(state.round_bets, [0; 2]);

        // Current game state
        assert_eq!(state.current_player, 0);
        assert_eq!(state.street, Street::Preflop);
        assert!(!state.terminal);
        assert_eq!(state.folded_player, None);

        // Action history
        assert!(state.action_history.is_empty());
        assert!(state.actions_this_round.is_empty());
        assert_eq!(state.raises_this_round, 0);

        // Payoffs
        assert_eq!(state.payoffs, [0.0; 2]);

        // Blinds and button
        assert_eq!(state.button_player, 0);
        assert_eq!(state.small_blind, 1);
        assert_eq!(state.big_blind, 2);

        // Hand number
        assert_eq!(state.hand_number, 0);
    }
}