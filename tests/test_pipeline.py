"""End-to-end pipeline smoke test with the demo source (no network)."""

import tempfile
import unittest
from pathlib import Path

from radar.config import Config, SourceConfig
from radar.pipeline import run


class TestPipeline(unittest.TestCase):
    def test_demo_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = Config(
                db_path="t.db",
                sources=[SourceConfig(name="demo", type="demo",
                                      keywords=["shampoo"], max_results=5)],
            )
            results, stats = run(cfg, workdir=Path(tmp))
            self.assertEqual(stats.snapshots, 5)
            self.assertEqual(stats.products_scored, 5)
            self.assertEqual(stats.source_errors, [])
            self.assertTrue(all(0 <= r.score <= 100 for r in results))
            # report file written
            reports = list((Path(tmp) / "reports").glob("report-*.md"))
            self.assertEqual(len(reports), 1)

    def test_deterministic_demo_source(self):
        cfg1 = Config(db_path="a.db", sources=[
            SourceConfig(name="demo", type="demo", keywords=["k"], max_results=3)])
        cfg2 = Config(db_path="b.db", sources=[
            SourceConfig(name="demo", type="demo", keywords=["k"], max_results=3)])
        with tempfile.TemporaryDirectory() as tmp:
            r1, _ = run(cfg1, workdir=Path(tmp))
            r2, _ = run(cfg2, workdir=Path(tmp))
            same_day = [(x.product_id, x.rating) for x in r1] == \
                       [(x.product_id, x.rating) for x in r2]
            self.assertTrue(same_day, "demo source should be deterministic per day")


if __name__ == "__main__":
    unittest.main()
