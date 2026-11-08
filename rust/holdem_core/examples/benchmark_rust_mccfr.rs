
use holdem_core::equity_cache_access::Cache;
use holdem_core::cfr::trainer::MCCFRTrainer;

use std::path::Path;
use std::time::Instant;

fn main() {
    const ITERATIONS: usize = 10_000_000;
    const PRINT_EVERY: usize = 100_000;
    const SEED: u64 = 69;
    const SAVE_EVERY: usize = 100_000;
    let path: &Path = Path::new("/home/richard.dunbar101/Projects/LiteHoldemPoker/checkpoints/rs_10M.bin");

    // 1. Locate the existing SQLite equity cache
    let cache_path = Path::new("/home/richard.dunbar101/Projects/LiteHoldemPoker/cache/equity_cache_rust.sqlite");

    assert!(
        cache_path.exists(),
        "Equity cache not found at {:?}",
        cache_path
    );

    // 2. Load the cache into memory
    let cache = Cache::new(
        cache_path.to_str().unwrap()
    ).expect("Failed to open SQLite cache");

    let memory_cache = cache
        .load_into_memory()
        .expect("Failed to load memory cache");

    assert_eq!(memory_cache.len(), 2_364_550);

    println!("Equity cache loaded successfully.");

    // 3. Initialise the MCCFR trainer
    let mut trainer = MCCFRTrainer::new(
        memory_cache,
        SEED,
    );

    // 4. Start benchmark timer
    let start = Instant::now();

    // 5. Train using the same settings as Python
    trainer.train(
        ITERATIONS,
        Some(PRINT_EVERY),
        true,
        Some(path),
        Some(SAVE_EVERY),
    ).expect("MCCFR training failed");

    // 6. Calculate performance
    let elapsed = start.elapsed().as_secs_f64();

    // 7. Display results
    println!("\n--- Rust MCCFR Benchmark Summary ---");
    println!("Trainer:          External Sampling MCCFR");
    println!("Iterations:       {}", ITERATIONS);
    println!("Infosets:         {}", trainer.nodes.len());
    println!("Elapsed:          {:.2}s", elapsed);
    println!(
        "Iterations/sec:   {:.2}",
        ITERATIONS as f64 / elapsed
    );
}
