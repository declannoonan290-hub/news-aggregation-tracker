from __future__ import annotations

import os
import re
import time
from datetime import datetime, timezone
from typing import Iterable, List, Optional, Tuple


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def today_ymd_local() -> str:
    # "local" date; good enough for daily logs
    return datetime.now().strftime("%Y-%m-%d")


def clean_text(s: str) -> str:
    s = re.sub(r"\s+", " ", s or "").strip()
    return s


def dedupe_keep_order(items: Iterable[str]) -> List[str]:
    seen = set()
    out: List[str] = []
    for x in items:
        if x not in seen:
            out.append(x)
            seen.add(x)
    return out


class SimpleRateLimiter:
    def __init__(self, min_interval_sec: float = 0.25) -> None:
        self.min_interval_sec = min_interval_sec
        self._last = 0.0

    def wait(self) -> None:
        now = time.time()
        dt = now - self._last
        if dt < self.min_interval_sec:
            time.sleep(self.min_interval_sec - dt)
        self._last = time.time()


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)
