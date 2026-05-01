import asyncio
import json
import logging
import uuid
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, HTTPException
from sqlalchemy import select, update

from app.database.connection import AsyncSessionLocal
from app.database.models import ResearchJob, ResearchReport
from app.graph.graph import run_pipeline

log = logging.getLogger("finresearch.api.research")
router = APIRouter(prefix="/research", tags=["research"])

VALID_PERIODS = {"1mo", "3mo", "6mo", "1y", "2y", "5y"}


async def _run_job(job_id: str, ticker: str, period: str):
    """Background task: run pipeline and write result back to DB."""
    async with AsyncSessionLocal() as db:
        await db.execute(
            update(ResearchJob)
            .where(ResearchJob.id == job_id)
            .values(status="running", updated_at=datetime.utcnow())
        )
        await db.commit()

    try:
        final_state = await run_pipeline(ticker, period=period)
        result = json.dumps({
            "ticker": ticker,
            "forecast": final_state.get("forecast"),
            "risk_signals": final_state.get("risk_signals"),
            "report": final_state.get("report"),
            "pipeline_logs": final_state.get("logs"),
        })
        async with AsyncSessionLocal() as db:
            await db.execute(
                update(ResearchJob)
                .where(ResearchJob.id == job_id)
                .values(status="done", result=result, updated_at=datetime.utcnow())
            )
            await db.commit()
    except Exception as e:
        log.error(f"[Job {job_id}] failed: {e}")
        async with AsyncSessionLocal() as db:
            await db.execute(
                update(ResearchJob)
                .where(ResearchJob.id == job_id)
                .values(status="failed", error=str(e), updated_at=datetime.utcnow())
            )
            await db.commit()


@router.post("/{ticker}")
async def run_research(ticker: str, period: str = "1y", background_tasks: BackgroundTasks = None):
    """Submit a research pipeline job. Returns a job_id immediately.

    Poll GET /api/v1/research/jobs/{job_id} for status and results.
    period options: 1mo, 3mo, 6mo, 1y, 2y, 5y
    """
    if period not in VALID_PERIODS:
        period = "1y"
    ticker = ticker.upper()
    job_id = str(uuid.uuid4())

    async with AsyncSessionLocal() as db:
        db.add(ResearchJob(id=job_id, ticker=ticker, period=period, status="queued"))
        await db.commit()

    background_tasks.add_task(_run_job, job_id, ticker, period)
    log.info(f"[API] Queued job {job_id} for {ticker} period={period}")

    return {"job_id": job_id, "ticker": ticker, "period": period, "status": "queued"}


@router.get("/jobs/{job_id}")
async def get_job(job_id: str):
    """Poll for pipeline job status and results."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(ResearchJob).where(ResearchJob.id == job_id))
        job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    response = {
        "job_id": job.id,
        "ticker": job.ticker,
        "period": job.period,
        "status": job.status,
        "created_at": job.created_at.isoformat(),
        "updated_at": job.updated_at.isoformat(),
    }
    if job.status == "done" and job.result:
        response.update(json.loads(job.result))
    if job.status == "failed":
        response["error"] = job.error

    return response


@router.get("/{ticker}/latest")
async def get_latest_report(ticker: str):
    """Return the most recently generated report for a ticker."""
    ticker = ticker.upper()
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(ResearchReport)
            .where(ResearchReport.ticker == ticker)
            .order_by(ResearchReport.generated_at.desc())
            .limit(1)
        )
        report = result.scalar_one_or_none()

    if not report:
        raise HTTPException(
            status_code=404,
            detail=f"No report found for {ticker}. Run POST /api/v1/research/{ticker} first.",
        )
    return {
        "id": report.id,
        "ticker": report.ticker,
        "generated_at": report.generated_at.isoformat(),
        "summary": report.summary,
        "risk_signals": report.risk_signals,
        "trend_forecast": report.trend_forecast,
        "full_report": report.full_report,
    }
