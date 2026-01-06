from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import requests

SEC_COMPANY_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
SEC_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik10}.json"

CACHE_DIR = Path(".cache")
CACHE_DIR.mkdir(exist_ok=True)
TICKER_CACHE = CACHE_DIR / "sec_company_tickers.json"


@dataclass(frozen=True)
class Form4Filing:
    filing_date: str
    url: str
    accession: str


def _sec_headers() -> Dict[str, str]:
    ua = os.getenv("SEC_USER_AGENT", "").strip()
    if not ua:
        # SEC will very often 403 without a real UA
        # Example: "DeclanNoonan (declannoonandd@gmail.com)"
        ua = "stock_sentiment_ai (set SEC_USER_AGENT env var)"
    return {
        "User-Agent": ua,
        "Accept-Encoding": "gzip, deflate",
        "Accept": "application/json,text/html,*/*",
        "Connection": "keep-alive",
    }


def _sec_get(url: str, timeout: int = 20) -> requests.Response:
    r = requests.get(url, headers=_sec_headers(), timeout=timeout)
    if r.status_code == 403:
        raise RuntimeError(
            "SEC returned 403. Set a real SEC_USER_AGENT first, e.g.\n"
            'export SEC_USER_AGENT="DeclanNoonan (declannoonandd@gmail.com)"\n'
            "Then run again."
        )
    r.raise_for_status()
    return r


def _load_company_tickers() -> Dict:
    # Use cached file to avoid hammering SEC and getting blocked
    if TICKER_CACHE.exists():
        try:
            return json.loads(TICKER_CACHE.read_text())
        except Exception:
            pass

    data = _sec_get(SEC_COMPANY_TICKERS_URL).json()
    try:
        TICKER_CACHE.write_text(json.dumps(data))
    except Exception:
        pass
    return data


def lookup_cik_for_ticker(ticker: str) -> Optional[str]:
    t = (ticker or "").strip().upper()
    if not t:
        return None

    data = _load_company_tickers()
    # company_tickers.json is an object keyed by integer-like strings
    for _, row in data.items():
        if str(row.get("ticker", "")).upper() == t:
            cik = int(row.get("cik_str", 0))
            return f"{cik:010d}"
    return None


def fetch_recent_form4_filings(cik10: str, limit: int = 10) -> List[Form4Filing]:
    # Be polite
    time.sleep(0.15)

    js = _sec_get(SEC_SUBMISSIONS_URL.format(cik10=cik10)).json()
    recent = (js.get("filings", {}) or {}).get("recent", {}) or {}

    forms = recent.get("form", []) or []
    dates = recent.get("filingDate", []) or []
    accessions = recent.get("accessionNumber", []) or []

    out: List[Form4Filing] = []
    for form, d, acc in zip(forms, dates, accessions):
        if form != "4":
            continue

        accession_nodash = acc.replace("-", "")
        cik_nolead = str(int(cik10))  # remove leading zeros for archive path

        url = f"https://www.sec.gov/Archives/edgar/data/{cik_nolead}/{accession_nodash}/{acc}-index.html"
        out.append(Form4Filing(filing_date=d, url=url, accession=acc))

        if len(out) >= limit:
            break

    return out


def fetch_insider_transactions_for_ticker(ticker: str, limit: int = 10) -> List[Dict[str, str]]:
    cik10 = lookup_cik_for_ticker(ticker)
    if not cik10:
        return []

    filings = fetch_recent_form4_filings(cik10, limit=limit)
    return [{"filing_date": f.filing_date, "url": f.url, "accession": f.accession} for f in filings]


