from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.agents.market_data import MarketDataAgent
from app.agents.news import NewsAgent
from app.agents.sec import SECAgent

router = APIRouter(prefix="/ingest", tags=["ingest"])

_market_agent = MarketDataAgent()
_news_agent = NewsAgent()
_sec_agent = SECAgent()


@router.post("/market/{ticker}")
async def ingest_market_data(
    ticker: str,
    period: str = "1y",
    db: AsyncSession = Depends(get_db),
):
    """Fetch OHLCV data for a ticker and save to the database.

    period options: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
    """
    result = await _market_agent.fetch(ticker=ticker, period=period, db=db)
    if result["rows_saved"] == 0:
        raise HTTPException(status_code=404, detail=f"No price data found for {ticker}")
    return result


@router.get("/market/{ticker}/prices")
async def get_prices(
    ticker: str,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
):
    """Return the most recent price bars for a ticker."""
    rows = await _market_agent.get_latest(ticker=ticker, db=db, limit=limit)
    if not rows:
        raise HTTPException(
            status_code=404,
            detail=f"No prices in DB for {ticker} — run POST /ingest/market/{ticker} first",
        )
    return {"ticker": ticker.upper(), "prices": rows}


@router.post("/news/{ticker}")
async def ingest_news(ticker: str, db: AsyncSession = Depends(get_db)):
    """Fetch and store recent news headlines for a ticker (embeds into ChromaDB)."""
    result = await _news_agent.fetch(ticker=ticker, db=db)
    return result


@router.post("/sec/{ticker}")
async def ingest_sec(ticker: str, db: AsyncSession = Depends(get_db)):
    """Fetch and store recent 10-K and 10-Q filings from SEC EDGAR (embeds into ChromaDB)."""
    result = await _sec_agent.fetch(ticker=ticker, db=db)
    if result.get("filings_saved", 0) == 0 and "CIK not found" in result.get("message", ""):
        raise HTTPException(status_code=404, detail=result["message"])
    return result
