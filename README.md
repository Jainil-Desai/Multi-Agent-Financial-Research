# Multi-Agent Financial Research System

An AI-powered equity research platform that orchestrates multiple specialised agents to fetch market data, analyse SEC filings, detect risk signals, forecast price trends, and produce a structured analyst report — all from a single API call.

---

## Architecture

```
POST /research/{ticker}
        │
        ▼
┌─────────────────────────────────────────────────────┐
│                  LangGraph Pipeline                  │
│                                                     │
│  fetch_market → fetch_news → fetch_sec              │
│       → summarize → detect_risks                    │
│       → run_forecast → generate_report              │
└─────────────────────────────────────────────────────┘
        │                    │
        ▼                    ▼
   SQLite DB            ChromaDB
 (price bars,         (SEC filings +
  news, reports)       news embeddings)
```

**Stack:** Python 3.11 · FastAPI · LangGraph · OpenAI GPT-4o-mini · ChromaDB · Prophet · yfinance · SEC EDGAR API · React · Recharts · Docker

---

## Agents

| Agent | What it does |
|---|---|
| `MarketDataAgent` | Fetches 1–5y OHLCV history via yfinance, stores in SQLite |
| `NewsAgent` | Fetches headlines via yfinance, embeds in ChromaDB |
| `SECAgent` | Pulls 10-K / 10-Q filings from EDGAR, embeds in ChromaDB |
| `SummarizationAgent` | RAG over filing chunks → GPT-4o-mini summary |
| `RiskAgent` | Semantic search over news + filings → structured risk signals |
| `ForecastAgent` | Prophet time-series model → 30-day price forecast |
| `ReportAgent` | Assembles all outputs → formatted analyst report |

---

## Quickstart

### Prerequisites
- Python 3.11
- Node.js 18+
- OpenAI API key

### 1. Clone and set up the backend

```bash
git clone <repo-url>
cd Multi_Agent_Financial_Research_System

python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### 2. Start the API

```bash
uvicorn app.main:app --reload
# API running at http://127.0.0.1:8000
# Swagger docs at http://127.0.0.1:8000/docs
```

### 3. Start the frontend

```bash
cd frontend
npm install
npm run dev
# UI running at http://localhost:5173
```

---

## Usage

### Via the UI
Open `http://localhost:5173`, enter a ticker (e.g. `AAPL`), select a time period, and click **Run Research**. Results appear when the pipeline completes (~30–90s).

### Via the API

**Submit a research job:**
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/research/AAPL?period=1y"
# → { "job_id": "...", "status": "queued" }
```

**Poll for results:**
```bash
curl "http://127.0.0.1:8000/api/v1/research/jobs/{job_id}"
# → { "status": "done", "report": "...", "forecast": {...}, "risk_signals": [...] }
```

**Ingest data individually:**
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/ingest/market/AAPL"
curl -X POST "http://127.0.0.1:8000/api/v1/ingest/news/AAPL"
curl -X POST "http://127.0.0.1:8000/api/v1/ingest/sec/AAPL"
```

---

## Docker

```bash
cp .env.example .env   # add your OPENAI_API_KEY
docker-compose up --build
# API at http://localhost:8000
```

---

## Project Structure

```
app/
├── agents/          # Individual research agents
├── api/             # FastAPI routers (ingest, research)
├── database/        # SQLAlchemy models + async connection
├── graph/           # LangGraph state, nodes, compiled graph
├── rag/             # Embedding service + ChromaDB retriever
└── vector_store/    # ChromaDB client setup

frontend/
└── src/
    ├── components/  # PriceChart, RiskPanel, ReportPanel, TickerSearch
    └── hooks/       # useResearch (polling hook)
```

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `OPENAI_API_KEY` | Yes | OpenAI API key |
| `OPENAI_MODEL` | No | Model name (default: `gpt-4o-mini`) |
| `DATABASE_URL` | No | SQLAlchemy URL (default: SQLite) |
| `CHROMA_PERSIST_DIR` | No | ChromaDB storage path |
| `NEWS_API_KEY` | No | NewsAPI key (optional enhancement) |
