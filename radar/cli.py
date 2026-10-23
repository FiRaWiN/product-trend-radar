"""CLI: radar run / radar demo / radar report."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from . import __version__
from .config import Config, SourceConfig
from .pipeline import run


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="radar", description="Cross-border product trend monitoring."
    )
    parser.add_argument("--version", action="version", version=f"radar {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("run", help="Run one fetch-score cycle with a config file")
    p.add_argument("-c", "--config", default="config.toml")

    p = sub.add_parser("demo", help="Self-contained demo with synthetic data")
    p.add_argument("--keyword", default="shampoo")
    p.add_argument("-n", "--count", type=int, default=10)

    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    if args.command == "demo":
        cfg = Config(
            db_path="data/demo.db",
            sources=[
                SourceConfig(
                    name="demo",
                    type="demo",
                    keywords=[args.keyword],
                    max_results=args.count,
                )
            ],
        )
        run(cfg, workdir=Path.cwd())
        return 0

    if args.command == "run":
        from .config import load_config

        cfg = load_config(args.config)
        run(cfg, workdir=Path.cwd())
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
