import { useState } from 'react'

const SUGGESTIONS = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META', 'JPM']

const PERIODS = [
  { value: '1mo', label: '1M' },
  { value: '3mo', label: '3M' },
  { value: '6mo', label: '6M' },
  { value: '1y',  label: '1Y' },
  { value: '2y',  label: '2Y' },
  { value: '5y',  label: '5Y' },
]

export default function TickerSearch({ onSubmit, loading }) {
  const [value, setValue] = useState('')
  const [period, setPeriod] = useState('1y')

  const handleSubmit = (e) => {
    e.preventDefault()
    if (value.trim()) onSubmit(value.trim().toUpperCase(), period)
  }

  return (
    <div className="w-full max-w-2xl mx-auto">
      <form onSubmit={handleSubmit} className="flex gap-3">
        <input
          type="text"
          value={value}
          onChange={e => setValue(e.target.value.toUpperCase())}
          placeholder="Enter ticker symbol (e.g. AAPL)"
          disabled={loading}
          maxLength={10}
          className="flex-1 bg-[#1e2130] border border-[#2d3148] rounded-xl px-5 py-3.5 text-white placeholder-slate-500 text-lg font-mono tracking-widest focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500 disabled:opacity-50 transition-all"
        />
        <button
          type="submit"
          disabled={loading || !value.trim()}
          className="px-7 py-3.5 bg-purple-600 hover:bg-purple-500 disabled:bg-purple-900 disabled:text-purple-400 text-white font-semibold rounded-xl transition-all duration-150 text-sm whitespace-nowrap"
        >
          {loading ? 'Running…' : 'Run Research'}
        </button>
      </form>

      {/* Period selector + quick tickers */}
      <div className="flex items-center justify-between mt-3 flex-wrap gap-2">
        <div className="flex gap-2 flex-wrap">
          {SUGGESTIONS.map(t => (
            <button
              key={t}
              onClick={() => { setValue(t); onSubmit(t, period) }}
              disabled={loading}
              className="px-3 py-1 text-xs font-mono bg-[#1e2130] border border-[#2d3148] text-slate-400 hover:text-purple-400 hover:border-purple-600 rounded-lg transition-all disabled:opacity-40"
            >
              {t}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-1 bg-[#1e2130] border border-[#2d3148] rounded-lg p-1">
          {PERIODS.map(p => (
            <button
              key={p.value}
              onClick={() => setPeriod(p.value)}
              disabled={loading}
              className={`px-3 py-1 text-xs font-semibold rounded-md transition-all disabled:opacity-40 ${
                period === p.value
                  ? 'bg-purple-600 text-white'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
