use holdem_core::equity_cache_access::{Cache,MemoryCache};
use holdem_core::cards::{Card,create_deck};


use std::time::Instant;
use std::hint::black_box;

use rand::seq::SliceRandom;
use rand::SeedableRng;
use rand::rngs::StdRng;




fn main() {
    const LOOKUPS: usize = 100_000;



    // 1. Open your existing equity_cache_rust.sqlite database
    let cache = Cache::new("/home/richard.dunbar101/Projects/LiteHoldemPoker/cache/equity_cache_rust.sqlite").unwrap();
    

    // 2. Prepare a collection of valid private hands and boards
    let cards = create_deck();
    let mut states: Vec<([Card; 2], Vec<Card>)> =
        Vec::with_capacity(LOOKUPS);

    'generate: for a in 0..cards.len() {
        for b in (a + 1)..cards.len() {
            let player_cards = [cards[a], cards[b]];

            // Remove the two private cards
            let remaining: Vec<Card> = cards
                .iter()
                .copied()
                .filter(|card| !player_cards.contains(card))
                .collect();

            // Generate unique three-card boards
            for i in 0..remaining.len() {
                for j in (i + 1)..remaining.len() {
                    for k in (j + 1)..remaining.len() {
                        let board_cards = vec![
                            remaining[i],
                            remaining[j],
                            remaining[k],
                        ];

                        states.push((player_cards, board_cards));

                        if states.len() == LOOKUPS {
                            break 'generate;
                        }
                    }
                }
            }
        }
    }

    let mut rng = StdRng::seed_from_u64(69); //hehe

    states.shuffle(&mut rng);

    assert_eq!(states.len(), LOOKUPS);

    // 3. Start the timer
    let memory_cache: MemoryCache = cache.load_into_memory().unwrap();

    assert_eq!(memory_cache.len(), 2_364_550);

    let start = Instant::now();
    let mut checksum: f64 = 0.0;

    // 4. Perform 100,000 cache lookups
    
    

    for (private_cards, board_cards) in &states {

        let equity = memory_cache
            .get_equity_score(private_cards, board_cards)
            .expect("Missing equity result");

        checksum += black_box(equity);
    }

    // 5. Stop the timer
    let elapsed = start.elapsed().as_secs_f64();

    // 6. Print the performance summary
    println!("\n--- SQLite Cache Benchmark Summary ---");
    println!("Total lookups:     {}", LOOKUPS);
    println!("Total time:        {:.4}s", elapsed);
    println!("Lookups/sec:       {:.0}", LOOKUPS as f64 / elapsed);
    println!("Time per lookup:   {:.3}µs", elapsed * 1_000_000.0 / LOOKUPS as f64);
    println!("Checksum:          {:.6}", checksum);
}