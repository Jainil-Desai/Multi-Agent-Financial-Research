import ReactMarkdown from 'react-markdown'
import { useState } from 'react'

export default function ReportPanel({ report }) {
  const [copied, setCopied] = useState(false)
  if (!report) return null

  const copy = () => {
    navigator.clipboard.writeText(report)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="bg-[#1e2130] border border-[#2d3148] rounded-xl p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-white flex items-center gap-2">
          <span>📊</span> Analyst Report
        </h3>
        <button
          onClick={copy}
          className="text-xs text-slate-400 hover:text-purple-400 border border-[#2d3148] hover:border-purple-700 px-3 py-1 rounded-lg transition-all"
        >
          {copied ? '✓ Copied' : 'Copy'}
        </button>
      </div>
      <div className="report-content prose prose-invert max-w-none text-sm leading-relaxed">
        <ReactMarkdown>{report}</ReactMarkdown>
      </div>
    </div>
  )
}
