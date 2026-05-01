export default function RiskPanel({ signals }) {
  if (!signals?.length) return null

  return (
    <div className="bg-[#1e2130] border border-[#2d3148] rounded-xl p-5">
      <h3 className="font-semibold text-white mb-4 flex items-center gap-2">
        <span>⚠️</span> Risk Signals
        <span className="ml-auto text-xs font-normal bg-red-900/40 text-red-400 px-2 py-0.5 rounded-full">
          {signals.length} identified
        </span>
      </h3>
      <ul className="space-y-3">
        {signals.map((signal, i) => (
          <li key={i} className="flex gap-3 text-sm">
            <span className="mt-0.5 flex-shrink-0 w-5 h-5 rounded-full bg-red-900/40 text-red-400 flex items-center justify-center text-xs font-bold">
              {i + 1}
            </span>
            <span className="text-slate-300 leading-relaxed">{signal}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}
