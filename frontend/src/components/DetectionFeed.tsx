import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Radio, Filter } from 'lucide-react'
import { fetchDetections } from '../api/client'
import DetectionCard from './DetectionCard'
import type { Detection } from '../types'

interface Props {
  onSelect: (d: Detection | null) => void
  selected: Detection | null
}

const LOCATIONS = [
  'All',
  'Dyes Inlet South',
  'Dyes Inlet North',
  'Orcasound Lab - San Juan Island',
]

const CONFIDENCE_FILTERS = [
  { label: 'All', value: 0 },
  { label: '≥70%', value: 0.7 },
  { label: '≥90%', value: 0.9 },
]

export default function DetectionFeed({ onSelect, selected }: Props) {
  const [locationFilter, setLocationFilter] = useState('All')
  const [confFilter, setConfFilter] = useState(0)

  const { data, isLoading, isError } = useQuery({
    queryKey: ['detections', locationFilter, confFilter],
    queryFn: () =>
      fetchDetections({
        location: locationFilter === 'All' ? undefined : locationFilter,
        min_confidence: confFilter,
        limit: 200,
      }),
    refetchInterval: 10_000,
  })

  return (
    <div className="flex flex-col h-full bg-ocean-800 border border-ocean-700 rounded-xl overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 border-b border-ocean-700 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Radio size={15} className="text-cyan-400 animate-pulse" />
          <span className="text-sm font-semibold text-slate-200">Detection Feed</span>
          {data && (
            <span className="text-xs bg-cyan-900/50 text-cyan-300 px-2 py-0.5 rounded-full border border-cyan-800">
              {data.length}
            </span>
          )}
        </div>
        <Filter size={14} className="text-slate-500" />
      </div>

      {/* Filters */}
      <div className="px-3 py-2.5 border-b border-ocean-700 space-y-2">
        {/* Location filter */}
        <div className="flex gap-1 flex-wrap">
          {LOCATIONS.map((loc) => (
            <button
              key={loc}
              onClick={() => setLocationFilter(loc)}
              className={`text-xs px-2 py-1 rounded-md transition-colors ${
                locationFilter === loc
                  ? 'bg-cyan-600 text-white'
                  : 'bg-ocean-700 text-slate-400 hover:bg-ocean-600'
              }`}
            >
              {loc === 'Orcasound Lab - San Juan Island' ? 'San Juan' : loc}
            </button>
          ))}
        </div>
        {/* Confidence filter */}
        <div className="flex gap-1">
          {CONFIDENCE_FILTERS.map((f) => (
            <button
              key={f.label}
              onClick={() => setConfFilter(f.value)}
              className={`text-xs px-2 py-1 rounded-md transition-colors ${
                confFilter === f.value
                  ? 'bg-emerald-700 text-white'
                  : 'bg-ocean-700 text-slate-400 hover:bg-ocean-600'
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      {/* List */}
      <div className="flex-1 overflow-y-auto scrollbar-ocean p-3 space-y-2">
        {isLoading && (
          <div className="space-y-2">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="h-24 bg-ocean-700 rounded-xl animate-pulse" />
            ))}
          </div>
        )}

        {isError && (
          <div className="flex flex-col items-center justify-center h-40 text-slate-500 text-sm">
            <p>Could not connect to backend.</p>
            <p className="text-xs mt-1 text-slate-600">Make sure FastAPI is running on :8000</p>
          </div>
        )}

        {data?.map((detection) => (
          <DetectionCard
            key={detection.id}
            detection={detection}
            selected={selected?.id === detection.id}
            onClick={() => onSelect(selected?.id === detection.id ? null : detection)}
          />
        ))}

        {data?.length === 0 && !isLoading && (
          <p className="text-center text-slate-500 text-sm mt-10">No detections found.</p>
        )}
      </div>
    </div>
  )
}
