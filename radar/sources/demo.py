"""Deterministic synthetic data source.

Generates believable product snapshots with a stable PRNG seed, so demos,
tests and CI run anywhere without network access. Review counts grow over
time (seeded by date), which lets the trend score show real movement when
you run `radar demo` today and again tomorrow.
"""

from __future__ import annotations

import random
import time
import unicodedata

from ..models import ProductSnapshot
from .base import Source

_ADJECTIVES = ["Silk", "Volumizing", "Argan", "Biotin", "Repair", "Herbal"]
_NOUNS = ["Shampoo", "Conditioner", "Hair Mask", "Hair Oil", "Body Wash"]
_BRANDS = ["Lumora", "Kavesse", "Nuvella", "Orielle", "Vantura"]
_CURRENCIES = ["USD", "USD", "USD", "EUR"]


class DemoSource(Source):
    name = "demo"

    def __init__(self, source_name: str = "demo", seed: int | None = None):
        # seed drifts with the calendar day so review counts grow daily
        day = int(time.time() // 86400)
        self.seed = seed if seed is not None else day * 1000 + hash(source_name) % 1000
        self.source_name = source_name

    def fetch(self, keyword: str, max_results: int = 10) -> list[ProductSnapshot]:
        rng = random.Random(self.seed + sum(map(ord, unicodedata.normalize("NFKD", keyword))))
        now = time.time()
        out: list[ProductSnapshot] = []
        for i in range(max_results):
            brand = rng.choice(_BRANDS)
            adj = rng.choice(_ADJECTIVES)
            noun = rng.choice(_NOUNS)
            title = f"{brand} {adj} {noun} - 500ml"
            pid = f"{brand[:3].upper()}-{i:03d}"
            base_reviews = rng.randint(80, 6000)
            rating = round(rng.uniform(3.6, 4.9), 1)
            price = round(rng.uniform(6.9, 39.9), 2)
            rank = rng.randint(1, 8000) if rng.random() < 0.7 else None
            out.append(
                ProductSnapshot(
                    source=self.source_name,
                    product_id=pid,
                    keyword=keyword,
                    title=title,
                    price=price,
                    currency=rng.choice(_CURRENCIES),
                    rating=rating,
                    reviews=base_reviews,
                    rank=rank,
                    ts=now,
                )
            )
        return out
