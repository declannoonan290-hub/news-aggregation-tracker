from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from .feeds import FeedItem, fetch_rss, google_news_rss_url
from .sentiment import predict_sentiment
from .topics import TOPICS
from .util import clean_text


@dataclass(frozen=True)
class ScoredItem:
    label: str
    confidence: float
    title: str
    link: str
    source: str
    author: str
    published_raw: str
    published_dt: Optional[datetime]
    used: str  # "TITLEONLY" or "TITLE+SNIPPET"


def scan_topic(
    topic_key: str,
    top_k: int = 6,
    use_snippet: bool = True,
    since_dt: Optional[datetime] = None,
    until_dt: Optional[datetime] = None,
) -> Tuple[List[ScoredItem], Dict[str, int]]:
    topic = TOPICS[topic_key]
    queries = topic.get("queries", [])
    extra_rss = topic.get("extra_rss", [])

    feed_urls: List[str] = []
    for q in queries:
        feed_urls.append(google_news_rss_url(q))
    feed_urls.extend(extra_rss)

    items: List[FeedItem] = []
    for url in feed_urls:
        try:
            items.extend(fetch_rss(url))
        except Exception:
            continue

    # Deduplicate hard (Google News overlaps a lot)
    seen = set()
    deduped: List[FeedItem] = []
    for it in items:
        key = (it.link or "").strip()
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(it)

    # Filter by time window BEFORE sentiment scoring
    filtered: List[FeedItem] = []
    for it in deduped:
        dt = it.published_dt
        if since_dt or until_dt:
            # If we're window-filtering and we don't have a parsed datetime,
            # skip it to keep the window “real”.
            if dt is None:
                continue
            if since_dt and dt < since_dt:
                continue
            if until_dt and dt > until_dt:
                continue
        filtered.append(it)

    scored: List[ScoredItem] = []
    counts = {"Positive": 0, "Negative": 0, "Neutral": 0}

    for it in filtered:
        used = "TITLEONLY"
        text = it.title

        if use_snippet and it.summary:
            used = "TITLE+SNIPPET"
            text = f"{it.title}. {it.summary}"

        s = predict_sentiment(text)
        counts[s.label] = counts.get(s.label, 0) + 1

        scored.append(
            ScoredItem(
                label=s.label,
                confidence=s.confidence,
                title=clean_text(it.title),
                link=clean_text(it.link),
                source=clean_text(it.source),
                author=clean_text(it.author),
                published_raw=clean_text(it.published_raw),
                published_dt=it.published_dt,
                used=used,
            )
        )

    scored.sort(key=lambda x: x.confidence, reverse=True)
    return scored[:top_k], counts
