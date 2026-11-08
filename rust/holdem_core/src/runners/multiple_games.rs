use rand::Rng;

use crate::state::GameState;
use super::agent::MatchAgent;
use super::error::RunnerError;
use super::single_game::{run_game, GameResult};

#[derive(Debug, Clone, Default)]
pub struct MatchResult {
    pub hands: usize,
    /// Wins by seat: [player 0 wins, player 1 wins].
    pub wins: [usize; 2],
    pub draws: usize,
    /// Sum of chip payoffs by seat.
    pub payoff_sum: [f64; 2],
    /// Sum of squared payoffs for standard errors later.
    pub payoff_sq_sum: [f64; 2],
    pub actions_by_player: [usize; 2],
    /// Count how often each seat held the button.
    pub button_counts: [usize; 2],
}

impl MatchResult {
    pub fn record(&mut self, result: GameResult) {
        self.hands += 1;
        self.actions_by_player[0] += result.actions_by_player[0];
        self.actions_by_player[1] += result.actions_by_player[1];
        self.button_counts[result.button_player] += 1;

        for seat in 0..2 {
            let payoff = result.payoffs[seat];
            self.payoff_sum[seat] += payoff;
            self.payoff_sq_sum[seat] += payoff * payoff;
        }

        if result.payoffs[0] > 0.0 {
            self.wins[0] += 1;
        } else if result.payoffs[0] < 0.0 {
            self.wins[1] += 1;
        } else {
            self.draws += 1;
        }
    }

    pub fn average_payoff(&self, seat: usize) -> f64 {
        if self.hands == 0 { 0.0 } else { self.payoff_sum[seat] / self.hands as f64 }
    }
}

/// Aggregate repeated hands with the same player-to-seat assignment.
/// Pass the same GameState across calls so button rotation continues.
pub fn run_games<R: Rng + ?Sized>(
    state: &mut GameState,
    rng: &mut R,
    player0: &mut dyn MatchAgent,
    player1: &mut dyn MatchAgent,
    hands: usize,
) -> Result<MatchResult, RunnerError> {
    if hands == 0 {
        return Err(RunnerError::ZeroGames);
    }

    let mut summary = MatchResult::default();
    for _ in 0..hands {
        let game = run_game(state, rng, &mut *player0, &mut *player1)?;
        summary.record(game);
    }
    Ok(summary)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn aggregates_payoffs_wins_and_button_counts() {
        let mut summary = MatchResult::default();
        summary.record(GameResult {
            payoffs: [2.0, -2.0],
            actions_by_player: [3, 2],
            button_player: 0,
        });
        summary.record(GameResult {
            payoffs: [-4.0, 4.0],
            actions_by_player: [2, 3],
            button_player: 1,
        });
        summary.record(GameResult {
            payoffs: [0.0, 0.0],
            actions_by_player: [1, 1],
            button_player: 0,
        });

        assert_eq!(summary.hands, 3);
        assert_eq!(summary.wins, [1, 1]);
        assert_eq!(summary.draws, 1);
        assert_eq!(summary.payoff_sum, [-2.0, 2.0]);
        assert_eq!(summary.payoff_sq_sum, [20.0, 20.0]);
        assert_eq!(summary.button_counts, [2, 1]);
        assert_eq!(summary.actions_by_player, [6, 6]);
    }
}
