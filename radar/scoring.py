"""Trend scoring.

The score blends four signals, all computed from snapshot history:

- review_velocity : reviews gained per day over the observed window
  (demand proxy — people who buy rarely bother to review)
- rating          : absolute star rating (quality proxy)
- price_stability : 1 - normalized price fluctuation (stable price
  suggests a healthy, non-clearance listing)
- rank_improvement: category rank getting better over time

Weights are configurable in config.toml and normalized to sum to 1.
"""

from __future__ import annotations

from .models import ProductSnapshot, TrendResult

_MIN_SNAPSHOTS = 1


def _clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def review_velocity(history: list[ProductSnapshot]) -> float:
    """Reviews/day between earliest and latest snapshot; 0 if not enough data."""
    with_reviews = sorted(
        (s for s in history if s.reviews is not None), key=lambda s: s.ts
    )
    if len(with_reviews) < 2:
        return 0.0
    first, last = with_reviews[0], with_reviews[-1]
    days = max(last.ts - first.ts, 1.0) / 86400
    gained = max(last.reviews - first.reviews, 0)
    return gained / days


def price_change_pct(history: list[ProductSnapshot]) -> float | None:
    prices = [s.price for s in sorted(history, key=lambda s: s.ts) if s.price is not None]
    if len(prices) < 2 or prices[0] == 0:
        return None
    return (prices[-1] - prices[0]) / prices[0] * 100


def rank_change(history: list[ProductSnapshot]) -> int | None:
    ranks = [s.rank for s in sorted(history, key=lambda s: s.ts) if s.rank is not None]
    if len(ranks) < 2:
        return None
    return ranks[-1] - ranks[0]  # negative = rank improved


def score_product(
    history: list[ProductSnapshot],
    weights: dict[str, float],
    velocity_norm: float = 30.0,
) -> TrendResult:
    """Compute a 0-100 trend score.

    velocity_norm: review_velocity (reviews/day) mapped to [0,1] by
    dividing with this constant — 30/day ≈ "hot" for a mid-tail product.
    """
    if len(history) < _MIN_SNAPSHOTS:
        raise ValueError("need at least one snapshot")

    w = dict(weights)
    total = sum(w.values()) or 1.0
    w = {k: v / total for k, v in w.items()}

    vel = review_velocity(history)
    latest = history[-1]
    rating = latest.rating

    s_velocity = _clamp(vel / velocity_norm)
    s_rating = _clamp((rating or 0.0) / 5.0)
    change = price_change_pct(history)
    # |Δprice| >= 30% => stability 0
    s_price = 1.0 - _clamp(abs(change or 0.0) / 30.0)
    rc = rank_change(history)
    s_rank = _clamp(-rc / 500.0) if rc is not None else 0.5  # neutral: 0.5

    score = 100 * (
        w.get("review_velocity", 0) * s_velocity
        + w.get("rating", 0) * s_rating
        + w.get("price_stability", 0) * s_price
        + w.get("rank_improvement", 0) * s_rank
    )

    return TrendResult(
        source=latest.source,
        product_id=latest.product_id,
        title=latest.title,
        score=round(score, 1),
        review_velocity=round(vel, 2),
        rating=rating,
        price_change_pct=None if change is None else round(change, 1),
        rank_change=rc,
        snapshot_count=len(history),
        last_price=latest.price,
        currency=latest.currency,
    )
