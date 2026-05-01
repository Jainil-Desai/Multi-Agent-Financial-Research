import logging
from openai import AsyncOpenAI
from app.config import settings
from app.rag.retriever import query_filings

log = logging.getLogger("finresearch.summarizer")
_client = AsyncOpenAI(api_key=settings.openai_api_key)


class SummarizationAgent:
    """Uses RAG + LLM to summarize SEC filings for a ticker."""

    async def summarize(self, ticker: str, filings: list[dict]) -> str:
        ticker = ticker.upper()
        log.info(f"[SummarizationAgent] Summarizing filings for {ticker}")

        if not filings:
            return "No SEC filings available for summarization."

        chunks = query_filings(ticker, f"{ticker} business operations risk factors revenue", n_results=6)
        if not chunks:
            raw_texts = [f["raw_text"][:2000] for f in filings if f.get("raw_text")]
            context = "\n\n---\n\n".join(raw_texts[:3])
        else:
            context = "\n\n---\n\n".join(chunks)

        if not context.strip():
            return "Insufficient filing text available for summarization."

        filing_labels = ", ".join(
            f"{f.get('form_type', 'filing')} filed {f.get('filed_at', '')}"
            for f in filings[:3]
        )

        prompt = f"""You are a financial analyst. Summarize the following SEC filing excerpts for {ticker} ({filing_labels}).

Focus on:
1. Core business description and revenue model
2. Key financial highlights and trends
3. Major risks disclosed
4. Management's outlook

Filing excerpts:
{context}

Write a concise 3-4 paragraph analyst summary."""

        response = await _client.chat.completions.create(
            model=settings.openai_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=600,
        )
        summary = response.choices[0].message.content.strip()
        log.info(f"[SummarizationAgent] Summary complete for {ticker}")
        return summary
