import asyncio
import hashlib
import logging
from datetime import datetime

import yfinance as yf
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import NewsArticle
from app.rag.retriever import store_news

log = logging.getLogger("finresearch.news")


def _fetch_yf_news(ticker: str) -> list[dict]:
    t = yf.Ticker(ticker)
    news = t.news or []
    log.debug(f"[NewsAgent] raw news sample: {news[:1]}")
    return news


def _parse_item(item: dict) -> dict | None:
    """Normalise a yfinance news item regardless of API version."""
    # yfinance 0.2.x wraps content under a 'content' key
    content = item.get("content")
    if isinstance(content, dict):
        title = content.get("title", "")
        url = (content.get("canonicalUrl") or {}).get("url", "")
        source = (content.get("provider") or {}).get("displayName", "")
        pub_str = content.get("pubDate", "")
        try:
            published_at = datetime.fromisoformat(pub_str.replace("Z", "+00:00")) if pub_str else datetime.utcnow()
        except ValueError:
            published_at = datetime.utcnow()
        summary = content.get("summary", "")
    else:
        # Older flat format
        title = item.get("title", "")
        url = item.get("link", "")
        source = item.get("publisher", "")
        ts = item.get("providerPublishTime", 0)
        published_at = datetime.fromtimestamp(ts) if ts else datetime.utcnow()
        summary = ""

    if not title:
        return None
    return {"title": title, "url": url, "source": source, "published_at": published_at, "summary": summary}


class NewsAgent:
    """Fetches news headlines via yfinance and stores in SQLite + ChromaDB."""

    async def fetch(self, ticker: str, db: AsyncSession) -> dict:
        ticker = ticker.upper()
        log.info(f"[NewsAgent] Fetching news for {ticker}")

        raw_news = await asyncio.to_thread(_fetch_yf_news, ticker)
        log.info(f"[NewsAgent] Got {len(raw_news)} raw items for {ticker}")

        if not raw_news:
            return {"ticker": ticker, "articles_saved": 0}

        await db.execute(delete(NewsArticle).where(NewsArticle.ticker == ticker))

        articles = []
        embed_docs = []

        for item in raw_news:
            parsed = _parse_item(item)
            if not parsed:
                continue

            article_id = hashlib.md5(f"{ticker}{parsed['url']}".encode()).hexdigest()[:16]

            articles.append(NewsArticle(
                ticker=ticker,
                title=parsed["title"],
                source=parsed["source"],
                url=parsed["url"],
                published_at=parsed["published_at"],
                content=parsed["summary"],
            ))
            embed_docs.append({
                "id": article_id,
                "title": parsed["title"],
                "content": parsed["summary"],
                "source": parsed["source"],
                "published_at": parsed["published_at"].isoformat(),
            })

        db.add_all(articles)
        await db.commit()

        if embed_docs:
            await asyncio.to_thread(store_news, ticker, embed_docs)

        log.info(f"[NewsAgent] Saved {len(articles)} articles for {ticker}")
        return {"ticker": ticker, "articles_saved": len(articles)}
