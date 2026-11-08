pub mod agent;
pub mod error;
pub mod single_game;
pub mod multiple_games;
pub mod tournament;

pub use agent::MatchAgent;
pub use error::RunnerError;
pub use single_game::{run_game, GameResult};
pub use multiple_games::{run_games, MatchResult};
pub use tournament::{run_tournament, PairingResult, TournamentResult};
