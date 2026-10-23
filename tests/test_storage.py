import tempfile
import unittest
from pathlib import Path

from radar.models import ProductSnapshot
from radar.storage import Storage


def snap(pid, reviews, ts):
    return ProductSnapshot(
        source="demo", product_id=pid, keyword="k", title=f"T-{pid}",
        price=9.9, rating=4.2, reviews=reviews, ts=ts,
    )


class TestStorage(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Storage(Path(self.tmp.name) / "test.db")

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def test_roundtrip(self):
        n = self.db.save([snap("A", 10, 1.0), snap("A", 20, 2.0), snap("B", 5, 1.0)])
        self.assertEqual(n, 3)
        hist = self.db.history("demo", "A")
        self.assertEqual(len(hist), 2)
        self.assertEqual(hist[0].reviews, 10)   # oldest first
        self.assertEqual(hist[1].reviews, 20)

    def test_known_products_latest_title(self):
        self.db.save([snap("A", 10, 1.0)])
        self.db.save([snap("A", 10, 2.0)])
        known = self.db.known_products()
        self.assertEqual(len(known), 1)
        self.assertEqual(known[0][0], "demo")
        self.assertEqual(known[0][1], "A")


if __name__ == "__main__":
    unittest.main()
