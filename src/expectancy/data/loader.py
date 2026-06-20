"""Download and clean OHLCV from Yahoo Finance.

This is the *only* layer that touches the network. Everything downstream works
on the clean DataFrame this module returns, so the rest of the system never
depends on `yfinance`'s quirks.

Design choices that matter for a backtest:

* **Adjusted prices** (`auto_adjust=True`) so splits and dividends do not create
  fake gaps that the engine would read as real moves (survivorship/adjustment
  bias, brief §11).
* **Parquet cache** keyed by (ticker, start, end, interval): the first run hits
  the network, later runs are offline and reproducible.
* **Retry with backoff**: Yahoo scrapes unofficial endpoints and rate-limits, so
  a single failure should not abort a multi-instrument study.
"""

from __future__ import annotations

import time
from pathlib import Path

import pandas as pd

MIN_RECOMMENDED_CANDLES = 250
"""Below this many bars the sample is too thin to trust (a loud warning is logged)."""

_OHLCV_COLUMNS = ["Open", "High", "Low", "Close", "Volume"]
_CACHE_DIR = Path("data/cache")
_MAX_RETRIES = 3
_RETRY_BACKOFF_SECONDS = 2.0


class DataError(RuntimeError):
    """Raised when the data layer cannot produce a usable OHLCV frame."""


def _cache_path(ticker: str, start: str, end: str, interval: str) -> Path:
    safe_ticker = ticker.replace(".", "_").replace("^", "_")
    return _CACHE_DIR / f"{safe_ticker}_{start}_{end}_{interval}.parquet"


def _warn_if_missing_brazil_suffix(ticker: str) -> None:
    """Brazilian B3 tickers need the `.SA` suffix; warn on the common mistake."""
    looks_brazilian = ticker[:4].isalpha() and any(ch.isdigit() for ch in ticker)
    if looks_brazilian and "." not in ticker:
        print(
            f"[data] WARNING: '{ticker}' looks like a B3 ticker but has no '.SA' "
            f"suffix. Brazilian stocks must be requested as e.g. 'PETR4.SA'."
        )


def _flatten_columns(df: pd.DataFrame) -> pd.DataFrame:
    """yfinance may return a MultiIndex (field, ticker); keep only the field level."""
    if isinstance(df.columns, pd.MultiIndex):
        df = df.copy()
        df.columns = df.columns.get_level_values(0)
    return df


def _download(ticker: str, start: str, end: str, interval: str) -> pd.DataFrame:
    import yfinance as yf

    last_error: Exception | None = None
    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            df = yf.download(
                ticker,
                start=start,
                end=end,
                interval=interval,
                auto_adjust=True,
                progress=False,
                threads=False,
            )
            if df is not None and not df.empty:
                return _flatten_columns(df)
            last_error = DataError(f"empty frame for '{ticker}'")
        except Exception as exc:  # noqa: BLE001 - network layer, surface a clean error
            last_error = exc
        if attempt < _MAX_RETRIES:
            wait = _RETRY_BACKOFF_SECONDS * attempt
            print(f"[data] '{ticker}' download attempt {attempt} failed; retrying in {wait:.0f}s")
            time.sleep(wait)

    raise DataError(f"failed to download '{ticker}' after {_MAX_RETRIES} attempts: {last_error}")


def _clean(df: pd.DataFrame, ticker: str) -> pd.DataFrame:
    missing = [col for col in _OHLCV_COLUMNS if col not in df.columns]
    if missing:
        raise DataError(f"'{ticker}' is missing columns {missing}; got {list(df.columns)}")

    df = df[_OHLCV_COLUMNS].copy()
    df.index = pd.to_datetime(df.index)
    df = df[~df.index.duplicated(keep="first")]
    df = df.sort_index()
    df = df.dropna()
    df = df[(df[["Open", "High", "Low", "Close"]] > 0).all(axis=1)]
    return df


def load_ohlcv(
    ticker: str,
    start: str,
    end: str,
    interval: str = "1d",
    *,
    use_cache: bool = True,
) -> pd.DataFrame:
    """Return a clean OHLCV DataFrame for `ticker` between `start` and `end`.

    Columns: ``Open, High, Low, Close, Volume``. Index: unique, sorted dates.
    Raises :class:`DataError` on network failure or an unusable result.
    """
    _warn_if_missing_brazil_suffix(ticker)
    cache_file = _cache_path(ticker, start, end, interval)

    if use_cache and cache_file.exists():
        df = pd.read_parquet(cache_file)
    else:
        df = _download(ticker, start, end, interval)
        df = _clean(df, ticker)
        if use_cache:
            cache_file.parent.mkdir(parents=True, exist_ok=True)
            df.to_parquet(cache_file)

    df = _clean(df, ticker)

    if len(df) < MIN_RECOMMENDED_CANDLES:
        print(
            f"[data] WARNING: '{ticker}' returned only {len(df)} candles "
            f"(< {MIN_RECOMMENDED_CANDLES}). The sample may be too thin for a "
            f"trustworthy backtest."
        )
    return df
