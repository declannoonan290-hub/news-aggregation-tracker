from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, List


# ==========================
# Sentiment model
# ==========================
# Use a FinBERT-like model that supports safetensors to avoid torch.load (.bin) security restriction.
MODEL_NAME = os.getenv("SENTIMENT_MODEL", "ProsusAI/finbert")
USE_SAFETENSORS = True

# If the HF model can't load (offline / blocked), we fall back to VADER automatically.


# ==========================
# News scanning
# ==========================
MAX_ITEMS_PER_FEED = 30
TOP_K_PER_TOPIC = 6
REQUEST_TIMEOUT_SECS = 12

# If True, we attempt to use RSS summaries/snippets.
# We do NOT scrape full article pages by default (safer + fewer ToS issues).
USE_SNIPPETS = True


# ==========================
# Logging
# ==========================
SAVE_DAILY_LOG = True
LOG_DIR = "logs"
KEEP_LOG_DAYS = 10  # keeps last N days of text logs


# ==========================
# SEC / Quiver keys
# ==========================
# SEC asks automated tools to provide a descriptive User-Agent (often including contact info).
# Set it in your terminal:
# export SEC_USER_AGENT="Declan Noonan declannoonandd@gmail.com"
SEC_USER_AGENT = os.getenv("SEC_USER_AGENT", "stock_sentiment_ai (set SEC_USER_AGENT env var)")

# Optional: QuiverQuant token for politician trades
# export QUIVER_API_KEY="..."
QUIVER_API_KEY = os.getenv("QUIVER_API_KEY", "")


# ==========================
# Trade watchlists (used for insiders + politician grouping by “industry/topic”)
# Put the tickers you care about here.
# ==========================
TRADE_WATCHLIST: Dict[str, List[str]] = {
    # Topic -> tickers to group by
    "gold": ["GLD", "GOLD", "NEM", "AU", "AEM"],
    "oil": ["XOM", "CVX", "COP", "OXY", "SLB"],
    "ai": ["NVDA", "MSFT", "GOOGL", "META", "AMD", "TSM", "AVGO"],
    "crypto": ["COIN", "MSTR", "RIOT", "MARA"],
    "world": ["SPY", "QQQ", "DXY", "TLT"],  # optional macro proxies
}


@dataclass(frozen=True)
class SentimentResult:
    label: str  # Positive / Negative / Neutral
    confidence: float
