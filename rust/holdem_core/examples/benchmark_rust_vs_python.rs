
use std::path::Path;

use rand::rngs::StdRng;
use rand::SeedableRng;

use holdem_core::state::GameState;
use holdem_core::equity_cache_access::Cache;
use holdem_core::cfr::trainer::MCCFRTrainer;
use holdem_core::agents::cfr_agent::CFRAgent;
use holdem_core::bridge::python_agent::PythonAgentBridge;
use holdem_core::runners::single_game::run_game;

const PROJECT_ROOT: &str =
    "/home/richard.dunbar101/Projects/LiteHoldemPoker";

const RUST_CHECKPOINT: &str =
    "/home/richard.dunbar101/Projects/LiteHoldemPoker/checkpoints/rs_1M.bin";

const RUST_EQUITY_CACHE: &str =
    "/home/richard.dunbar101/Projects/LiteHoldemPoker/cache/equity_cache_rust.sqlite";

fn main() -> Result<(), Box<dyn std::error::Error>> {
    println!("Loading Rust equity cache...");

    let cache = Cache::new(RUST_EQUITY_CACHE)?;
    let memory_cache = cache.load_into_memory()?;

    println!("Loading Rust CFR checkpoint...");

    let trainer = MCCFRTrainer::load_checkpoint(
    Path::new(RUST_CHECKPOINT),
    memory_cache,
    42,
)
.map_err(|error| std::io::Error::other(format!("{error:?}")))?;

    println!("Rust infosets: {}", trainer.nodes.len());

    let mut rust_agent = CFRAgent::new(
        &trainer.nodes,
        &trainer.memory_cache,
        123,
        Some("Rust CFR"),
    );

    println!("Starting Python CFR agent...");

    let mut python_agent = PythonAgentBridge::new(
        "python",
        PROJECT_ROOT,
    )?;

    let mut state = GameState::new();
    let mut rng = StdRng::seed_from_u64(2026);

    println!("\n--- Rust CFR vs Python CFR ---");

    let result = run_game(
        &mut state,
        &mut rng,
        &mut rust_agent,
        &mut python_agent,
    )
    .map_err(|error| std::io::Error::other(format!("{error:?}")))?;

    println!("\n--- Game Result ---");
    println!("Button: {}", result.button_player);
    println!("Rust payoff:   {:.2}", result.payoffs[0]);
    println!("Python payoff: {:.2}", result.payoffs[1]);

    println!("Rust decisions: {}", result.actions_by_player[0]);
    println!("Python decisions: {}", result.actions_by_player[1]);

    assert!(state.terminal);

    assert!(
        (result.payoffs[0] + result.payoffs[1]).abs() < 1e-9,
        "Payoffs must sum to zero"
    );

    println!("\nRust vs Python game completed successfully!");

    Ok(())
}
