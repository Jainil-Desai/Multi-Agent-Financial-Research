import './index.css'
import TickerSearch from './components/TickerSearch'
import PriceChart from './components/PriceChart'
import RiskPanel from './components/RiskPanel'
import ReportPanel from './components/ReportPanel'
import { useResearch } from './hooks/useResearch'

const STATUS_LABEL = { queued: 'Queued…', running: 'Running pipeline…', done: 'Done', failed: 'Failed' }

export default function App() {
  const { loading, error, ticker, status, forecast, riskSignals, report, prices, runResearch } = useResearch()

  const hasResults = report || riskSignals.length > 0 || prices.length > 0

  return (
    <div className="min-h-screen bg-[#0f1117] text-slate-200">
      {/* Header */}
      <header className="border-b border-[#2d3148] bg-[#0f1117]/80 backdrop-blur sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center gap-4">
          <div className="flex items-center gap-2">
            <span className="text-xl">📈</span>
            <span className="font-semibold text-white">FinResearch</span>
            <span className="text-xs text-slate-500 bg-[#1e2130] px-2 py-0.5 rounded-full border border-[#2d3148]">AI</span>
          </div>
          <span className="text-slate-600 text-sm hidden sm:block">Multi-Agent Financial Research System</span>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-12">
        {/* Hero */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-white mb-3 tracking-tight">
            AI-Powered Equity Research
          </h1>
          <p className="text-slate-400 text-lg max-w-xl mx-auto">
            Market data · SEC filings · Risk detection · Price forecasting · Analyst report
          </p>
        </div>

        {/* Search */}
        <div className="mb-8">
          <TickerSearch onSubmit={runResearch} loading={loading} />
        </div>

        {/* Error */}
        {error && (
          <div className="mb-6 bg-red-900/20 border border-red-800 text-red-400 rounded-xl px-5 py-4 text-sm">
            ⚠️ {error}
          </div>
        )}

        {/* Status badge while running */}
        {loading && status && (
          <div className="mb-6 flex items-center gap-3 text-sm text-slate-400">
            <span className="inline-block w-2.5 h-2.5 rounded-full bg-purple-500 animate-pulse" />
            {STATUS_LABEL[status] || status}
          </div>
        )}

        {/* Results grid */}
        {hasResults && !loading && (
          <div className="space-y-6">
            {/* Ticker header */}
            <div className="flex items-baseline gap-3">
              <h2 className="text-2xl font-bold text-white font-mono">{ticker}</h2>
              <span className="text-slate-500 text-sm">Research Report</span>
            </div>

            {/* Price chart — full width */}
            {prices.length > 0 && (
              <PriceChart prices={prices} forecast={forecast} ticker={ticker} />
            )}

            {/* Two-column: risk + forecast stats */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <RiskPanel signals={riskSignals} />

              {forecast && !forecast.error && (
                <div className="bg-[#1e2130] border border-[#2d3148] rounded-xl p-5">
                  <h3 className="font-semibold text-white mb-4 flex items-center gap-2">
                    <span>🔮</span> 30-Day Forecast
                  </h3>
                  <div className="space-y-3">
                    {[
                      { label: 'Last Close', value: `$${forecast.last_actual_close}` },
                      { label: 'Predicted (30d)', value: `$${forecast.predicted_close_end}` },
                      { label: 'Expected Move', value: `${forecast.predicted_pct_change > 0 ? '+' : ''}${forecast.predicted_pct_change}%`, color: forecast.trend === 'bullish' ? 'text-green-400' : forecast.trend === 'bearish' ? 'text-red-400' : 'text-purple-400' },
                      { label: 'Trend', value: forecast.trend?.toUpperCase(), color: forecast.trend === 'bullish' ? 'text-green-400' : forecast.trend === 'bearish' ? 'text-red-400' : 'text-purple-400' },
                    ].map(({ label, value, color }) => (
                      <div key={label} className="flex justify-between items-center py-2 border-b border-[#2d3148] last:border-0">
                        <span className="text-slate-400 text-sm">{label}</span>
                        <span className={`font-mono font-semibold text-sm ${color || 'text-white'}`}>{value}</span>
                      </div>
                    ))}
                  </div>
                  {forecast.note && <p className="text-xs text-slate-500 mt-3">{forecast.note}</p>}
                </div>
              )}
            </div>

            {/* Full report */}
            <ReportPanel report={report} />
          </div>
        )}

        {/* Empty state */}
        {!loading && !hasResults && !error && (
          <div className="text-center py-20 text-slate-600">
            <div className="text-5xl mb-4">🔍</div>
            <p className="text-lg">Enter a ticker above to run the full research pipeline</p>
            <p className="text-sm mt-2">Powered by GPT-4o-mini + Prophet + SEC EDGAR</p>
          </div>
        )}
      </main>
    </div>
  )
}
