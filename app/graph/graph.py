from langgraph.graph import StateGraph, END

from app.graph.state import ResearchState
from app.graph.nodes import (
    fetch_market_node,
    fetch_news_node,
    fetch_sec_node,
    summarize_node,
    risk_node,
    forecast_node,
    report_node,
)

_graph = None


def build_graph():
    workflow = StateGraph(ResearchState)

    workflow.add_node("fetch_market", fetch_market_node)
    workflow.add_node("fetch_news", fetch_news_node)
    workflow.add_node("fetch_sec", fetch_sec_node)
    workflow.add_node("summarize", summarize_node)
    workflow.add_node("detect_risks", risk_node)
    workflow.add_node("run_forecast", forecast_node)
    workflow.add_node("generate_report", report_node)

    workflow.set_entry_point("fetch_market")
    workflow.add_edge("fetch_market", "fetch_news")
    workflow.add_edge("fetch_news", "fetch_sec")
    workflow.add_edge("fetch_sec", "summarize")
    workflow.add_edge("summarize", "detect_risks")
    workflow.add_edge("detect_risks", "run_forecast")
    workflow.add_edge("run_forecast", "generate_report")
    workflow.add_edge("generate_report", END)

    return workflow.compile()


def get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph


async def run_pipeline(ticker: str, period: str = "1y") -> ResearchState:
    graph = get_graph()
    initial_state: ResearchState = {
        "ticker": ticker.upper(),
        "period": period,
        "price_bars": [],
        "news_articles": [],
        "sec_filings": [],
        "filing_summary": "",
        "risk_signals": [],
        "forecast": {},
        "report": "",
        "logs": [],
    }
    return await graph.ainvoke(initial_state)
