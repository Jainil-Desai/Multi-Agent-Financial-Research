import {
  ResponsiveContainer, ComposedChart, Line, Area, XAxis, YAxis,
  Tooltip, CartesianGrid, Legend, ReferenceLine,
} from 'recharts'

function buildChartData(prices, forecast) {
  const historical = [...prices].reverse().map(p => ({
    date: p.date,
    close: parseFloat(p.close.toFixed(2)),
    type: 'historical',
  }))

  if (!forecast?.predictions?.length) return historical

  const lastActual = historical[historical.length - 1]
  const forecastPoints = forecast.predictions.map(p => ({
    date: p.date,
    predicted: p.predicted_close,
    lower: p.lower_bound,
    upper: p.upper_bound,
    type: 'forecast',
  }))

  return [
    ...historical,
    { ...lastActual, predicted: lastActual.close },
    ...forecastPoints,
  ]
}

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-[#1e2130] border border-[#2d3148] rounded-lg p-3 text-xs">
      <p className="text-slate-400 mb-1.5">{label}</p>
      {payload.map(p => (
        <p key={p.dataKey} style={{ color: p.color }}>
          {p.name}: ${p.value?.toFixed(2)}
        </p>
      ))}
    </div>
  )
}

export default function PriceChart({ prices, forecast, ticker }) {
  if (!prices.length) return null

  const data = buildChartData(prices, forecast)
  const trendColor = forecast?.trend === 'bullish' ? '#22c55e' : forecast?.trend === 'bearish' ? '#ef4444' : '#a78bfa'

  return (
    <div className="bg-[#1e2130] border border-[#2d3148] rounded-xl p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-white">{ticker} — Price & 30-Day Forecast</h3>
        {forecast?.trend && (
          <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${
            forecast.trend === 'bullish' ? 'bg-green-900/50 text-green-400' :
            forecast.trend === 'bearish' ? 'bg-red-900/50 text-red-400' :
            'bg-purple-900/50 text-purple-400'
          }`}>
            {forecast.trend.toUpperCase()} {forecast.predicted_pct_change != null ? `${forecast.predicted_pct_change > 0 ? '+' : ''}${forecast.predicted_pct_change}%` : ''}
          </span>
        )}
      </div>

      <ResponsiveContainer width="100%" height={320}>
        <ComposedChart data={data} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#2d3148" />
          <XAxis
            dataKey="date"
            tick={{ fill: '#64748b', fontSize: 11 }}
            tickFormatter={d => d?.slice(5)}
            interval={Math.floor(data.length / 8)}
          />
          <YAxis
            tick={{ fill: '#64748b', fontSize: 11 }}
            domain={['auto', 'auto']}
            tickFormatter={v => `$${v}`}
            width={60}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend wrapperStyle={{ fontSize: 12, color: '#94a3b8' }} />

          <Area dataKey="upper" fill={trendColor} fillOpacity={0.08} stroke="none" name="Upper bound" legendType="none" />
          <Area dataKey="lower" fill={trendColor} fillOpacity={0.08} stroke="none" name="Lower bound" legendType="none" />

          <Line dataKey="close" stroke="#818cf8" strokeWidth={2} dot={false} name="Close" connectNulls />
          <Line dataKey="predicted" stroke="#f59e0b" strokeWidth={2.5} strokeDasharray="6 3" dot={false} name="Forecast" connectNulls />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  )
}
