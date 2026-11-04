import csv
import time
import statistics
from pathlib import Path

# Update this import to match your project
from lite_holdem_ai.game.evaluate_hand import EvaluateHand

CSV_PATH = Path("benchmarks/evaluator_reference.csv")
RUNS = 5
WARMUP_HANDS = 1000


def load_hands(path: Path):
    """Load all hands before benchmarking."""
    hands = []

    with path.open("r", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            cards = [int(row[f"card_{i}"]) for i in range(7)]

            private_cards = cards[:2]
            public_cards = cards[2:]

            hands.append((private_cards, public_cards))

    return hands


def benchmark_evaluator():
    hands = load_hands(CSV_PATH)
    evaluator = EvaluateHand()

    print(f"Loaded {len(hands):,} hands")
    print(f"Benchmark runs: {RUNS}")

    # Warm-up (not timed)
    for private, public in hands[:WARMUP_HANDS]:
        evaluator.evaluate(private, public)

    times = []
    checksums = []

    for run in range(RUNS):
        checksum = 0

        start = time.perf_counter()

        for private, public in hands:
            category, kickers = evaluator.evaluate(private, public)

            checksum += int(category) + sum(kickers)

        elapsed = time.perf_counter() - start

        times.append(elapsed)
        checksums.append(checksum)

        evaluations_per_sec = len(hands) / elapsed

        print(
            f"Run {run + 1}: "
            f"{elapsed:.4f}s | "
            f"{evaluations_per_sec:,.0f} evals/sec"
        )

    assert len(set(checksums)) == 1, "Inconsistent results"

    median_time = statistics.median(times)

    print("\n--- Benchmark Summary ---")
    print(f"Total hands:       {len(hands):,}")
    print(f"Fastest time:      {min(times):.4f}s")
    print(f"Median time:       {median_time:.4f}s")
    print(f"Slowest time:      {max(times):.4f}s")
    print(f"Evaluations/sec:   {len(hands) / median_time:,.0f}")
    print(f"Checksum:          {checksums[0]}")


if __name__ == "__main__":
    benchmark_evaluator()
