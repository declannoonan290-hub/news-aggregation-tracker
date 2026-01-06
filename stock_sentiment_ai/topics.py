# stock_sentiment_ai/topics.py
from __future__ import annotations

# Each topic can include:
# - queries: list[str] used for Google News RSS searches
# - extra_rss: list[str] for any additional RSS feeds you want to include
# - tickers: list[str] used for SEC Form 4 lookups (must be real stock/ETF tickers)

TOPICS = {
    "gold": {
        "queries": [
            "gold price",
            "gold miners",
            "GLD ETF",
            "XAUUSD",
            "Federal Reserve rates gold",
        ],
        "extra_rss": [],
        "tickers": [
            "GOLD",  # Barrick
            "NEM",   # Newmont
            "AEM",   # Agnico Eagle
            "WPM",   # Wheaton Precious Metals
            "FNV",   # Franco-Nevada
            "GLD",   # SPDR Gold Shares (ETF)
            "IAU",   # iShares Gold Trust (ETF)
        ],
    },

    "oil": {
        "queries": [
            "crude oil price",
            "WTI oil",
            "Brent oil",
            "OPEC",
            "US crude inventories EIA",
            "oil futures",
        ],
        "extra_rss": [],
        "tickers": [
            "XOM",  # Exxon
            "CVX",  # Chevron
            "COP",  # ConocoPhillips
            "OXY",  # Occidental
            "EOG",  # EOG Resources
            "SLB",  # Schlumberger
            "XLE",  # Energy Select Sector SPDR (ETF)
            "USO",  # United States Oil Fund (ETF)
        ],
    },

    "ai": {
        "queries": [
            "AI stocks",
            "Nvidia AI chips",
            "semiconductors AI demand",
            "OpenAI Microsoft AI",
            "Google AI",
            "datacenter GPUs",
        ],
        "extra_rss": [],
        "tickers": [
            "NVDA",
            "MSFT",
            "GOOGL",
            "AMZN",
            "META",
            "TSLA",
            "AMD",
            "AVGO",
            "ASML",
            "SMCI",
            "TSM",
            "AAPL",
            "AIQ",   # Global X Artificial Intelligence & Technology ETF
            "BOTZ",  # Global X Robotics & Artificial Intelligence ETF
            "SOXX",  # iShares Semiconductor ETF
        ],
    },

    "crypto": {
        "queries": [
            "bitcoin price",
            "ethereum price",
            "crypto market",
            "bitcoin ETF flows",
            "SEC crypto",
            "coinbase",
        ],
        "extra_rss": [],
        "tickers": [
            "COIN",  # Coinbase
            "MSTR",  # MicroStrategy/Strategy
            "RIOT",  # Riot Platforms
            "MARA",  # Marathon Digital
            "HUT",   # Hut 8
            "BITO",  # ProShares Bitcoin Strategy ETF
            "IBIT",  # iShares Bitcoin Trust (if your broker supports; SEC lookup may or may not return useful filings)
            "GBTC",  # Grayscale Bitcoin Trust
        ],
    },

    "world": {
        "queries": [
            "global markets",
            "inflation data",
            "central bank rates",
            "geopolitics market impact",
            "trade tariffs",
            "China economy markets",
            "Europe economy markets",
        ],
        "extra_rss": [],
        "tickers": [
            "SPY",  # S&P 500 ETF
            "QQQ",  # Nasdaq 100 ETF
            "DIA",  # Dow ETF
            "IWM",  # Russell 2000 ETF
            "TLT",  # 20+ Year Treasury ETF
            "UUP",  # US Dollar ETF
            "EEM",  # Emerging Markets ETF
            "FXI",  # China large-cap ETF
            "EWJ",  # Japan ETF
            "EWG",  # Germany ETF
        ],
    },
}
