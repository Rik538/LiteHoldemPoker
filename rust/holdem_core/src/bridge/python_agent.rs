
use std::error::Error;
use std::io::{BufRead, BufReader, ErrorKind, Write};
use std::process::{
    Child, ChildStdin, ChildStdout, Command, Stdio,
};

use serde_json::Value;

use crate::actions::Action;
use crate::observed_state::ObservedState;
use crate::bridge::observation::observation_to_json;

pub struct PythonAgentBridge {
    child: Child,
    stdin: ChildStdin,
    stdout: BufReader<ChildStdout>,
}

impl PythonAgentBridge {
    pub fn new(
        python_executable: &str,
        project_root: &str,
    ) -> Result<Self, Box<dyn Error>> {

        let mut child = Command::new(python_executable)
            .args([
                "-u",
                "-m",
                "lite_holdem_ai.bridge.agent_bridge",
            ])
            .current_dir(project_root)
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::inherit())
            .spawn()?;

        let stdin = child.stdin.take().unwrap();
        let stdout = child.stdout.take().unwrap();

        Ok(Self {
            child,
            stdin,
            stdout: BufReader::new(stdout),
        })
    }

    pub fn select_action(
        &mut self,
        observation: &ObservedState<'_>,
    ) -> Result<Action, Box<dyn Error>> {

        // Convert observation to JSON.
        let message = observation_to_json(observation)?;

        // Send one JSON line to Python.
        writeln!(self.stdin, "{message}")?;
        self.stdin.flush()?;

        // Read one response line.
        let mut response_line = String::new();

        let bytes_read = self.stdout.read_line(
            &mut response_line
        )?;

        if bytes_read == 0 {
            return Err(std::io::Error::new(
                ErrorKind::UnexpectedEof,
                "Python agent process closed",
            ).into());
        }

        // Parse JSON response.
        let response: Value =
            serde_json::from_str(&response_line)?;

        if let Some(error) = response["error"].as_str() {
            return Err(std::io::Error::new(
                ErrorKind::InvalidData,
                format!("Python agent error: {error}"),
            ).into());
        }

        let action_name = response["action"]
            .as_str()
            .ok_or_else(|| std::io::Error::new(
                ErrorKind::InvalidData,
                "Missing action in Python response",
            ))?;

        // Convert Python action string to Rust Action.
        let action = match action_name {
            "FOLD" => Action::Fold,
            "CHECK" => Action::Check,
            "CALL" => Action::Call,
            "BET" => Action::Bet,
            "RAISE" => Action::Raise,
            _ => {
                return Err(std::io::Error::new(
                    ErrorKind::InvalidData,
                    format!("Unknown Python action: {action_name}"),
                ).into());
            }
        };

        // Never allow Python to submit an illegal action.
        if !observation.legal_actions.contains(&Some(action)) {
            return Err(std::io::Error::new(
                ErrorKind::InvalidData,
                format!("Illegal action returned: {action_name}"),
            ).into());
        }

        Ok(action)
    }
}

impl Drop for PythonAgentBridge {
    fn drop(&mut self) {
        let _ = self.child.kill();
        let _ = self.child.wait();
    }
}
