use crate::actions::Action;
use crate::observed_state::ObservedState;
use crate::agents::cfr_agent::CFRAgent;
use crate::agents::cached_bucket_equity_agent::CachedBucketEquityAgent;
use crate::bridge::python_agent::PythonAgentBridge;

/// The minimal API the game runner needs from any player.
/// Add another `impl MatchAgent for YourAgent` to enter more agents.
pub trait MatchAgent {
    fn name(&self) -> &str;
    fn select_action(&mut self, observation: &ObservedState<'_>) -> Result<Action, String>;
}

impl MatchAgent for CFRAgent<'_> {
    fn name(&self) -> &str {
        &self.name
    }

    fn select_action(&mut self, observation: &ObservedState<'_>) -> Result<Action, String> {
        CFRAgent::select_action(self, observation, &observation.legal_actions)
            .map_err(|error| format!("{error:?}"))
    }
}

impl MatchAgent for CachedBucketEquityAgent<'_> {
    fn name(&self) -> &str {
        &self.name
    }

    fn select_action(&mut self, observation: &ObservedState<'_>) -> Result<Action, String> {
        CachedBucketEquityAgent::select_action(self, observation, &observation.legal_actions)
            .map_err(|error| format!("{error:?}"))
    }
}




impl MatchAgent for PythonAgentBridge {
    fn name(&self) -> &str {
        "Python CFR"
    }

    fn select_action(
        &mut self,
        observation: &ObservedState<'_>,
    ) -> Result<Action, String> {
        PythonAgentBridge::select_action(self, observation)
            .map_err(|error| error.to_string())
    }
}
