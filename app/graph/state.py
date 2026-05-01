from typing import TypedDict, List, Annotated
import operator


class ResearchState(TypedDict):
    ticker: str
    period: str
    price_bars: List[dict]
    news_articles: List[dict]
    sec_filings: List[dict]
    filing_summary: str
    risk_signals: List[str]
    forecast: dict
    report: str
    logs: Annotated[List[str], operator.add]
