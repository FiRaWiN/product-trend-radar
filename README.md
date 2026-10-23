# product-trend-radar 📈

[![tests](https://github.com/FiRaWiN/product-trend-radar/actions/workflows/tests.yml/badge.svg)](https://github.com/FiRaWiN/product-trend-radar/actions/workflows/tests.yml)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

**Cross-border e-commerce product trend monitoring** — pluggable data sources,
trend scoring, SQLite history, Markdown reports, and instant Feishu (Lark)
alerts when a product heats up.

*跨境电商选品趋势监控：可插拔数据源 → 趋势评分 → 历史入库 → Markdown 报告 → 飞书热品推送。*

[中文说明](#中文说明) below.

## Why

Cross-border sellers drown in product research: which items in a category are
gaining momentum *right now*? Checking manually doesn't scale, and most SaaS
tools are expensive and black-box. This project is a small, honest, hackable
alternative: every signal is inspectable, every weight is configurable.

## How it works

```
 ┌──────────┐   snapshots   ┌─────────┐   history   ┌───────────┐
 │  Sources │ ────────────▶ │ Storage │ ──────────▶ │  Scoring  │
 │ demo/amz │               │ (SQLite)│             │ 0-100 分  │
 └──────────┘               └─────────┘             └─────┬─────┘
                                                          │
                                    ┌─────────────────────┼──────────┐
                                    ▼                     ▼          ▼
                              Markdown report       Console table  Feishu 🔔
```

**Trend score (0–100)** blends four configurable signals:

| Signal | Weight (default) | Meaning |
|---|---|---|
| `review_velocity` | 40% | new reviews/day — buyers who rarely review are the honest demand signal |
| `rating` | 30% | absolute star rating |
| `price_stability` | 15% | stable price = healthy listing, not a clearance fire-sale |
| `rank_improvement` | 15% | category rank trending up |

## Quick start

```bash
# zero-dependency demo run (synthetic data, no network needed)
python -m radar demo --keyword shampoo

# with a real config
cp config.example.toml config.toml   # edit sources/keywords/feishu webhook
python -m radar run -c config.toml

# optional: real Amazon search-page scraping
pip install -r requirements.txt
```

Each run persists snapshots to SQLite and writes a Markdown report to
`reports/`. Schedule it with cron / launchd and the trend score gets smarter
as history accumulates:

```cron
# every 6 hours
0 */6 * * * cd /path/to/product-trend-radar && /usr/bin/python3 -m radar run -c config.toml >> radar.log 2>&1
```

## Architecture

```
radar/
├── sources/        # pluggable data sources
│   ├── base.py     #   Source ABC + SourceError
│   ├── demo.py     #   deterministic synthetic data (CI-friendly)
│   └── amazon.py   #   best-effort search-page scraper (optional deps)
├── storage.py      # SQLite via stdlib sqlite3
├── scoring.py      # 0-100 trend score from snapshot history
├── report.py       # Markdown report generator
├── notify.py       # console table + Feishu webhook card
├── pipeline.py     # fetch -> save -> score -> notify
└── cli.py          # radar run / radar demo
```

Adding a source = implement one method:

```python
class MySource(Source):
    name = "temu"
    def fetch(self, keyword: str, max_results: int = 10) -> list[ProductSnapshot]:
        ...
```

## Honest limitations

- The Amazon scraper is **best-effort**: Amazon bot-detects aggressively, page
  markup changes break selectors, and this is meant for low-frequency personal
  research only — not bulk crawling. For production use the official Product
  Advertising API or a licensed data provider.
- `rank` (best-seller rank) is only available from sources that expose it; the
  demo source fakes it so scoring can be exercised end-to-end.
- The trend score is a heuristic, not a crystal ball. Weights are yours to tune.

## Test

```bash
python -m unittest discover -s tests -v
```

## Roadmap

- [ ] AliExpress / Temu sources
- [ ] Review-text keyword mining (with [ugnlp](https://github.com/FiRaWiN/ugnlp))
- [ ] Per-keyword score normalization
- [ ] GitHub Action for scheduled runs

## License

MIT — see [LICENSE](LICENSE).

---

# 中文说明

跨境电商选品痛点：怎么知道一个类目里**哪些商品正在起量**？手动刷屏不现实，
SaaS 工具又贵又黑盒。本项目是一个小而透明、可随意改造的替代方案：
每个信号都看得见，每个权重都能改。

- **数据源可插拔**：内置 demo（合成数据，零依赖可跑）和 Amazon 抓取器（可选依赖），
  实现一个 `fetch()` 方法即可接入新平台
- **趋势评分 0-100**：评论增速 40% + 星级 30% + 价格稳定 15% + 排名改善 15%，
  权重可在 `config.toml` 里调
- **SQLite 历史**：每次运行落库，历史越攒评分越准
- **输出**：控制台表格 + Markdown 报告 + 飞书机器人热品推送（`feishu_webhook` 填进配置即可）

运行示例：

```bash
python -m radar demo --keyword shampoo   # 合成数据，立刻能跑
cp config.example.toml config.toml       # 配置关键词/飞书 webhook
python -m radar run -c config.toml       # 正式运行一轮
```

用 cron 每 6 小时跑一次，报告落在 `reports/`，热品自动推飞书。

诚实声明：Amazon 抓取器是 best-effort（反爬严格、页面结构会变），仅适合
低频个人研究；生产环境请用官方 PA-API 或持牌数据服务商。评分是启发式，
不是预言机。
