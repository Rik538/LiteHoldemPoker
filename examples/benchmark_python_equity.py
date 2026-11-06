import time
import statistics

# Adjust this import to match your project structure
from lite_holdem_ai.equity.builder import EquityCacheBuilder

RUNS = 5

# A♥ K♦ using your 20-card deck's ID mapping
PLAYER_CARDS = [18, 13]
PUBLIC_CARDS = []


def benchmark_equity():
    builder = EquityCacheBuilder()

    times = []
    results = []

    print("=== Python Preflop Equity Benchmark ===")
    print(f"Player cards: {PLAYER_CARDS}")
    print(f"Benchmark runs: {RUNS}\n")

    for run in range(RUNS):
        start = time.perf_counter()

        result = builder.calculate_equity(
            PLAYER_CARDS,
            PUBLIC_CARDS,
        )

        elapsed = time.perf_counter() - start

        times.append(elapsed)
        results.append(result)

        print(
            f"Run {run + 1}: "
            f"Time taken: {elapsed:.4f}s, "
            f"Scenarios per second: "
            f"{result['total'] / elapsed:,.0f}"
        )

    # Validate consistency across benchmark runs
    assert all(r == results[0] for r in results), "Equity results differ between runs!"

    result = results[0]

    assert result["total"] == 668_304
    assert result["wins"] + result["losses"] + result["splits"] == result["total"]

    median_time = statistics.median(times)

    print("\n--- Benchmark Summary ---")
    print(f"Total scenarios:   {result['total']:,}")
    print(f"Fastest time:      {min(times):.4f}s")
    print(f"Median time:       {median_time:.4f}s")
    print(f"Slowest time:      {max(times):.4f}s")
    print(f"Scenarios/sec:     " f"{result['total'] / median_time:,.0f}")

    print("\n--- Equity Results ---")
    print(f"Wins:              {result['wins']:,}")
    print(f"Losses:            {result['losses']:,}")
    print(f"Splits:            {result['splits']:,}")
    print(f"Equity:            {result['equity']:.8f}")


if __name__ == "__main__":
    benchmark_equity()
