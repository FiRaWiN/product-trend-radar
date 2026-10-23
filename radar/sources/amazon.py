"""Amazon best-effort scraper (optional: needs requests + beautifulsoup4).

Honest caveats, also stated in the README:
- Amazon actively bot-detects; this fetches the public search page with a
  browser-like User-Agent and may still be blocked (HTTP 503 / captcha).
- Designed for low-frequency personal research (a few runs per day),
  NOT for bulk crawling. Respect robots.txt and local law.
- Markup changes break selectors; they are kept simple and centralised.

For production monitoring use the official Amazon Product Advertising API
(PAAP) or a licensed data provider — swap it in by implementing Source.
"""

from __future__ import annotations

import re

from ..models import ProductSnapshot
from .base import Source, SourceError

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError as e:  # pragma: no cover
    raise ImportError(
        "Amazon source needs: pip install requests beautifulsoup4"
    ) from e

_SEARCH_URL = "https://www.amazon.com/s"
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}
_PRICE_RE = re.compile(r"[$€£]\s?(\d+(?:[.,]\d+)?)")


class AmazonSource(Source):
    name = "amazon"

    def fetch(self, keyword: str, max_results: int = 10) -> list[ProductSnapshot]:
        try:
            resp = requests.get(
                _SEARCH_URL,
                params={"k": keyword},
                headers=_HEADERS,
                timeout=15,
            )
        except requests.RequestException as e:
            raise SourceError(f"network error: {e}") from e
        if resp.status_code != 200:
            raise SourceError(f"HTTP {resp.status_code} (likely bot-blocked)")
        soup = BeautifulSoup(resp.text, "html.parser")
        items = soup.select("div[data-asin]")[: max_results]
        out: list[ProductSnapshot] = []
        seen: set[str] = set()
        for item in items:
            asin = item.get("data-asin")
            if not asin or asin in seen:
                continue
            seen.add(asin)
            title_el = item.select_one("h2 span")
            rating_el = item.select_one("span.a-icon-alt")
            reviews_el = item.select_one(
                'span[aria-label$="ratings"], span[aria-label$="rating"]'
            )
            price_el = item.select_one("span.a-offscreen")
            out.append(
                ProductSnapshot(
                    source=self.name,
                    product_id=asin,
                    keyword=keyword,
                    title=title_el.get_text(strip=True) if title_el else "(untitled)",
                    price=_parse_price(price_el.get_text(strip=True)) if price_el else None,
                    rating=_parse_rating(rating_el.get_text(strip=True)) if rating_el else None,
                    reviews=_parse_reviews(reviews_el.get_text(strip=True)) if reviews_el else None,
                )
            )
        if not out:
            raise SourceError("parsed 0 items — page layout may have changed")
        return out

    @staticmethod
    def _parse_price(text: str) -> float | None:
        m = _PRICE_RE.search(text)
        return float(m.group(1).replace(",", "")) if m else None

    @staticmethod
    def _parse_rating(text: str) -> float | None:
        m = re.search(r"(\d\.\d)", text)
        return float(m.group(1)) if m else None

    @staticmethod
    def _parse_reviews(text: str) -> int | None:
        digits = re.sub(r"[^\d]", "", text)
        return int(digits) if digits else None
