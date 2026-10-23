"""Markdown report generation."""

from __future__ import annotations

import time
from pathlib import Path

from .models import TrendResult


def generate_md(results: list[TrendResult], path: str | Path, top_n: int = 20) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    now = time.strftime("%Y-%m-%d %H:%M", time.localtime())
    lines = [
        f"# 选品雷达报告 · {now}",
        "",
        f"跟踪产品数：{len(results)}，按趋势分排序（Top {min(top_n, len(results))}）。",
        "",
        "| # | 产品 | 趋势分 | 评分 | 评论增速(条/天) | 价格变化 | 排名变化 | 快照数 |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for i, r in enumerate(sorted(results, key=lambda x: -x.score)[:top_n], 1):
        rating = f"{r.rating:.1f}" if r.rating is not None else "-"
        price = f"{r.price_change_pct:+.1f}%" if r.price_change_pct is not None else "-"
        rank = f"{r.rank_change:+d}" if r.rank_change is not None else "-"
        lines.append(
            f"| {i} | {r.title[:50]} | **{r.score}** | {rating} | "
            f"{r.review_velocity} | {price} | {rank} | {r.snapshot_count} |"
        )
    lines += [
        "",
        "---",
        "*由 product-trend-radar 自动生成。评分 = 评论增速 40% + 评分 30% + 价格稳定 15% + 排名改善 15%（可在 config.toml 调整）。*",
    ]
    p.write_text("\n".join(lines), encoding="utf-8")
    return p
