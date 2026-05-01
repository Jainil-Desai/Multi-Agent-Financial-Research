import logging
from sqlalchemy import select

from app.database.connection import AsyncSessionLocal
from app.database.models import PriceBar, NewsArticle, SecFiling
from app.agents.market_data import MarketDataAgent
from app.agents.news import NewsAgent
from app.agents.sec import SECAgent
from app.agents.summarizer import SummarizationAgent
from app.agents.risk import RiskAgent
from app.agents.forecast import ForecastAgent
from app.agents.report import ReportAgent
from app.graph.state import ResearchState

log = logging.getLogger("finresearch.graph")


async def fetch_market_node(state: ResearchState) -> dict:
    ticker = state["ticker"]
    period = state.get("period", "1y")
    try:
        async with AsyncSessionLocal() as db:
            result = await MarketDataAgent().fetch(ticker=ticker, period=period, db=db)
            rows = await db.execute(
                select(PriceBar).where(PriceBar.ticker == ticker).order_by(PriceBar.date.desc())
            )
            bars = [
                {"date": r.date.date().isoformat(), "open": r.open, "high": r.high,
                 "low": r.low, "close": r.close, "volume": r.volume}
                for r in rows.scalars().all()
            ]
        return {"price_bars": bars, "logs": [f"Fetched {len(bars)} price bars for {ticker}"]}
    except Exception as e:
        log.error(f"[fetch_market_node] {e}")
        return {"price_bars": [], "logs": [f"Market data fetch failed: {e}"]}


async def fetch_news_node(state: ResearchState) -> dict:
    ticker = state["ticker"]
    try:
        async with AsyncSessionLocal() as db:
            result = await NewsAgent().fetch(ticker=ticker, db=db)
            rows = await db.execute(
                select(NewsArticle).where(NewsArticle.ticker == ticker).order_by(NewsArticle.published_at.desc())
            )
            articles = [
                {"title": r.title, "source": r.source, "url": r.url,
                 "published_at": r.published_at.isoformat(), "content": r.content}
                for r in rows.scalars().all()
            ]
        return {"news_articles": articles, "logs": [f"Fetched {len(articles)} news articles for {ticker}"]}
    except Exception as e:
        log.error(f"[fetch_news_node] {e}")
        return {"news_articles": [], "logs": [f"News fetch failed: {e}"]}


async def fetch_sec_node(state: ResearchState) -> dict:
    ticker = state["ticker"]
    try:
        async with AsyncSessionLocal() as db:
            await SECAgent().fetch(ticker=ticker, db=db)
            rows = await db.execute(
                select(SecFiling).where(SecFiling.ticker == ticker).order_by(SecFiling.filed_at.desc())
            )
            filings = [
                {"form_type": r.form_type, "filed_at": r.filed_at.isoformat(),
                 "accession_number": r.accession_number, "document_url": r.document_url,
                 "raw_text": r.raw_text}
                for r in rows.scalars().all()
            ]
        return {"sec_filings": filings, "logs": [f"Fetched {len(filings)} SEC filings for {ticker}"]}
    except Exception as e:
        log.error(f"[fetch_sec_node] {e}")
        return {"sec_filings": [], "logs": [f"SEC fetch failed: {e}"]}


async def summarize_node(state: ResearchState) -> dict:
    ticker = state["ticker"]
    try:
        summary = await SummarizationAgent().summarize(ticker=ticker, filings=state.get("sec_filings", []))
        return {"filing_summary": summary, "logs": ["Filing summarization complete"]}
    except Exception as e:
        log.error(f"[summarize_node] {e}")
        return {"filing_summary": "Summarization failed.", "logs": [f"Summarization failed: {e}"]}


async def risk_node(state: ResearchState) -> dict:
    ticker = state["ticker"]
    try:
        signals = await RiskAgent().detect(
            ticker=ticker,
            news=state.get("news_articles", []),
            filings=state.get("sec_filings", []),
        )
        return {"risk_signals": signals, "logs": [f"Identified {len(signals)} risk signals"]}
    except Exception as e:
        log.error(f"[risk_node] {e}")
        return {"risk_signals": [], "logs": [f"Risk detection failed: {e}"]}


async def forecast_node(state: ResearchState) -> dict:
    ticker = state["ticker"]
    try:
        fc = await ForecastAgent().forecast(ticker=ticker, price_bars=state.get("price_bars", []))
        return {"forecast": fc, "logs": [f"Forecast complete: {fc.get('trend')} ({fc.get('predicted_pct_change', '?')}%)"]}
    except Exception as e:
        log.error(f"[forecast_node] {e}")
        return {"forecast": {"error": str(e), "trend": "unknown"}, "logs": [f"Forecast failed: {e}"]}


async def report_node(state: ResearchState) -> dict:
    ticker = state["ticker"]
    try:
        async with AsyncSessionLocal() as db:
            report = await ReportAgent().generate(
                ticker=ticker,
                price_bars=state.get("price_bars", []),
                news=state.get("news_articles", []),
                filing_summary=state.get("filing_summary", ""),
                risk_signals=state.get("risk_signals", []),
                forecast=state.get("forecast", {}),
                db=db,
            )
        return {"report": report["full_report"], "logs": ["Analyst report generated"]}
    except Exception as e:
        log.error(f"[report_node] {e}")
        return {"report": f"Report generation failed: {e}", "logs": [f"Report failed: {e}"]}
