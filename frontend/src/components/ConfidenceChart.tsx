import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts'
import type { DetectionStats } from '../types'

interface Props {
  stats: DetectionStats | undefined
}

const COLORS: Record<string, string> = {
  'Dyes Inlet South': '#ef4444',
  'Dyes Inlet North': '#f97316',
  'Orcasound Lab - San Juan Island': '#3b82f6',
}

export default function ConfidenceChart({ stats }: Props) {
  if (!stats) return null

  const data = Object.entries(stats.by_location).map(([name, count]) => ({
    name: name.replace('Orcasound Lab - ', '').replace('Dyes Inlet ', 'Dyes '),
    count,
    fullName: name,
  }))

  return (
    <div className="bg-ocean-800 border border-ocean-700 rounded-xl p-4">
      <p className="text-sm font-semibold text-slate-200 mb-3">Detections by Location</p>
      <ResponsiveContainer width="100%" height={120}>
        <BarChart data={data} margin={{ top: 0, right: 10, left: -10, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
          <XAxis
            dataKey="name"
            tick={{ fill: '#94a3b8', fontSize: 11 }}
            axisLine={{ stroke: '#334155' }}
            tickLine={false}
          />
          <YAxis
            tick={{ fill: '#94a3b8', fontSize: 11 }}
            axisLine={false}
            tickLine={false}
            tickFormatter={(v: number) => (v >= 1000 ? `${(v / 1000).toFixed(0)}k` : String(v))}
          />
          <Tooltip
            contentStyle={{
              background: '#1e293b',
              border: '1px solid #334155',
              borderRadius: '8px',
              color: '#e2e8f0',
              fontSize: 12,
            }}
            formatter={(v: number) => [v.toLocaleString(), 'Detections']}
          />
          <Bar dataKey="count" radius={[4, 4, 0, 0]}>
            {data.map((entry) => (
              <Cell key={entry.fullName} fill={COLORS[entry.fullName] ?? '#06b6d4'} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
