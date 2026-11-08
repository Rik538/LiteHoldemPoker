use crate::actions::Action;
use crate::errors::GameError;

#[derive(Debug)]
pub enum RunnerError {
    Game(GameError),
    MissingObservation { player: usize },
    NoLegalActions { player: usize },
    AgentFailure { player: usize, message: String },
    IllegalAgentAction { player: usize, action: Action },
    ActionLimitExceeded { limit: usize },
    NeedAtLeastTwoAgents,
    ZeroGames,
}

impl From<GameError> for RunnerError {
    fn from(value: GameError) -> Self {
        Self::Game(value)
    }
}
