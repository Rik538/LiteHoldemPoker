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

#[derive(Debug)]
pub enum TrainerError {
    NoLegalActions,
    ObservationError,
    InfosetError,
    GameError(GameError),

    CheckpointEncode(bincode::error::EncodeError),
    CheckpointDecode(bincode::error::DecodeError),
    CheckpointIo(std::io::Error),
    CheckpointVersion(u32),
}

impl From<GameError> for TrainerError {
    fn from(error: GameError) -> Self {
        TrainerError::GameError(error)
    }
}

