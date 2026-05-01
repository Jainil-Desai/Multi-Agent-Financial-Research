import logging
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database.models import ResearchReport

log = logging.getLogger("finresearch.report")
_client = AsyncOpenAI(api_key=settings.openai_api_key)


class ReportAgent:
    """Assembles all research outputs into a structured analyst report."""

    async def generate(
        self,
        ticker: str,
        price_bars: list[dict],
        news: list[dict],
        filing_summary: str,
        risk_signals: list[str],
        forecast: dict,
        db: AsyncSession,
    ) -> dict:
        ticker = ticker.upper()
        log.info(f"[ReportAgent] Generating report for {ticker}")

        recent_prices = price_bars[:5] if price_bars else []
        price_summary = ""
        if recent_prices:
            latest = recent_prices[0]
            oldest = recent_prices[-1]
            price_summary = (
                f"Latest close: ${latest['close']:.2f} on {latest['date']}. "
                f"5-day range: ${min(b['low'] for b in recent_prices):.2f} - ${max(b['high'] for b in recent_prices):.2f}."
            )

        news_summary = "\n".join(f"- {n['title']}" for n in news[:8]) if news else "No recent news available."
        risk_text = "\n".join(f"- {r}" for r in risk_signals) if risk_signals else "No specific risks identified."
        forecast_text = (
            f"{forecast.get('trend', 'unknown').capitalize()} outlook: "
            f"predicted {forecast.get('predicted_pct_change', 0):+.1f}% over {forecast.get('forecast_days', 30)} days "
            f"(target: ${forecast.get('predicted_close_end', 0):.2f})."
            if forecast and not forecast.get("error")
            else "Forecast unavailable."
        )

        prompt = f"""You are a senior equity research analyst. Write a professional analyst report for {ticker}.

## Data Summary

**Price Action:**
{price_summary}

**Recent News Headlines:**
{news_summary}

**SEC Filing Summary:**
{filing_summary}

**Risk Signals:**
{risk_text}

**30-Day Price Forecast:**
{forecast_text}

---

Write a structured analyst report with these sections:
1. **Executive Summary** (2-3 sentences)
2. **Business Overview** (from filings)
3. **Recent Developments** (from news)
4. **Risk Assessment**
5. **Price Outlook & Forecast**
6. **Analyst Rating** (Buy / Hold / Sell with one-line rationale)

Do not include any header, title, date, analyst name, or firm name. Start directly with the Executive Summary section.
Be concise, professional, and data-driven."""

        response = await _client.chat.completions.create(
            model=settings.openai_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=900,
        )
        full_report = response.choices[0].message.content.strip()

        report_row = ResearchReport(
            ticker=ticker,
            summary=filing_summary[:500],
            risk_signals="\n".join(risk_signals),
            trend_forecast=forecast_text,
            full_report=full_report,
        )
        db.add(report_row)
        await db.commit()
        await db.refresh(report_row)

        log.info(f"[ReportAgent] Report saved for {ticker} (id={report_row.id})")
        return {
            "id": report_row.id,
            "ticker": ticker,
            "generated_at": report_row.generated_at.isoformat(),
            "forecast": forecast,
            "risk_signals": risk_signals,
            "full_report": full_report,
        }
