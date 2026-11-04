use crate::actions::Action;

#[derive(Debug, PartialEq, Eq)]
pub enum GameError {
    IllegalAction(Action),
    GameAlreadyTerminal,
    DeckExhausted,
    InvalidPlayer(usize),
    InvalidPublicCards(usize),
    MissingPlayerCards(usize),
}