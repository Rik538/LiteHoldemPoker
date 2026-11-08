use holdem_core::bridge::python_agent::PythonAgentBridge;
use holdem_core::observed_state::ObservedState;

fn main() -> Result<(), Box<dyn std::error::Error>> {

    let mut python = PythonAgentBridge::new(
        "python",
        "/home/richard.dunbar101/Projects/LiteHoldemPoker",
    )?;

    let observation = ObservedState::test_state();


    let action = python.select_action(&observation)?;

    println!("Python CFR selected: {:?}", action);

    assert!(
        observation.legal_actions.contains(&Some(action)),
        "Python CFR returned an illegal action"
    );

    println!("Rust/Python communication successful!");

    Ok(())
}