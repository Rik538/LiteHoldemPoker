

import random
from dataclasses import dataclass
from pathlib import Path


@dataclass
class MultiseedTrainingResult:
    seed: int
    checkpoint_path: Path | None
    iterations_trained: int
    infosets: int


class MultiseedMCCFRTrainer:
    def __init__(
        self,
        trainer_factory,
        seed: int | None = None,
    ):
       
        self.trainer_factory = trainer_factory
        self.rng = random.Random(seed)

    def seed_checkpoint_path(self, base_path, seed):
        if base_path is None:
            return None

        base_path = Path(base_path)

        return base_path.with_name(
            f"{base_path.stem}_seed{seed}{base_path.suffix}"
        )

    def train(
        self,
        iterations: int,
        path=None,
        save_every: int | None = 1000,
        print_every: int | None = 100,
        update_both_players: bool = True,
        average_starting_iteration: int = 0,
        seeds: int | list[int] = 5,
        print_strategies_limit: int | None = None,
    ):
        if isinstance(seeds, int):
            seed_values = list(range(1, seeds + 1))
        else:
            seed_values = list(seeds)

        results = []

        for current_seed in seed_values:
            print()
            print("-" * 40)
            print(f"Training seed {current_seed}")

            seed_path = self.seed_checkpoint_path(path, current_seed)

            trainer = self.trainer_factory(current_seed)

            trainer.train(
                iterations=iterations,
                path=seed_path,
                save_every=save_every,
                print_every=print_every,
                update_both_players=update_both_players,
                averaging_start_iteration=average_starting_iteration,
            )

            result = MultiseedTrainingResult(
                seed=current_seed,
                checkpoint_path=seed_path,
                iterations_trained=trainer.iterations_trained,
                infosets=len(trainer.nodes),
            )
            results.append(result)

            print()
            print(f"Training complete for seed {current_seed}.")
            print(f"Iterations trained: {trainer.iterations_trained}")
            print(f"Infosets: {len(trainer.nodes)}")

            if seed_path is not None:
                print(f"Saved checkpoint to: {seed_path}")

            if print_strategies_limit is not None:
                print()
                print("Sample strategies:")
                trainer.print_strategies(limit=print_strategies_limit)

            if hasattr(trainer, "close"):
                trainer.close()

        print()
        print("-" * 40)
        print("Multiseed training complete")

        return results