"""Core data models."""

from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class ProductSnapshot:
    """One observation of one product at one point in time.

    A "product" is identified by (source, product_id) — e.g. an ASIN on
    Amazon or a synthetic id in demo mode.
    """

    source: str
    product_id: str
    keyword: str
    title: str
    price: float | None = None       # in listing currency
    currency: str = "USD"
    rating: float | None = None      # 0.0 - 5.0
    reviews: int | None = None       # cumulative review count
    rank: int | None = None          # category best-seller rank (lower is better)
    ts: float = field(default_factory=time.time)

    @property
    def key(self) -> tuple[str, str]:
        return (self.source, self.product_id)


@dataclass
class TrendResult:
    """Trend score and components for one product."""

    source: str
    product_id: str
    title: str
    score: float                    # 0 - 100
    review_velocity: float          # reviews/day over the observed window
    rating: float | None
    price_change_pct: float | None  # vs first snapshot, None if unknown
    rank_change: int | None         # negative = improved
    snapshot_count: int = 0
    last_price: float | None = None
    currency: str = "USD"
