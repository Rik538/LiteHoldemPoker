# -*- coding: utf-8 -*-
"""
Created on Wed Jun  3 20:03:46 2026

@author: Richard
"""

from pathlib import Path

from lite_holdem_ai.equity import build_equity_cache


def main():
    cache_path = Path("cache") / "equity_cache.sqlite"
    cache_path.parent.mkdir(exist_ok=True)

    build_equity_cache(
        path=cache_path,
        board_sizes=[0,3,4,5],
        batch_size=100,
        clear_existing=True,
        verbose=True,
    )


if __name__ == "__main__":
    main()