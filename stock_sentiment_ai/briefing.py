# stock_sentiment_ai/briefing.py
from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from typing import Dict, List, Tuple

from .topics import TOPICS
from .scanner import scan_topic, ScoredItem

ET = ZoneInfo("America/New_York")


def clear_screen() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def now_et() -> datetime:
    return datetime.now(tz=ET)


def fmt_dt_header(dt: datetime) -> str:
    # e.g. "mon jan 05 2026 01:31am ET"
    return dt.strftime("%a %b %d %Y %I:%M%p").lower().replace(" 0", " " ) + " ET"


def fmt_author_time_date(author: str, published_dt: datetime | None, published_raw: str) -> str:
    # Desired: "john smith 9:30am 11/22/25 ET"
    who = (author or "").strip() or "Unknown"

    if published_dt:
        dt_et = published_dt.astimezone(ET)
        # On macOS, %-I works; on Windows it may not. We’ll try both.
        try:
            time_str = dt_et.strftime("%-I:%M%p").lower()   # 9:30am
        except Exception:
            time_str = dt_et.strftime("%I:%M%p").lstrip("0").lower()
        date_str = dt_et.strftime("%m/%d/%y")               # 11/22/25
        return f"{who} {time_str} {date_str} ET"

    if published_raw:
        return f"{who} {published_raw}"

    return f"{who} Unknown time"


def approx_prev_market_close_et(dt: datetime) -> datetime:
    """
    Approximation: previous weekday 4:00pm ET.
    (Does not account for market holidays.)
    """
    dt = dt.astimezone(ET)
    d = dt.date()

    # If it's Monday, previous close is Friday.
    if dt.weekday() == 0:
        d = d - timedelta(days=3)
    # If it's Sunday, previous close is Friday.
    elif dt.weekday() == 6:
        d = d - timedelta(days=2)
    # If it's Saturday, previous close is Friday.
    elif dt.weekday() == 5:
        d = d - timedelta(days=1)
    else:
        d = d - timedelta(days=1)

    return datetime(d.year, d.month, d.day, 16, 0, 0, tzinfo=ET)


def mode_window(mode: str, dt_now: datetime) -> Tuple[datetime | None, datetime | None, str]:
    """
    Returns (start_dt, end_dt, window_label).
    If start_dt is None, we do not time-filter headlines.
    """
    if mode == "last24":
        start = dt_now - timedelta(hours=24)
        return start, dt_now, "window last 24h"

    if mode in ("preopen", "auto"):
        start = approx_prev_market_close_et(dt_now)
        return start, dt_now, f"window since {start.strftime('%-I:%M%p').lower()} {start.strftime('%m/%d/%y')} ET"

    # fallback: no window filter
    return None, None, "window all"


def should_keep_by_window(item: ScoredItem, start_dt: datetime | None, end_dt: datetime | None) -> bool:
    """
    Only filter if we actually have parsed datetimes.
    If a feed doesn't give a parsable datetime, we keep it
    (so you don't end up with 0 headlines).
    """
    if not start_dt or not end_dt:
        return True

    if item.published_dt is None:
        return True

    dt = item.published_dt.astimezone(ET)
    return start_dt <= dt <= end_dt


def print_topic_block(topic_key: str, items: List[ScoredItem], top_k: int) -> None:
    label = topic_key.upper()
    print(f"\n{label} — top {min(top_k, len(items))}\n")
    if not items:
        print("(none)\n")
        return

    for i, r in enumerate(items[:top_k], start=1):
        meta = fmt_author_time_date(r.author, r.published_dt, r.published_raw)
        print(f"{i}. [{r.label}] conf {r.confidence:.2f} {r.source} | {meta}")
        print(f"   {r.title}")
        print(f"   {r.link}")
        print()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", default="auto", choices=["auto", "preopen", "last24"])
    parser.add_argument("--clear", action="store_true")
    parser.add_argument("--topk", type=int, default=6)
    args = parser.parse_args()

    if args.clear:
        clear_screen()

    dt_now = now_et()
    start_dt, end_dt, window_label = mode_window(args.mode, dt_now)

    # Header
    print("=" * 88)
    print(f"PRE-MARKET BRIEFING — {fmt_dt_header(dt_now)} | mode={args.mode} | {window_label}")
    print("=" * 88)

    # Gather per-topic headlines
    all_items: List[ScoredItem] = []
    per_topic: Dict[str, List[ScoredItem]] = {}
    totals = {"Positive": 0, "Negative": 0, "Neutral": 0}
    topic_counts: Dict[str, int] = {}

    print("\nHEADLINES BY TOPIC")

    for topic_key in TOPICS.keys():
        items, counts = scan_topic(topic_key, top_k=max(args.topk, 10), use_snippet=True)

        # Window filter (but keep items with unknown datetime)
        items = [it for it in items if should_keep_by_window(it, start_dt, end_dt)]

        per_topic[topic_key] = items
        topic_counts[topic_key] = len(items)

        # Totals for sentiment
        for k, v in counts.items():
            if k in totals:
                totals[k] += v

        all_items.extend(items)

    # Print topics
    for topic_key in TOPICS.keys():
        print_topic_block(topic_key, per_topic[topic_key], args.topk)

    # Key metrics (bottom like your latest output)
    print("=" * 88)
    overall_n = len(all_items)
    print("KEY METRICS")
    print(f"- Overall: {overall_n} items | Sentiment totals: {totals['Positive']} pos / {totals['Negative']} neg / {totals['Neutral']} neutral")
    for topic_key in TOPICS.keys():
        print(f"- {topic_key.upper():6}: {topic_counts.get(topic_key, 0)} items")

    print("\nTOP HIGHLIGHTS (global)")
    if not all_items:
        print("(No headlines returned — your feeds may be blocked, or your time window is too tight.)")
    else:
        # "Highlights": highest confidence across all topics
        all_items.sort(key=lambda x: x.confidence, reverse=True)
        for i, r in enumerate(all_items[:min(8, len(all_items))], start=1):
            meta = fmt_author_time_date(r.author, r.published_dt, r.published_raw)
            print(f"{i}. [{r.label}] conf {r.confidence:.2f} {r.source} | {meta}")
            print(f"   {r.title}")
            print(f"   {r.link}")

    # Insiders / Politicians sections are assumed handled elsewhere in your project.
    # If your existing code prints them, keep that code in your project and call it here.

    print("\nPOLITICIANS (Stock Act) — disclosures")
    print("- No data pulled. To enable Quiver, set QUIVER_API_KEY in your environment.")
    print("  Example (macOS/zsh): export QUIVER_API_KEY='your_key_here'")
    print()


if __name__ == "__main__":
    main()

