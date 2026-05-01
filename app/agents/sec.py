import asyncio
import logging
from datetime import datetime

import httpx
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import SecFiling
from app.rag.retriever import store_filing

log = logging.getLogger("finresearch.sec")

HEADERS = {"User-Agent": "FinResearchBot contact@finresearch.dev"}
TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
FILING_INDEX_URL = "https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/index.json"
EDGAR_ARCHIVE = "https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/{filename}"


def _get_cik(ticker: str, tickers_data: dict) -> str | None:
    t = ticker.upper()
    for entry in tickers_data.values():
        if entry.get("ticker", "").upper() == t:
            return str(entry["cik_str"]).zfill(10)
    return None


async def _fetch_json(client: httpx.AsyncClient, url: str) -> dict:
    r = await client.get(url, headers=HEADERS, follow_redirects=True)
    r.raise_for_status()
    return r.json()


async def _fetch_text(client: httpx.AsyncClient, url: str, max_chars: int = 12000) -> str:
    r = await client.get(url, headers=HEADERS, follow_redirects=True)
    r.raise_for_status()
    text = r.text
    return text[:max_chars]


class SECAgent:
    """Fetches 10-K and 10-Q filings from SEC EDGAR and stores in SQLite + ChromaDB."""

    async def fetch(self, ticker: str, db: AsyncSession, forms: list[str] = None) -> dict:
        if forms is None:
            forms = ["10-K", "10-Q"]
        ticker = ticker.upper()
        log.info(f"[SECAgent] Fetching {forms} filings for {ticker}")

        async with httpx.AsyncClient(timeout=30) as client:
            tickers_data = await _fetch_json(client, TICKERS_URL)
            cik = _get_cik(ticker, tickers_data)
            if not cik:
                log.warning(f"[SECAgent] CIK not found for {ticker}")
                return {"ticker": ticker, "filings_saved": 0, "message": "CIK not found"}

            submissions = await _fetch_json(client, SUBMISSIONS_URL.format(cik=cik))
            filings_meta = submissions.get("filings", {}).get("recent", {})

            form_types = filings_meta.get("form", [])
            accessions = filings_meta.get("accessionNumber", [])
            dates = filings_meta.get("filingDate", [])
            primary_docs = filings_meta.get("primaryDocument", [])

            await db.execute(delete(SecFiling).where(SecFiling.ticker == ticker))

            saved = []
            seen_forms: dict[str, int] = {}

            for form, accession, date_str, doc in zip(form_types, accessions, dates, primary_docs):
                if form not in forms:
                    continue
                if seen_forms.get(form, 0) >= 2:
                    continue

                accession_clean = accession.replace("-", "")
                doc_url = EDGAR_ARCHIVE.format(cik=cik.lstrip("0"), accession=accession_clean, filename=doc)
                index_url = FILING_INDEX_URL.format(cik=cik.lstrip("0"), accession=accession_clean)

                try:
                    raw_text = await _fetch_text(client, doc_url)
                except Exception as e:
                    log.warning(f"[SECAgent] Could not fetch doc for {accession}: {e}")
                    raw_text = ""

                filed_at = datetime.strptime(date_str, "%Y-%m-%d") if date_str else datetime.utcnow()

                filing = SecFiling(
                    ticker=ticker,
                    form_type=form,
                    filed_at=filed_at,
                    accession_number=accession,
                    document_url=doc_url,
                    raw_text=raw_text,
                )
                db.add(filing)
                saved.append({"form": form, "accession": accession, "filed": date_str})

                if raw_text:
                    await asyncio.to_thread(store_filing, ticker, accession, form, raw_text)

                seen_forms[form] = seen_forms.get(form, 0) + 1

            await db.commit()
            log.info(f"[SECAgent] Saved {len(saved)} filings for {ticker}")
            return {"ticker": ticker, "filings_saved": len(saved), "filings": saved}
