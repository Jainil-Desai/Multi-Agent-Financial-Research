import asyncio
import logging

import yfinance as yf
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import PriceBar

log = logging.getLogger("finresearch.market_data")


def _download(ticker: str, period: str):
    t = yf.Ticker(ticker)
    df = t.history(period=period)
    return df


class MarketDataAgent:
    """Fetches OHLCV price history from Yahoo Finance and persists to SQLite."""

    async def fetch(self, ticker: str, period: str = "1y", db: AsyncSession = None) -> dict:
        ticker = ticker.upper()
        log.info(f"[MarketDataAgent] Fetching {ticker} ({period})")

        raw = await asyncio.to_thread(_download, ticker, period)
        log.info(f"[MarketDataAgent] shape={raw.shape}, columns={list(raw.columns)}")

        if raw.empty:
            log.warning(f"[MarketDataAgent] No data for {ticker}")
            return {"ticker": ticker, "rows_saved": 0, "message": "No data from yfinance"}

        await db.execute(delete(PriceBar).where(PriceBar.ticker == ticker))

        bars = []
        for ts, row in raw.iterrows():
            bars.append(PriceBar(
                ticker=ticker,
                date=ts.to_pydatetime().replace(tzinfo=None),
                open=float(row["Open"]),
                high=float(row["High"]),
                low=float(row["Low"]),
                close=float(row["Close"]),
                volume=float(row["Volume"]),
            ))

        db.add_all(bars)
        await db.commit()

        log.info(f"[MarketDataAgent] Saved {len(bars)} bars for {ticker}")
        return {
            "ticker": ticker,
            "period": period,
            "rows_saved": len(bars),
            "from": bars[0].date.date().isoformat(),
            "to": bars[-1].date.date().isoformat(),
        }

    async def get_latest(self, ticker: str, db: AsyncSession, limit: int = 10) -> list[dict]:
        result = await db.execute(
            select(PriceBar)
            .where(PriceBar.ticker == ticker.upper())
            .order_by(PriceBar.date.desc())
            .limit(limit)
        )
        rows = result.scalars().all()
        return [
            {"date": r.date.date().isoformat(), "open": r.open, "high": r.high,
             "low": r.low, "close": r.close, "volume": r.volume}
            for r in rows
        ]
