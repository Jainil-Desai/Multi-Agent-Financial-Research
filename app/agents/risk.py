import logging
from openai import AsyncOpenAI
from app.config import settings
from app.rag.retriever import query_news, query_filings

log = logging.getLogger("finresearch.risk")
_client = AsyncOpenAI(api_key=settings.openai_api_key)


class RiskAgent:
    """Detects risk signals from news headlines and SEC filings."""

    async def detect(self, ticker: str, news: list[dict], filings: list[dict]) -> list[str]:
        ticker = ticker.upper()
        log.info(f"[RiskAgent] Detecting risks for {ticker}")

        news_chunks = query_news(ticker, f"{ticker} lawsuit regulation investigation earnings miss risk", n_results=5)
        filing_chunks = query_filings(ticker, f"{ticker} risk factors litigation competition headwinds", n_results=5)

        news_text = "\n".join(f"- {n['title']}" for n in news[:15]) if news else ""
        rag_news = "\n".join(news_chunks)
        rag_filings = "\n".join(filing_chunks)

        context = f"""Recent headlines for {ticker}:
{news_text}

Relevant news context (semantic search):
{rag_news}

Relevant filing risk factors:
{rag_filings}"""

        prompt = f"""You are a financial risk analyst reviewing {ticker}.

Based on the following data, identify specific risk signals:

{context}

Return a JSON array of risk signal strings. Each string should be concise (1-2 sentences) and specific.
Example format: ["Risk 1 description", "Risk 2 description", ...]

Identify up to 6 distinct risk signals. Return only the JSON array, no other text."""

        response = await _client.chat.completions.create(
            model=settings.openai_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=400,
        )

        import json, re
        raw = response.choices[0].message.content.strip()
        # Strip markdown code fences if the LLM wrapped the JSON
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw).strip()
        try:
            signals = json.loads(raw)
            if not isinstance(signals, list):
                signals = [str(signals)]
        except json.JSONDecodeError:
            signals = [line.strip("- ").strip() for line in raw.splitlines() if line.strip() and not line.strip().startswith("[")]

        log.info(f"[RiskAgent] Found {len(signals)} risk signals for {ticker}")
        return signals
