from datetime import datetime
from sqlalchemy import String, Float, DateTime, Text, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional

from app.database.connection import Base


class PriceBar(Base):
    """Daily OHLCV price data per ticker."""
    __tablename__ = "price_bars"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(String(16), index=True, nullable=False)
    date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    open: Mapped[float] = mapped_column(Float)
    high: Mapped[float] = mapped_column(Float)
    low: Mapped[float] = mapped_column(Float)
    close: Mapped[float] = mapped_column(Float)
    volume: Mapped[float] = mapped_column(Float)


class NewsArticle(Base):
    """News headlines fetched from external feeds."""
    __tablename__ = "news_articles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(String(16), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    source: Mapped[str] = mapped_column(String(128))
    url: Mapped[str] = mapped_column(String(1024))
    published_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    content: Mapped[str] = mapped_column(Text, default="")
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class SecFiling(Base):
    """SEC EDGAR filings metadata."""
    __tablename__ = "sec_filings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(String(16), index=True, nullable=False)
    form_type: Mapped[str] = mapped_column(String(16))
    filed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    accession_number: Mapped[str] = mapped_column(String(64), unique=True)
    document_url: Mapped[str] = mapped_column(String(1024))
    raw_text: Mapped[str] = mapped_column(Text, default="")
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ResearchReport(Base):
    """Generated analyst reports."""
    __tablename__ = "research_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(String(16), index=True, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    summary: Mapped[str] = mapped_column(Text, default="")
    risk_signals: Mapped[str] = mapped_column(Text, default="")
    trend_forecast: Mapped[str] = mapped_column(Text, default="")
    full_report: Mapped[str] = mapped_column(Text, default="")


class ResearchJob(Base):
    """Background pipeline job tracking."""
    __tablename__ = "research_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    ticker: Mapped[str] = mapped_column(String(16), index=True, nullable=False)
    period: Mapped[str] = mapped_column(String(8), default="1y")
    status: Mapped[str] = mapped_column(String(16), default="queued")  # queued | running | done | failed
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    result: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
