
use std::hint::black_box;
use std::time::Instant;

use holdem_core::cards::{Card, Rank, Suit};
use holdem_core::equity_builder::preflop_equity;

fn main() {
    const RUNS: usize = 5;

    let player_cards = [
        Card::new(Suit::Heart, Rank::Ace),
        Card::new(Suit::Diamond, Rank::King),
    ];

    let mut times = Vec::with_capacity(RUNS);
    let mut results = Vec::with_capacity(RUNS);

    println!("=== Rust Preflop Equity Benchmark ===");
    println!("Player cards: {:?}", player_cards);
    println!("Benchmark runs: {}\n", RUNS);

    for run in 0..RUNS {
        let start = Instant::now();

        let result = preflop_equity(black_box(&player_cards));

        let elapsed = start.elapsed().as_secs_f64();

        black_box(result);

        times.push(elapsed);
        results.push(result);

        let (_, _, _, total) = result.counts();

        println!(
            "Run {}: Time taken: {:.4}s, Scenarios per second: {:.0}",
            run + 1,
            elapsed,
            total as f64 / elapsed
        );
    }

    // Check consistency between runs
    assert!(
        results.iter().all(|r| *r == results[0]),
        "Equity results differ between runs!"
    );

    let result = results[0];
    let (wins, losses, splits, total) = result.counts();

    // Validate against known results
    assert_eq!(wins, 286_899);
    assert_eq!(losses, 219_102);
    assert_eq!(splits, 162_303);
    assert_eq!(total, 668_304);

    // Performance statistics
    times.sort_by(f64::total_cmp);

    let fastest = times[0];
    let median = times[RUNS / 2];
    let slowest = times[RUNS - 1];

    let scenarios_per_sec = total as f64 / median;

    println!("\n--- Benchmark Summary ---");
    println!("Total scenarios:   {}", total);
    println!("Fastest time:      {:.4}s", fastest);
    println!("Median time:       {:.4}s", median);
    println!("Slowest time:      {:.4}s", slowest);
    println!("Scenarios/sec:     {:.0}", scenarios_per_sec);

    println!("\n--- Equity Results ---");
    println!("Wins:              {}", wins);
    println!("Losses:            {}", losses);
    println!("Splits:            {}", splits);
    println!("Equity:            {:.8}", result.equity());
}
