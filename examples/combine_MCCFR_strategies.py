# -*- coding: utf-8 -*-
"""
Created on Mon Jun 22 18:13:03 2026

@author: Richard
"""

from pathlib import Path
from lite_holdem_ai.cfr.combine_MCCFR_strategies import CombineMCCFRStrategies

def main():
    
    combine_strategies = CombineMCCFRStrategies()
    
    checkpoint_dir = Path("checkpoints")

    input_paths = [
        checkpoint_dir / "lite_holdem_nohist_500k_seed1.pkl",
        checkpoint_dir / "lite_holdem_nohist_500k_seed2.pkl",
        checkpoint_dir / "lite_holdem_nohist_500k_seed3.pkl",
    ]

    output_path = checkpoint_dir / "lite_holdem_nohist_500k_seedavg_1to3.pkl"

    result = combine_strategies.average_checkpoints(
        input_paths=input_paths,
        output_path=output_path,
    )

    print(f"Saved averaged checkpoint to: {result}")


if __name__ == "__main__":
    main()