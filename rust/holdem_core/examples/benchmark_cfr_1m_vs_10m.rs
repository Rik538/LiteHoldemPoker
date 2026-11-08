//! Run a seat-balanced tournament between two saved Rust MCCFR checkpoints.
//! Put this file in holdem_core/examples/ and run with:
//! cargo run --release -p holdem_core --example benchmark_cfr_1m_vs_10m

use std::path::Path;

use holdem_core::agents::cfr_agent::CFRAgent;
use holdem_core::cfr::checkpoint::MCCFRCheckpoint;
use holdem_core::equity_cache_access::Cache;
use holdem_core::runners::{run_tournament, MatchAgent};
use holdem_core::agents::cached_bucket_equity_agent::CachedBucketEquityAgent;

const CACHE_PATH: &str =
    "/home/richard.dunbar101/Projects/LiteHoldemPoker/cache/equity_cache_rust.sqlite";
const CHECKPOINT_1M: &str =
    "/home/richard.dunbar101/Projects/LiteHoldemPoker/checkpoints/rs_1M.bin";
// Assumed filename: adjust if your 10M checkpoint is named differently.
const CHECKPOINT_10M: &str =
    "/home/richard.dunbar101/Projects/LiteHoldemPoker/checkpoints/rs_10M.bin";

const HANDS_PER_SEATING: usize = 50_000; // 100,000 hands total
const TOURNAMENT_SEED: u64 = 123;

fn read_checkpoint(path: &str) -> MCCFRCheckpoint {
    let bytes = std::fs::read(Path::new(path))
        .unwrap_or_else(|error| panic!("Cannot read checkpoint {path}: {error}"));

    let (checkpoint, bytes_read): (MCCFRCheckpoint, usize) = bincode::decode_from_slice(
        &bytes,
        bincode::config::standard(),
    )
    .unwrap_or_else(|error| panic!("Cannot decode checkpoint {path}: {error}"));

    assert_eq!(checkpoint.version, 1, "Unsupported checkpoint version in {path}");
    assert_eq!(bytes_read, bytes.len(), "Trailing bytes in checkpoint {path}");
    checkpoint
}

fn main() {
    // Decode just the trained nodes: do not load another 2.36M-entry cache per agent.
    let checkpoint_1m = read_checkpoint(CHECKPOINT_1M);
    let checkpoint_10m = read_checkpoint(CHECKPOINT_10M);

    println!("1M checkpoint iterations:  {}", checkpoint_1m.iterations_trained);
    println!("10M checkpoint iterations: {}", checkpoint_10m.iterations_trained);
    println!("1M infosets:  {}", checkpoint_1m.nodes.len());
    println!("10M infosets: {}", checkpoint_10m.nodes.len());

    let cache = Cache::new(CACHE_PATH).expect("Failed to open equity SQLite cache");
    let memory_cache = cache
        .load_into_memory()
        .expect("Failed to load equity values into RAM");
    assert_eq!(memory_cache.len(), 2_364_550);

    let mut agent_1m = CFRAgent::new(
        &checkpoint_1m.nodes,
        &memory_cache,
        101,
        Some("CFR 1M"),
    );
    let mut agent_10m = CFRAgent::new(
        &checkpoint_10m.nodes,
        &memory_cache,
        202,
        Some("CFR 10M"),
    );


    let mut equity_agent = CachedBucketEquityAgent::new(
        &memory_cache,
        None,
    );


    let mut agents: [&mut dyn MatchAgent; 3] = [&mut agent_1m, &mut agent_10m, &mut equity_agent];
    let results = run_tournament(&mut agents, HANDS_PER_SEATING, TOURNAMENT_SEED)
        .expect("Tournament failed");

    for pair in &results.pairings {
        println!("\n--- {} vs {} ---", pair.agent_a, pair.agent_b);
        println!("Hands:                  {}", pair.hands);
        println!("{} wins:             {}", pair.agent_a, pair.wins_a);
        println!("{} wins:            {}", pair.agent_b, pair.wins_b);
        println!("Draws:                  {}", pair.draws);
        println!("{} avg payoff/hand: {:+.6}", pair.agent_a, pair.average_payoff_a());
        println!("95% CI half-width:      +/-{:.6}", pair.ci95_half_width());
        println!("1M as player 0 payoff: {:+.6}", pair.a_as_player0.average_payoff(0));
        println!("1M as player 1 payoff: {:+.6}", pair.a_as_player1.average_payoff(1));
        println!("Button counts, leg 1:  {:?}", pair.a_as_player0.button_counts);
        println!("Button counts, leg 2:  {:?}", pair.a_as_player1.button_counts);
    }

    println!("\nCFR 1M:  decisions={}, missing_nodes={}", agent_1m.decisions, agent_1m.missing_nodes);
    println!("CFR 10M: decisions={}, missing_nodes={}", agent_10m.decisions, agent_10m.missing_nodes);
}
