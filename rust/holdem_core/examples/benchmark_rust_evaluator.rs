use std::time::Instant;


use holdem_core::python_evaluator::evaluate_python_hand;


fn main() {
    let iterations = 5;
    
    let card_arrays = load_csv("/home/richard.dunbar101/Projects/LiteHoldemPoker/benchmarks/evaluator_reference.csv");
    

    let mut times = Vec::new();
    let mut checksums = Vec::new();

    
    
    
    for iter_no in 0..iterations {

        let start = Instant::now();

        let mut checksum :u64 = 0;
        
        for hand in card_arrays.iter() {
            let hand_value = evaluate_python_hand(
                std::hint::black_box(hand)
            );
            
            checksum += sum_results(&hand_value);
        }

        let elapsed = start.elapsed().as_secs_f64();

        times.push(elapsed);

        println!(
            "Run {}: Time taken: {:.4}ms, Evaluations per second: {:.0}",
            iter_no + 1,
            elapsed * 1000.0,
            card_arrays.len() as f64 / elapsed
        );

        checksums.push(checksum);


    }

    assert!(
        checksums.iter().all(|&c| c == checksums[0]),
        "Checksums differ between runs!"
    );

    times.sort_by(f64::total_cmp);

    let fastest = times[0];
    let slowest = times[times.len() - 1];
    let median = times[times.len() / 2]; // For 5 runs

    let evaluations_per_sec = card_arrays.len() as f64 / median;

    println!("\n--- Benchmark Summary ---");
    println!("Total hands:       {}", card_arrays.len());
    println!("Fastest time:      {:.4}s", fastest);
    println!("Median time:       {:.4}s", median);
    println!("Slowest time:      {:.4}s", slowest);
    println!("Evaluations/sec:   {:.0}", evaluations_per_sec);
    println!("Checksum:          {}", checksums[0]);

    
    
}




fn load_csv(path: &str) -> Vec<[u8; 7]> {
    let mut reader = csv::Reader::from_path(path).unwrap();

    reader.records().map(|result| {
        let record = result.unwrap();
        let mut card_array = [0u8; 7];
        for i in 0..7 {
            card_array[i] = record[i].parse().unwrap();
        }
        card_array
    }).collect()
}



fn sum_results(results: &(u8, [u8; 5])) -> u64 {
    let (category, kickers) = results;

    let kicker_sum: u64 = kickers
        .iter()
        .map(|&k| {
            if k == 0 {
                0
            } else {
                (k - 10) as u64
            }
        })
        .sum();

    (*category as u64) + kicker_sum
}
