import { clsx } from 'clsx'
import { MapPin, Clock, FileAudio } from 'lucide-react'
import type { Detection } from '../types'

interface Props {
  detection: Detection
  selected: boolean
  onClick: () => void
}

function confidenceColor(c: number) {
  if (c >= 0.9) return 'text-emerald-400 bg-emerald-400/10 border-emerald-500/30'
  if (c >= 0.7) return 'text-amber-400 bg-amber-400/10 border-amber-500/30'
  return 'text-red-400 bg-red-400/10 border-red-500/30'
}

function confidenceBarColor(c: number) {
  if (c >= 0.9) return 'bg-emerald-400'
  if (c >= 0.7) return 'bg-amber-400'
  return 'bg-red-400'
}

function locationColor(loc: string) {
  if (loc.includes('San Juan')) return 'text-blue-400'
  if (loc.includes('North')) return 'text-orange-400'
  return 'text-red-400'
}

function formatTime(sec: number) {
  const h = Math.floor(sec / 3600)
  const m = Math.floor((sec % 3600) / 60)
  const s = Math.floor(sec % 60)
  if (h > 0) return `${h}h ${m}m ${s}s`
  if (m > 0) return `${m}m ${s}s`
  return `${s}s`
}

export default function DetectionCard({ detection, selected, onClick }: Props) {
  const pct = Math.round(detection.confidence * 100)

  return (
    <button
      onClick={onClick}
      className={clsx(
        'w-full text-left rounded-xl border p-4 transition-all duration-150 hover:border-cyan-500/50',
        selected
          ? 'bg-cyan-950/40 border-cyan-500/60 shadow-lg shadow-cyan-900/20'
          : 'bg-ocean-800 border-ocean-700 hover:bg-ocean-700/50'
      )}
    >
      <div className="flex items-start justify-between gap-2 mb-3">
        <span className={clsx('text-xs font-semibold uppercase tracking-wide', locationColor(detection.location))}>
          <MapPin size={10} className="inline mr-1" />
          {detection.location}
        </span>
        <span
          className={clsx(
            'text-xs font-bold px-2 py-0.5 rounded-full border',
            confidenceColor(detection.confidence)
          )}
        >
          {pct}%
        </span>
      </div>

      {/* Confidence bar */}
      <div className="h-1.5 w-full bg-ocean-700 rounded-full mb-3 overflow-hidden">
        <div
          className={clsx('h-full rounded-full transition-all', confidenceBarColor(detection.confidence))}
          style={{ width: `${pct}%` }}
        />
      </div>

      <div className="flex items-center gap-3 text-xs text-slate-400">
        <span className="flex items-center gap-1">
          <Clock size={10} />
          {formatTime(detection.start_sec)} – {formatTime(detection.end_sec)}
        </span>
        <span className="text-ocean-700">·</span>
        <span className="text-slate-500">{detection.date}</span>
      </div>

      <div className="mt-2 flex items-center gap-1 text-xs text-slate-500 truncate">
        <FileAudio size={10} />
        <span className="truncate">{detection.file}</span>
      </div>
    </button>
  )
}
