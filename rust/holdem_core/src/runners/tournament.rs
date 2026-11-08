use rand::rngs::StdRng;
use rand::SeedableRng;

use crate::state::GameState;
use super::agent::MatchAgent;
use super::error::RunnerError;
use super::multiple_games::{run_games, MatchResult};

#[derive(Debug, Clone)]
pub struct PairingResult {
    pub agent_a: String,
    pub agent_b: String,
    /// A is seat 0; B is seat 1.
    pub a_as_player0: MatchResult,
    /// B is seat 0; A is seat 1.
    pub a_as_player1: MatchResult,
    pub hands: usize,
    pub wins_a: usize,
    pub wins_b: usize,
    pub draws: usize,
    pub payoff_sum_a: f64,
    pub payoff_sq_sum_a: f64,
}

impl PairingResult {
    fn new(agent_a: String, agent_b: String, ab: MatchResult, ba: MatchResult) -> Self {
        Self {
            agent_a,
            agent_b,
            hands: ab.hands + ba.hands,
            wins_a: ab.wins[0] + ba.wins[1],
            wins_b: ab.wins[1] + ba.wins[0],
            draws: ab.draws + ba.draws,
            payoff_sum_a: ab.payoff_sum[0] + ba.payoff_sum[1],
            payoff_sq_sum_a: ab.payoff_sq_sum[0] + ba.payoff_sq_sum[1],
            a_as_player0: ab,
            a_as_player1: ba,
        }
    }

    pub fn average_payoff_a(&self) -> f64 {
        self.payoff_sum_a / self.hands as f64
    }

    /// Approximate 95% confidence-interval half-width for payoff per hand.
    pub fn ci95_half_width(&self) -> f64 {
        if self.hands < 2 {
            return 0.0;
        }
        let n = self.hands as f64;
        let mean = self.average_payoff_a();
        let sample_variance = ((self.payoff_sq_sum_a - n * mean * mean) / (n - 1.0)).max(0.0);
        1.96 * (sample_variance / n).sqrt()
    }
}

#[derive(Debug, Default)]
pub struct TournamentResult {
    pub pairings: Vec<PairingResult>,
}

/// Round-robin tournament: each distinct pair plays two matches,
/// reversing player seats in the second match.
/// `hands_per_seating = 5000` means 10,000 hands per pairing.
pub fn run_tournament(
    agents: &mut [&mut dyn MatchAgent],
    hands_per_seating: usize,
    seed: u64,
) -> Result<TournamentResult, RunnerError> {
    if agents.len() < 2 {
        return Err(RunnerError::NeedAtLeastTwoAgents);
    }
    if hands_per_seating == 0 {
        return Err(RunnerError::ZeroGames);
    }

    let mut report = TournamentResult::default();
    let mut pair_index = 0u64;

    for i in 0..agents.len() {
        for j in (i + 1)..agents.len() {
            // Obtain two independent mutable agent references.
            let (left, right) = agents.split_at_mut(j);
            let a: &mut dyn MatchAgent = &mut *left[i];
            let b: &mut dyn MatchAgent = &mut *right[0];

            let name_a = a.name().to_owned();
            let name_b = b.name().to_owned();

            let mut state = GameState::new();
            let mut rng = StdRng::seed_from_u64(seed.wrapping_add(pair_index));
            pair_index += 1;

            let ab = run_games(
                &mut state, &mut rng, &mut *a, &mut *b, hands_per_seating,
            )?;
            let ba = run_games(
                &mut state, &mut rng, &mut *b, &mut *a, hands_per_seating,
            )?;

            report.pairings.push(PairingResult::new(name_a, name_b, ab, ba));
        }
    }

    Ok(report)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn correctly_reverses_seat_accounting() {
        let ab = MatchResult {
            hands: 2,
            wins: [2, 0],
            payoff_sum: [6.0, -6.0],
            payoff_sq_sum: [20.0, 20.0],
            ..Default::default()
        };
        let ba = MatchResult {
            hands: 2,
            wins: [2, 0],
            payoff_sum: [4.0, -4.0],
            payoff_sq_sum: [8.0, 8.0],
            ..Default::default()
        };

        let r = PairingResult::new("A".into(), "B".into(), ab, ba);
        assert_eq!(r.hands, 4);
        assert_eq!(r.wins_a, 2);
        assert_eq!(r.wins_b, 2);
        assert_eq!(r.payoff_sum_a, 2.0);
        assert_eq!(r.average_payoff_a(), 0.5);
    }
}
