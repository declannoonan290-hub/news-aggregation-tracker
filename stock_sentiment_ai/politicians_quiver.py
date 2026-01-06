from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

import pandas as pd

from .config import QUIVER_API_KEY


@dataclass(frozen=True)
class PolTrade:
    ticker: str
    politician: str
    transaction: str  # e.g. "Purchase", "Sale"
    date: str
    amount: str


def fetch_recent_congress_trades(
    tickers: Optional[List[str]] = None,
    limit: int = 50,
) -> List[PolTrade]:
    """
    Uses QuiverQuant python API. Needs QUIVER_API_KEY env var.
    If no key, returns empty list.

    Quiver method is `congress_trading()` per their package README.
    """
    if not QUIVER_API_KEY:
        return []

    try:
        import quiverquant
    except Exception:
        return []

    q = quiverquant.quiver(QUIVER_API_KEY)

    try:
        if tickers and len(tickers) == 1:
            df = q.congress_trading(tickers[0])
        else:
            df = q.congress_trading()
    except Exception:
        return []

    if df is None or len(df) == 0:
        return []

    # Normalize columns defensively (Quiver sometimes changes naming)
    cols = {c.lower(): c for c in df.columns}
    def pick(*names: str) -> Optional[str]:
        for n in names:
            if n.lower() in cols:
                return cols[n.lower()]
        return None

    c_ticker = pick("ticker", "symbol")
    c_pol = pick("representative", "politician", "name")
    c_tx = pick("transaction", "type")
    c_date = pick("transactiondate", "date")
    c_amt = pick("amount", "range")

    out: List[PolTrade] = []
    for _, row in df.head(limit).iterrows():
        ticker = str(row.get(c_ticker, "")).upper() if c_ticker else ""
        if tickers and ticker and ticker not in set([t.upper() for t in tickers]):
            continue

        out.append(
            PolTrade(
                ticker=ticker or "UNKNOWN",
                politician=str(row.get(c_pol, "Unknown")) if c_pol else "Unknown",
                transaction=str(row.get(c_tx, "Unknown")) if c_tx else "Unknown",
                date=str(row.get(c_date, "")) if c_date else "",
                amount=str(row.get(c_amt, "")) if c_amt else "",
            )
        )

    return out
