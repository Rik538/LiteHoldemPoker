import time
from pathlib import Path

from lite_holdem_ai.equity import build_equity_cache
from lite_holdem_ai.equity.cache import EquityCache

EXPECTED_RECORDS = {
    0: 190,
    3: 155_040,
    4: 581_400,
    5: 1_627_920,
}

BATCH_SIZE = 5000


def main():
    cache_path = Path("cache") / "equity_cache_python_benchmark.sqlite"
    cache_path.parent.mkdir(parents=True, exist_ok=True)

    total_start = time.perf_counter()
    results = []

    print("=== Python Full Equity Cache Benchmark ===")

    for board_size, expected_records in EXPECTED_RECORDS.items():

        print(f"\nBuilding board size {board_size}...")

        start = time.perf_counter()

        build_equity_cache(
            path=cache_path,
            board_sizes=[board_size],
            batch_size=BATCH_SIZE,
            clear_existing=(board_size == 0),
            verbose=False,
        )

        elapsed = time.perf_counter() - start

        # Verify records were stored
        with EquityCache(cache_path) as cache:
            actual_records = cache.count(board_size)

        assert actual_records == expected_records, (
            f"Board {board_size}: expected {expected_records}, " f"got {actual_records}"
        )

        records_per_sec = actual_records / elapsed

        results.append((board_size, actual_records, elapsed, records_per_sec))

        print(f"Records:       {actual_records:,}")
        print(f"Time:          {elapsed:.4f}s")
        print(f"Records/sec:   {records_per_sec:,.0f}")

    total_elapsed = time.perf_counter() - total_start
    total_records = sum(result[1] for result in results)

    print("\n--- Python Cache Benchmark Summary ---")

    for board_size, records, elapsed, rate in results:
        print(
            f"Board {board_size}: "
            f"{records:,} records | "
            f"{elapsed:.2f}s | "
            f"{rate:,.0f} records/sec"
        )

    print("\n--- Full Cache Summary ---")
    print(f"Total records:     {total_records:,}")
    print(f"Total time:        {total_elapsed:.2f}s")
    print(f"Total minutes:     {total_elapsed / 60:.2f}")
    print(f"Total hours:       {total_elapsed / 3600:.2f}")
    print(f"Records/sec:       {total_records / total_elapsed:,.0f}")
    print(f"Database size:     {cache_path.stat().st_size / 1_000_000:.2f} MB")
    print("Validation:        PASSED")


if __name__ == "__main__":
    main()
