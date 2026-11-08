
use std::path::Path;
use std::time::Instant;

use holdem_core::agents::cfr_agent::CFRAgent;
use holdem_core::bridge::python_agent::PythonAgentBridge;
use holdem_core::cfr::trainer::MCCFRTrainer;
use holdem_core::equity_cache_access::Cache;
use holdem_core::runners::agent::MatchAgent;
use holdem_core::runners::tournament::run_tournament;

// Project paths
const PROJECT_ROOT: &str =
    "/home/richard.dunbar101/Projects/LiteHoldemPoker";

const RUST_CHECKPOINT: &str =
    "/home/richard.dunbar101/Projects/LiteHoldemPoker/checkpoints/rs_1M.bin";

const RUST_EQUITY_CACHE: &str =
    "/home/richard.dunbar101/Projects/LiteHoldemPoker/cache/equity_cache_rust.sqlite";

// 5,000 hands per seating = 10,000 hands total.
const HANDS_PER_SEATING: usize = 50_000;

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

    println!("Rust iterations: {}", trainer.iterations_trained);
    println!("Rust infosets: {}", trainer.nodes.len());

    // Create Rust CFR agent.
    let mut rust_agent = CFRAgent::new(
        &trainer.nodes,
        &trainer.memory_cache,
        123,
        Some("Rust CFR"),
    );

    // Start Python CFR agent.
    println!("Starting Python CFR agent...");

    let mut python_agent = PythonAgentBridge::new(
        "python",
        PROJECT_ROOT,
    )?;

    // Both agents implement MatchAgent.
    let mut agents: [&mut dyn MatchAgent; 2] = [
        &mut rust_agent,
        &mut python_agent,
    ];

    println!("\n--- Rust CFR vs Python CFR Tournament ---");
    println!("Hands per seating: {HANDS_PER_SEATING}");
    println!("Total hands: {}", HANDS_PER_SEATING * 2);

    let start = Instant::now();

    let tournament = run_tournament(
        &mut agents,
        HANDS_PER_SEATING,
        2026,
    )
    .map_err(|error| std::io::Error::other(format!("{error:?}")))?;

    let elapsed = start.elapsed();

    // Exactly one pairing: Rust vs Python.
    let result = &tournament.pairings[0];

    let average = result.average_payoff_a();
    let ci = result.ci95_half_width();

    println!("\n--- Tournament Results ---");

    println!("Match: {} vs {}", result.agent_a, result.agent_b);
    println!("Hands: {}", result.hands);

    println!("Rust wins: {}", result.wins_a);
    println!("Python wins: {}", result.wins_b);
    println!("Draws: {}", result.draws);

    println!("\n--- Payoff Statistics ---");

    println!("Rust total payoff: {:+.2}", result.payoff_sum_a);
    println!("Rust average payoff/hand: {average:+.6}");
    println!("95% CI half-width: +/-{ci:.6}");

    println!(
        "95% CI: [{:+.6}, {:+.6}]",
        average - ci,
        average + ci
    );

    println!("\n--- Seat Performance ---");

    println!(
        "Rust as player 0: {:+.6} chips/hand",
        result.a_as_player0.payoff_sum[0]
            / result.a_as_player0.hands as f64
    );

    println!(
        "Rust as player 1: {:+.6} chips/hand",
        result.a_as_player1.payoff_sum[1]
            / result.a_as_player1.hands as f64
    );

    println!("\n--- Performance ---");

    println!("Elapsed: {:.2?}", elapsed);
    println!(
        "Hands/second: {:.2}",
        result.hands as f64 / elapsed.as_secs_f64()
    );

    println!("\nTournament completed successfully!");

    Ok(())
}
