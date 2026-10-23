"""Configuration loading (TOML, stdlib tomllib)."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class SourceConfig:
    name: str
    type: str = "demo"
    keywords: list[str] = field(default_factory=list)
    max_results: int = 10


@dataclass
class NotifyConfig:
    console: bool = True
    feishu_webhook: str | None = None   # https://open.feishu.cn/open-apis/bot/v2/hook/xxx
    feishu_min_score: float = 75.0      # only push products above this score


@dataclass
class Config:
    db_path: str = "data/radar.db"
    sources: list[SourceConfig] = field(default_factory=list)
    notify: NotifyConfig = field(default_factory=NotifyConfig)
    weights: dict[str, float] = field(
        default_factory=lambda: {
            "review_velocity": 0.4,
            "rating": 0.3,
            "price_stability": 0.15,
            "rank_improvement": 0.15,
        }
    )


def load_config(path: str | Path) -> Config:
    raw = tomllib.loads(Path(path).read_text(encoding="utf-8"))
    cfg = Config(
        db_path=raw.get("db_path", Config.db_path),
        weights=raw.get("weights", Config().weights),
    )
    notify = raw.get("notify", {})
    cfg.notify = NotifyConfig(
        console=notify.get("console", True),
        feishu_webhook=notify.get("feishu_webhook"),
        feishu_min_score=notify.get("feishu_min_score", 75.0),
    )
    for s in raw.get("sources", []):
        cfg.sources.append(
            SourceConfig(
                name=s["name"],
                type=s.get("type", "demo"),
                keywords=s.get("keywords", []),
                max_results=s.get("max_results", 10),
            )
        )
    return cfg
