
use crate::actions::Action;
use crate::observed_state::ObservedState;
use crate::equity_cache_access::MemoryCache;
use crate::cfr::abstraction::street_aware_equity_bucket;

#[derive(Debug, PartialEq, Eq)]
pub enum CachedBucketAgentError {
    NoLegalActions,
    MissingEquity,
}

pub struct CachedBucketEquityAgent<'a> {
    pub name: String,
    pub memory_cache: &'a MemoryCache,
    pub decisions: usize,
}

impl<'a> CachedBucketEquityAgent<'a> {
    pub fn new(
        memory_cache: &'a MemoryCache,
        name: Option<&str>,
    ) -> Self {
        Self {
            name: name.unwrap_or("Cached Bucket Equity").to_string(),
            memory_cache,
            decisions: 0,
        }
    }

    pub fn select_action(
        &mut self,
        observation: &ObservedState<'_>,
        legal_actions: &[Option<Action>; 3],
    ) -> Result<Action, CachedBucketAgentError> {
        if !legal_actions.iter().any(Option::is_some) {
            return Err(CachedBucketAgentError::NoLegalActions);
        }

        self.decisions += 1;

        let equity = self.memory_cache
            .get_equity_score(
                &observation.private_cards,
                observation.public_cards,
            )
            .ok_or(CachedBucketAgentError::MissingEquity)?;

        let bucket = street_aware_equity_bucket(
            equity,
            observation.street,
        );

        Ok(self.act_from_bucket(
            bucket,
            equity,
            observation.pot as f64,
            observation.amount_to_call as f64,
            legal_actions,
        ))
    }

    fn act_from_bucket(
        &self,
        bucket: u8,
        equity: f64,
        pot: f64,
        amount_to_call: f64,
        legal_actions: &[Option<Action>; 3],
    ) -> Action {
        if amount_to_call == 0.0 {
            self.act_bucket_when_free(bucket, legal_actions)
        } else {
            self.act_bucket_facing_bet(
                bucket,
                equity,
                pot,
                amount_to_call,
                legal_actions,
            )
        }
    }

    fn act_bucket_when_free(
        &self,
        bucket: u8,
        legal_actions: &[Option<Action>; 3],
    ) -> Action {
        if bucket >= 3 && Self::is_legal(legal_actions, Action::Bet) {
            return Action::Bet;
        }

        if Self::is_legal(legal_actions, Action::Check) {
            return Action::Check;
        }

        Self::first_legal(legal_actions)
    }

    fn act_bucket_facing_bet(
        &self,
        bucket: u8,
        equity: f64,
        pot: f64,
        amount_to_call: f64,
        legal_actions: &[Option<Action>; 3],
    ) -> Action {
        let pot_odds = Self::pot_odds(pot, amount_to_call);

        match bucket {
            4 => {
                if Self::is_legal(legal_actions, Action::Raise) {
                    return Action::Raise;
                }

                if Self::is_legal(legal_actions, Action::Call) {
                    return Action::Call;
                }
            }

            3 => {
                if equity >= 0.68
                    && Self::is_legal(legal_actions, Action::Raise)
                {
                    return Action::Raise;
                }

                if Self::is_legal(legal_actions, Action::Call) {
                    return Action::Call;
                }
            }

            2 => {
                if equity >= pot_odds
                    && Self::is_legal(legal_actions, Action::Call)
                {
                    return Action::Call;
                }
            }

            1 => {
                if equity >= pot_odds + 0.05
                    && Self::is_legal(legal_actions, Action::Call)
                {
                    return Action::Call;
                }
            }

            _ => {}
        }

        // Fold weak hands when facing a bet.
        if Self::is_legal(legal_actions, Action::Fold) {
            return Action::Fold;
        }

        // Fallback to calling where possible.
        if Self::is_legal(legal_actions, Action::Call) {
            return Action::Call;
        }

        Self::first_legal(legal_actions)
    }

    fn pot_odds(pot: f64, amount_to_call: f64) -> f64 {
        amount_to_call / (pot + amount_to_call)
    }

    fn is_legal(
        legal_actions: &[Option<Action>; 3],
        action: Action,
    ) -> bool {
        legal_actions.contains(&Some(action))
    }

    fn first_legal(
        legal_actions: &[Option<Action>; 3],
    ) -> Action {
        legal_actions
            .iter()
            .flatten()
            .copied()
            .next()
            .expect("No legal actions available")
    }
}
