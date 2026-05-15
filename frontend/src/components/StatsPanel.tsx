import { Activity, MapPin, TrendingUp, Zap } from 'lucide-react'
import type { DetectionStats } from '../types'

interface StatCardProps {
  icon: React.ReactNode
  label: string
  value: string | number
  sub?: string
  accent?: string
}

function StatCard({ icon, label, value, sub, accent = 'text-cyan-400' }: StatCardProps) {
  return (
    <div className="bg-ocean-800 border border-ocean-700 rounded-xl p-5 flex items-start gap-4">
      <div className={`mt-0.5 ${accent}`}>{icon}</div>
      <div>
        <p className="text-slate-400 text-xs uppercase tracking-widest font-medium">{label}</p>
        <p className={`text-2xl font-bold mt-0.5 ${accent}`}>{value}</p>
        {sub && <p className="text-slate-500 text-xs mt-1">{sub}</p>}
      </div>
    </div>
  )
}

interface Props {
  stats: DetectionStats | undefined
  isLoading: boolean
}

export default function StatsPanel({ stats, isLoading }: Props) {
  if (isLoading || !stats) {
    return (
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="bg-ocean-800 border border-ocean-700 rounded-xl p-5 h-24 animate-pulse" />
        ))}
      </div>
    )
  }

  const locationCount = Object.keys(stats.by_location).length
  const highPct = stats.total > 0 ? ((stats.high_confidence_count / stats.total) * 100).toFixed(1) : '0'

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <StatCard
        icon={<Activity size={22} />}
        label="Total Detections"
        value={stats.total.toLocaleString()}
        sub={`${stats.date_range.min} → ${stats.date_range.max}`}
        accent="text-cyan-400"
      />
      <StatCard
        icon={<TrendingUp size={22} />}
        label="Avg Confidence"
        value={`${(stats.avg_confidence * 100).toFixed(1)}%`}
        sub={`Peak: ${(stats.max_confidence * 100).toFixed(1)}%`}
        accent="text-emerald-400"
      />
      <StatCard
        icon={<Zap size={22} />}
        label="High Confidence"
        value={stats.high_confidence_count.toLocaleString()}
        sub={`${highPct}% of all detections (≥90%)`}
        accent="text-amber-400"
      />
      <StatCard
        icon={<MapPin size={22} />}
        label="Active Hydrophones"
        value={locationCount}
        sub={Object.keys(stats.by_location).join(', ')}
        accent="text-violet-400"
      />
    </div>
  )
}
