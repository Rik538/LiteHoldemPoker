
use holdem_core::agents::cfr_agent::CFRAgent;
use holdem_core::agents::cached_bucket_equity_agent::CachedBucketEquityAgent;

use holdem_core::cfr::trainer::MCCFRTrainer;
use holdem_core::equity_cache_access::Cache;
use holdem_core::state::GameState;

use rand::rngs::StdRng;
use rand::SeedableRng;

use std::path::Path;

fn main() {
    const HANDS: usize = 10_000;

    // Load equity cache
    let cache = Cache::new(
        "/home/richard.dunbar101/Projects/LiteHoldemPoker/cache/equity_cache_rust.sqlite"
    ).unwrap();

    let memory_cache = cache.load_into_memory().unwrap();

    // Restore trained MCCFR nodes
    let trainer = MCCFRTrainer::load_checkpoint(
        Path::new("/home/richard.dunbar101/Projects/LiteHoldemPoker/checkpoints/rs_1M.bin"),
        memory_cache,
        69,
    ).unwrap();

    let mut cfr_agent = CFRAgent::new(
        &trainer.nodes,
        &trainer.memory_cache,
        69,
        Some("Rust CFR"),
    );

    let mut equity_agent = CachedBucketEquityAgent::new(
        &trainer.memory_cache,
        None,
    );

    let mut rng = StdRng::seed_from_u64(123);
    let mut state = GameState::new();

    let mut total_payoff = 0.0;
    let mut wins = 0;
    let mut losses = 0;
    let mut draws = 0;

    for _ in 0..HANDS {
        state.start_hand(&mut rng).unwrap();

        while !state.terminal {
            let player = state.current_player;

            let observation = state
                .get_observation(&player)
                .unwrap();

            let action = if player == 0 {
                cfr_agent.select_action(
                    &observation,
                    &observation.legal_actions,
                ).unwrap()
            } else {
                equity_agent.select_action(
                    &observation,
                    &observation.legal_actions,
                ).unwrap()
            };

            state.apply_action(action).unwrap();
        }

        let payoff = state.payoffs[0];
        total_payoff += payoff;

        if payoff > 0.0 {
            wins += 1;
        } else if payoff < 0.0 {
            losses += 1;
        } else {
            draws += 1;
        }
    }

    println!("\n--- CFR vs Cached Bucket Equity ---");
    println!("Hands played: {}", HANDS);
    println!("CFR wins:     {}", wins);
    println!("Equity wins:  {}", losses);
    println!("Draws:        {}", draws);

    println!(
        "CFR avg payoff: {:.6}",
        total_payoff / HANDS as f64
    );

    println!("CFR decisions: {}", cfr_agent.decisions);
    println!("Missing nodes: {}", cfr_agent.missing_nodes);
    println!("Equity decisions: {}", equity_agent.decisions);
}
