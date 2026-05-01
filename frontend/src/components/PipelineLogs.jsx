const STAGE_ICONS = {
  market: '📈',
  news: '📰',
  sec: '📄',
  summar: '🔍',
  risk: '⚠️',
  forecast: '🔮',
  report: '📊',
}

function getIcon(log) {
  const l = log.toLowerCase()
  for (const [key, icon] of Object.entries(STAGE_ICONS)) {
    if (l.includes(key)) return icon
  }
  return '✓'
}

export default function PipelineLogs({ logs, loading }) {
  if (!logs.length && !loading) return null

  return (
    <div className="bg-[#1e2130] border border-[#2d3148] rounded-xl p-5">
      <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4">Pipeline Progress</h3>
      <div className="space-y-2">
        {logs.map((log, i) => (
          <div key={i} className="flex items-start gap-3 text-sm">
            <span className="text-base leading-none mt-0.5">{getIcon(log)}</span>
            <span className="text-slate-300">{log}</span>
          </div>
        ))}
        {loading && (
          <div className="flex items-center gap-3 text-sm text-slate-500">
            <span className="inline-block w-3 h-3 rounded-full bg-purple-500 animate-pulse" />
            <span>Running next stage…</span>
          </div>
        )}
      </div>
    </div>
  )
}
