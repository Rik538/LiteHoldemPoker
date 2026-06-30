# -*- coding: utf-8 -*-
"""
SQLite-backed equity cache for Lite Hold'em.

The cache stores exact equity results for canonical private/public card
combinations.

Private and public cards are canonicalised by sorting, so these are equivalent:

    private=[16, 17], public=[0, 4, 8]
    private=[17, 16], public=[8, 0, 4]
"""

from __future__ import annotations

import sqlite3
from pathlib import Path


class EquityCache:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

        self.connection = sqlite3.connect(self.path)
        self.create_schema()

    def create_schema(self) -> None:
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS equity_cache (
                private_key TEXT NOT NULL,
                public_key TEXT NOT NULL,
                board_size INTEGER NOT NULL,
                equity REAL NOT NULL,
                bucket INTEGER NOT NULL,
                wins INTEGER NOT NULL,
                losses INTEGER NOT NULL,
                splits INTEGER NOT NULL,
                total INTEGER NOT NULL,
                PRIMARY KEY (private_key, public_key)
            )
            """
        )

        self.connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_equity_cache_board_size
            ON equity_cache (board_size)
            """
        )

        self.connection.commit()

    def close(self) -> None:
        self.connection.close()

    def __enter__(self) -> "EquityCache":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()

    def card_key(self, cards) -> str:
        return ",".join(str(card) for card in sorted(cards))

    def make_key(self, private_cards, public_cards) -> tuple[str, str]:
        private_key = self.card_key(private_cards)
        public_key = self.card_key(public_cards)
        return private_key, public_key

    def contains(self, private_cards, public_cards) -> bool:
        private_key, public_key = self.make_key(private_cards, public_cards)

        cursor = self.connection.execute(
            """
            SELECT 1
            FROM equity_cache
            WHERE private_key = ? AND public_key = ?
            LIMIT 1
            """,
            (private_key, public_key),
        )

        return cursor.fetchone() is not None

    def set(self, private_cards, public_cards, result: dict, bucket: int) -> None:
        private_key, public_key = self.make_key(private_cards, public_cards)

        self.connection.execute(
            """
            INSERT OR REPLACE INTO equity_cache (
                private_key,
                public_key,
                board_size,
                equity,
                bucket,
                wins,
                losses,
                splits,
                total
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                private_key,
                public_key,
                len(public_cards),
                float(result["equity"]),
                int(bucket),
                int(result["wins"]),
                int(result["losses"]),
                int(result["splits"]),
                int(result["total"]),
            ),
        )

        self.connection.commit()

    def set_many(self, records) -> None:
        """
        Insert many records efficiently.

        Each record should be:
            (private_cards, public_cards, result, bucket)
        """
        rows = []

        for private_cards, public_cards, result, bucket in records:
            private_key, public_key = self.make_key(private_cards, public_cards)

            rows.append(
                (
                    private_key,
                    public_key,
                    len(public_cards),
                    float(result["equity"]),
                    int(bucket),
                    int(result["wins"]),
                    int(result["losses"]),
                    int(result["splits"]),
                    int(result["total"]),
                )
            )

        self.connection.executemany(
            """
            INSERT OR REPLACE INTO equity_cache (
                private_key,
                public_key,
                board_size,
                equity,
                bucket,
                wins,
                losses,
                splits,
                total
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )

        self.connection.commit()

    def get(self, private_cards, public_cards) -> dict:
        private_key, public_key = self.make_key(private_cards, public_cards)

        cursor = self.connection.execute(
            """
            SELECT equity, bucket, wins, losses, splits, total
            FROM equity_cache
            WHERE private_key = ? AND public_key = ?
            """,
            (private_key, public_key),
        )

        row = cursor.fetchone()

        if row is None:
            raise KeyError(
                f"Missing equity cache entry for "
                f"private={list(private_cards)}, public={list(public_cards)}"
            )

        equity, bucket, wins, losses, splits, total = row

        return {
            "equity": equity,
            "bucket": bucket,
            "wins": wins,
            "losses": losses,
            "splits": splits,
            "total": total,
        }

    def count(self, board_size: int | None = None) -> int:
        if board_size is None:
            cursor = self.connection.execute(
                "SELECT COUNT(*) FROM equity_cache"
            )
        else:
            cursor = self.connection.execute(
                """
                SELECT COUNT(*)
                FROM equity_cache
                WHERE board_size = ?
                """,
                (board_size,),
            )

        return int(cursor.fetchone()[0])

    def clear(self) -> None:
        self.connection.execute("DELETE FROM equity_cache")
        self.connection.commit()
        
class InMemoryEquityCache:
    """
    Dict-backed equity cache loaded from a SQLite EquityCache.

    Use this for training/evaluation hot paths where repeated SQLite queries
    are too slow.
    """

    def __init__(self, rows):
        self.data = {}
        self.counts_by_board_size = {}

        for row in rows:
            (
                private_key,
                public_key,
                board_size,
                equity,
                bucket,
                wins,
                losses,
                splits,
                total,
            ) = row

            key = (private_key, public_key)

            self.data[key] = (
                equity,
                bucket,
                wins,
                losses,
                splits,
                total,
            )

            self.counts_by_board_size[board_size] = (
                self.counts_by_board_size.get(board_size, 0) + 1
            )

    @classmethod
    def from_sqlite(cls, path: str | Path) -> "InMemoryEquityCache":
        sqlite_cache = EquityCache(path)

        try:
            cursor = sqlite_cache.connection.execute(
                """
                SELECT
                    private_key,
                    public_key,
                    board_size,
                    equity,
                    bucket,
                    wins,
                    losses,
                    splits,
                    total
                FROM equity_cache
                """
            )

            return cls(cursor.fetchall())

        finally:
            sqlite_cache.close()

    def card_key(self, cards) -> str:
        return ",".join(str(card) for card in sorted(cards))

    def make_key(self, private_cards, public_cards) -> tuple[str, str]:
        private_key = self.card_key(private_cards)
        public_key = self.card_key(public_cards)
        return private_key, public_key

    def contains(self, private_cards, public_cards) -> bool:
        return self.make_key(private_cards, public_cards) in self.data

    def get(self, private_cards, public_cards) -> dict:
        key = self.make_key(private_cards, public_cards)

        try:
            equity, bucket, wins, losses, splits, total = self.data[key]
        except KeyError:
            raise KeyError(
                f"Missing equity cache entry for "
                f"private={list(private_cards)}, public={list(public_cards)}"
            )

        return {
            "equity": equity,
            "bucket": bucket,
            "wins": wins,
            "losses": losses,
            "splits": splits,
            "total": total,
        }

    def count(self, board_size: int | None = None) -> int:
        if board_size is None:
            return len(self.data)

        return self.counts_by_board_size.get(board_size, 0)

    def close(self) -> None:
        pass

    def __enter__(self) -> "InMemoryEquityCache":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()