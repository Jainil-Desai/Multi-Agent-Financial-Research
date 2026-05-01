import { useState, useRef } from 'react'
import axios from 'axios'

const POLL_INTERVAL = 3000 // ms

export function useResearch() {
  const [state, setState] = useState({
    loading: false,
    error: null,
    ticker: null,
    period: '1y',
    status: null,
    forecast: null,
    riskSignals: [],
    report: null,
    prices: [],
  })
  const pollRef = useRef(null)

  const stopPolling = () => {
    if (pollRef.current) {
      clearInterval(pollRef.current)
      pollRef.current = null
    }
  }

  const runResearch = async (ticker, period = '1y') => {
    stopPolling()
    setState(s => ({
      ...s, loading: true, error: null, status: 'queued',
      ticker: ticker.toUpperCase(), period,
      report: null, forecast: null, riskSignals: [], prices: [],
    }))

    let jobId
    try {
      const res = await axios.post(`/api/v1/research/${ticker}?period=${period}`)
      jobId = res.data.job_id
    } catch (err) {
      setState(s => ({ ...s, loading: false, error: err.response?.data?.detail || err.message }))
      return
    }

    // Poll until done or failed
    pollRef.current = setInterval(async () => {
      try {
        const { data } = await axios.get(`/api/v1/research/jobs/${jobId}`)
        setState(s => ({ ...s, status: data.status }))

        if (data.status === 'done') {
          stopPolling()
          let prices = []
          try {
            const pr = await axios.get(`/api/v1/ingest/market/${ticker}/prices?limit=500`)
            prices = pr.data.prices || []
          } catch (_) {}

          setState(s => ({
            ...s,
            loading: false,
            forecast: data.forecast,
            riskSignals: Array.isArray(data.risk_signals) ? data.risk_signals : [],
            report: data.report,
            prices,
          }))
        } else if (data.status === 'failed') {
          stopPolling()
          setState(s => ({ ...s, loading: false, error: data.error || 'Pipeline failed' }))
        }
      } catch (err) {
        stopPolling()
        setState(s => ({ ...s, loading: false, error: err.message }))
      }
    }, POLL_INTERVAL)
  }

  return { ...state, runResearch }
}
