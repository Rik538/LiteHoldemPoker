import csv
from pathlib import Path
from itertools import combinations

# Replace with the actual import from your project
from lite_holdem_ai.game.evaluate_hand import EvaluateHand


def generate_reference():
    evaluator = EvaluateHand()

    # Assumes Python card IDs run from 0 to 19
    deck = list(range(20))

    output = Path("benchmarks/evaluator_reference.csv")
    output.parent.mkdir(parents=True, exist_ok=True)

    count = 0

    with output.open("w", newline="") as file:
        writer = csv.writer(file)

        writer.writerow(
            [f"card_{i}" for i in range(7)]
            + ["category"]
            + [f"kicker_{i}" for i in range(5)]
        )

        for cards in combinations(deck, 7):
            private_cards = list(cards[:2])
            public_cards = list(cards[2:])

            category, kickers = evaluator.evaluate(private_cards, public_cards)

            # Convert Python ranks (0-4) to Rust ranks (10-14)
            normalised_kickers = [rank + 10 for rank in kickers]

            # Pad to five elements
            normalised_kickers += [0] * (5 - len(normalised_kickers))

            writer.writerow(list(cards) + [int(category)] + normalised_kickers)

            count += 1

    print(f"Generated {count:,} reference hands")
    print(f"Saved to {output}")


if __name__ == "__main__":
    generate_reference()
