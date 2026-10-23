"""Notifications: console and Feishu (Lark) webhook."""

from __future__ import annotations

import json
import urllib.request

from .models import TrendResult


def console(results: list[TrendResult]) -> None:
    if not results:
        print("No products tracked yet.")
        return
    print(f"{'score':>6}  {'rating':>6}  {'rev/day':>7}  {'Δprice%':>8}  title")
    for r in sorted(results, key=lambda x: -x.score):
        rating = f"{r.rating:.1f}" if r.rating is not None else "-"
        price = f"{r.price_change_pct:+.1f}" if r.price_change_pct is not None else "-"
        title = r.title[:60]
        print(f"{r.score:>6.1f}  {rating:>6}  {r.review_velocity:>7.2f}  {price:>8}  {title}")


def feishu(results: list[TrendResult], webhook: str, min_score: float) -> int:
    """Push hot products to a Feishu bot. Returns count of pushed items."""
    hot = [r for r in results if r.score >= min_score]
    if not hot:
        return 0
    lines = []
    for r in sorted(hot, key=lambda x: -x.score)[:10]:
        price = f", 价格变化 {r.price_change_pct:+.1f}%" if r.price_change_pct is not None else ""
        lines.append(
            f"**{r.title[:50]}** — 趋势分 {r.score}（评分 {r.rating or '-'}，"
            f"{r.review_velocity} 条/天{price}）"
        )
    payload = {
        "msg_type": "interactive",
        "card": {
            "header": {"title": {"tag": "plain_text", "content": "📈 选品雷达 · 热品提醒"}},
            "elements": [
                {"tag": "div", "text": {"tag": "lark_md", "content": "\n".join(lines)}}
            ],
        },
    }
    req = urllib.request.Request(
        webhook,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        resp.read()
    return len(hot)
