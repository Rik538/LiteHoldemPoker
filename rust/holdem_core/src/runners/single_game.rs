use rand::Rng;

use crate::state::GameState;
use super::agent::MatchAgent;
use super::error::RunnerError;

// Guard against a faulty game-state transition that never terminates.
const MAX_ACTIONS_PER_HAND: usize = 64;

#[derive(Debug, Clone, Copy)]
pub struct GameResult {
    /// Signed chips won/lost, indexed by player seat (0 or 1).
    pub payoffs: [f64; 2],
    pub actions_by_player: [usize; 2],
    pub button_player: usize,
}

/// Plays exactly one complete hand, using the engine's hand-start logic.
/// Reuse `state` across hands so `start_hand()` can rotate the button.
pub fn run_game<R: Rng + ?Sized>(
    state: &mut GameState,
    rng: &mut R,
    player0: &mut dyn MatchAgent,
    player1: &mut dyn MatchAgent,
) -> Result<GameResult, RunnerError> {
    state.start_hand(rng)?;

    let mut actions_by_player = [0usize; 2];
    let mut actions = 0usize;

    while !state.terminal {
        if actions >= MAX_ACTIONS_PER_HAND {
            return Err(RunnerError::ActionLimitExceeded {
                limit: MAX_ACTIONS_PER_HAND,
            });
        }

        let player = state.current_player;

        // The observation borrows cards from state, so finish using it
        // before calling apply_action(&mut self).
        let chosen_action = {
            let observation = state
                .get_observation(&player)
                .ok_or(RunnerError::MissingObservation { player })?;

            if observation.legal_actions.iter().all(Option::is_none) {
                return Err(RunnerError::NoLegalActions { player });
            }

            let agent: &mut dyn MatchAgent = if player == 0 {
                &mut *player0
            } else {
                &mut *player1
            };

            let action = agent
                .select_action(&observation)
                .map_err(|message| RunnerError::AgentFailure { player, message })?;

            if !observation.legal_actions.contains(&Some(action)) {
                return Err(RunnerError::IllegalAgentAction { player, action });
            }
            action
        };

        state.apply_action(chosen_action)?;
        actions_by_player[player] += 1;
        actions += 1;
    }

    Ok(GameResult {
        payoffs: state.payoffs,
        actions_by_player,
        button_player: state.button_player,
    })
}
