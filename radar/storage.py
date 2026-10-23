"""SQLite persistence (stdlib sqlite3)."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from .models import ProductSnapshot

_SCHEMA = """
CREATE TABLE IF NOT EXISTS snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    product_id TEXT NOT NULL,
    keyword TEXT NOT NULL,
    title TEXT NOT NULL,
    price REAL,
    currency TEXT,
    rating REAL,
    reviews INTEGER,
    rank INTEGER,
    ts REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_snapshots_key
    ON snapshots (source, product_id, ts);
"""


class Storage:
    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.executescript(_SCHEMA)
        self.conn.commit()

    def save(self, snaps: list[ProductSnapshot]) -> int:
        rows = [
            (
                s.source, s.product_id, s.keyword, s.title,
                s.price, s.currency, s.rating, s.reviews, s.rank, s.ts,
            )
            for s in snaps
        ]
        self.conn.executemany(
            "INSERT INTO snapshots (source, product_id, keyword, title, price,"
            " currency, rating, reviews, rank, ts) VALUES (?,?,?,?,?,?,?,?,?,?)",
            rows,
        )
        self.conn.commit()
        return len(rows)

    def history(self, source: str, product_id: str) -> list[ProductSnapshot]:
        """All snapshots for a product, oldest first."""
        cur = self.conn.execute(
            "SELECT source, product_id, keyword, title, price, currency,"
            " rating, reviews, rank, ts FROM snapshots"
            " WHERE source=? AND product_id=? ORDER BY ts",
            (source, product_id),
        )
        return [ProductSnapshot(*row) for row in cur.fetchall()]

    def known_products(self) -> list[tuple[str, str, str]]:
        """(source, product_id, latest title) for every tracked product."""
        cur = self.conn.execute(
            "SELECT source, product_id, title FROM snapshots s"
            " WHERE ts = (SELECT MAX(ts) FROM snapshots x"
            "            WHERE x.source=s.source AND x.product_id=s.product_id)"
        )
        return cur.fetchall()

    def close(self) -> None:
        self.conn.close()
