"""Pipeline orchestration: fetch -> save -> score -> notify/report."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from pathlib import Path

from .config import Config, SourceConfig
from .notify import console as notify_console
from .notify import feishu
from .report import generate_md
from .scoring import score_product
from .sources.base import Source, SourceError
from .sources.demo import DemoSource
from .storage import Storage

logger = logging.getLogger("radar")


def build_source(cfg: SourceConfig) -> Source:
    if cfg.type == "demo":
        return DemoSource(source_name=cfg.name)
    if cfg.type == "amazon":
        try:
            from .sources.amazon import AmazonSource
        except ImportError as e:
            raise SourceError(str(e)) from e
        return AmazonSource()
    raise SourceError(f"unknown source type: {cfg.type!r}")


@dataclass
class RunStats:
    snapshots: int = 0
    products_scored: int = 0
    source_errors: list[str] = None

    def __post_init__(self):
        if self.source_errors is None:
            self.source_errors = []


def run(cfg: Config, workdir: Path | None = None) -> tuple[list, RunStats]:
    """One fetch-score cycle. Returns (trend results, run stats)."""
    workdir = Path(workdir or ".")
    db = Storage(workdir / cfg.db_path)
    stats = RunStats()

    # 1. fetch + persist
    for src_cfg in cfg.sources:
        try:
            src = build_source(src_cfg)
            for kw in src_cfg.keywords:
                snaps = src.fetch(kw, src_cfg.max_results)
                db.save(snaps)
                stats.snapshots += len(snaps)
        except SourceError as e:
            logger.warning("source %s failed: %s", src_cfg.name, e)
            stats.source_errors.append(f"{src_cfg.name}: {e}")

    # 2. score everything we have history for
    results = []
    for source, product_id, _title in db.known_products():
        history = db.history(source, product_id)
        results.append(score_product(history, cfg.weights))
    stats.products_scored = len(results)

    # 3. notify + report
    if cfg.notify.console:
        notify_console(results)
    if cfg.notify.feishu_webhook:
        try:
            pushed = feishu(results, cfg.notify.feishu_webhook, cfg.notify.feishu_min_score)
            logger.info("feishu: pushed %d products", pushed)
        except OSError as e:
            logger.warning("feishu push failed: %s", e)
    if results:
        report_path = workdir / "reports" / f"report-{time.strftime('%Y%m%d-%H%M')}.md"
        generate_md(results, report_path)
        print(f"\n📄 report saved: {report_path}")

    db.close()
    return results, stats
