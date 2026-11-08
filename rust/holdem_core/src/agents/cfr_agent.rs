
use std::collections::HashMap;

use rand::rngs::StdRng;
use rand::{SeedableRng,RngExt};

use crate::actions::Action;
use crate::observed_state::ObservedState;
use crate::equity_cache_access::MemoryCache;
use crate::cfr::infoset::InfoSet;
use crate::cfr::node::{CFRNode, action_index};

#[derive(Debug)]
pub enum CFRAgentError {
    NoLegalActions,
    MissingEquity,
}

pub struct CFRAgent<'a> {
    pub name: String,
    pub nodes: &'a HashMap<InfoSet, CFRNode>,
    pub memory_cache: &'a MemoryCache,
    pub missing_nodes: usize,
    pub decisions: usize,
    rng: StdRng,
}

impl<'a> CFRAgent<'a> {
    pub fn new(
        nodes: &'a HashMap<InfoSet, CFRNode>,
        memory_cache: &'a MemoryCache,
        seed: u64,
        name: Option<&str>,
    ) -> Self {
        Self {
            name: name.unwrap_or("CFR").to_string(),
            nodes,
            memory_cache,
            missing_nodes: 0,
            decisions: 0,
            rng: StdRng::seed_from_u64(seed),
        }
    }

    pub fn select_action(
        &mut self,
        observation: &ObservedState<'_>,
        legal_actions: &[Option<Action>; 3],
    ) -> Result<Action, CFRAgentError> {
        let legal_count = legal_actions
            .iter()
            .flatten()
            .count();

        if legal_count == 0 {
            return Err(CFRAgentError::NoLegalActions);
        }

        self.decisions += 1;

        // Construct the information-set key.
        let infoset = InfoSet::from_observation(
            observation,
            self.memory_cache,
        )
        .ok_or(CFRAgentError::MissingEquity)?;

        // Retrieve the trained node.
        let node = match self.nodes.get(&infoset) {
            Some(node) => node,

            None => {
                self.missing_nodes += 1;

                // Unknown infoset: choose uniformly
                // between legal actions.
                let index = self.rng.random_range(0..legal_count);

                return Ok(
                    *legal_actions
                        .iter()
                        .flatten()
                        .nth(index)
                        .unwrap()
                );
            }
        };

        // Use the learned average strategy.
        let avg_strategy =
            node.get_average_strategy(legal_actions);

        Ok(self.sample_action(legal_actions, &avg_strategy))
    }

    pub fn sample_action(
        &mut self,
        legal_actions: &[Option<Action>; 3],
        strategy: &[f64; 5],
    ) -> Action {
        let roll: f64 = self.rng.random();
        let mut cumulative = 0.0;
        let mut last_action = None;

        for action in legal_actions.iter().flatten() {
            let idx = action_index(action);

            cumulative += strategy[idx];
            last_action = Some(*action);

            if roll < cumulative {
                return *action;
            }
        }

        // Handles small floating-point rounding errors.
        last_action.expect("No legal actions available")
    }
}
