from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import List, Optional
from urllib.parse import quote_plus

import feedparser


@dataclass
class FeedItem:
    title: str
    link: str
    source: str
    summary: str
    author: str
    published_raw: str
    published_dt: Optional[datetime]


def google_news_rss_url(query: str) -> str:
    q = quote_plus(query)
    return f"https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en"


def _best_effort_source(entry) -> str:
    # Google News often provides entry.source.title
    try:
        src = entry.get("source")
        if isinstance(src, dict) and src.get("title"):
            return str(src.get("title", "")).strip()
        # Sometimes feedparser returns a FeedParserDict with .title
        if hasattr(src, "title") and src.title:
            return str(src.title).strip()
    except Exception:
        pass

    # Fallback: many Google News titles end with " - Publisher"
    title = str(entry.get("title", "")).strip()
    if " - " in title:
        maybe = title.rsplit(" - ", 1)[-1].strip()
        # Avoid silly long “publisher” strings
        if 1 <= len(maybe) <= 60:
            return maybe

    return "Unknown"


def _best_effort_author(entry) -> str:
    # Many RSS feeds do NOT include author. Best effort only.
    a = str(entry.get("author", "") or "").strip()
    if a:
        return a

    authors = entry.get("authors")
    if isinstance(authors, list) and authors:
        first = authors[0]
        if isinstance(first, dict) and first.get("name"):
            return str(first.get("name", "")).strip()

    return ""


def _best_effort_published(entry) -> tuple[str, Optional[datetime]]:
    raw = str(entry.get("published", "") or entry.get("updated", "") or "").strip()
    if not raw:
        return "", None

    # RFC822 dates usually parse cleanly here
    try:
        dt = parsedate_to_datetime(raw)
        if dt is not None:
            return raw, dt
    except Exception:
        pass

    return raw, None


def fetch_rss(url: str) -> List[FeedItem]:
    feed = feedparser.parse(url)

    out: List[FeedItem] = []
    for e in feed.entries:
        title = str(e.get("title", "")).strip()
        link = str(e.get("link", "")).strip()
        summary = str(e.get("summary", "") or "").strip()

        source = _best_effort_source(e)
        author = _best_effort_author(e)
        published_raw, published_dt = _best_effort_published(e)

        if not title or not link:
            continue

        out.append(
            FeedItem(
                title=title,
                link=link,
                source=source,
                summary=summary,
                author=author,
                published_raw=published_raw,
                published_dt=published_dt,
            )
        )

    return out
