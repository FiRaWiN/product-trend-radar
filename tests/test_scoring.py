import unittest

from radar.models import ProductSnapshot
from radar.scoring import (
    price_change_pct,
    rank_change,
    review_velocity,
    score_product,
)

DAY = 86400.0


def snap(reviews, price=None, rating=None, rank=None, days_ago=0, pid="P1"):
    import time

    return ProductSnapshot(
        source="demo", product_id=pid, keyword="k", title="T",
        price=price, rating=rating, reviews=reviews, rank=rank,
        ts=time.time() - DAY * days_ago,
    )


class TestScoring(unittest.TestCase):
    def test_review_velocity(self):
        hist = [snap(100, days_ago=10), snap(400, days_ago=0)]
        self.assertAlmostEqual(review_velocity(hist), 30.0)

    def test_review_velocity_insufficient(self):
        self.assertEqual(review_velocity([snap(100)]), 0.0)

    def test_price_change(self):
        hist = [snap(1, price=10.0, days_ago=5), snap(2, price=12.5, days_ago=0)]
        self.assertAlmostEqual(price_change_pct(hist), 25.0)

    def test_rank_change_negative_is_improvement(self):
        hist = [snap(1, rank=800, days_ago=5), snap(2, rank=300, days_ago=0)]
        self.assertEqual(rank_change(hist), -500)

    def test_score_bounds_and_ordering(self):
        weights = {"review_velocity": 0.4, "rating": 0.3,
                   "price_stability": 0.15, "rank_improvement": 0.15}
        cold = score_product([snap(10, rating=3.0, days_ago=1)], weights)
        hot = score_product(
            [snap(10, price=20, rating=4.9, rank=1000, days_ago=10),
             snap(310, price=20, rating=4.9, rank=500, days_ago=0)],
            weights,
        )
        for r in (cold, hot):
            self.assertTrue(0.0 <= r.score <= 100.0, r.score)
        self.assertGreater(hot.score, cold.score)

    def test_weights_normalized(self):
        # weights that don't sum to 1 still produce valid scores
        w = {"review_velocity": 4, "rating": 3, "price_stability": 1.5,
             "rank_improvement": 1.5}
        r = score_product([snap(50, rating=4.5, days_ago=1)], w)
        self.assertTrue(0.0 <= r.score <= 100.0)


if __name__ == "__main__":
    unittest.main()
