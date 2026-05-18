import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Waves, Wifi, WifiOff, RefreshCw, Upload } from 'lucide-react'
import { fetchStats, fetchHealth, fetchInsights } from '../api/client'
import StatsPanel from './StatsPanel'
import DetectionFeed from './DetectionFeed'
import SpectrogramViewer from './SpectrogramViewer'
import ConfidenceChart from './ConfidenceChart'
import HydrophoneMap from './HydrophoneMap'
import type { Detection } from '../types'

export default function Dashboard() {
  const [selected, setSelected] = useState<Detection | null>(null)

  const { data: stats, isLoading: statsLoading, refetch: refetchStats } = useQuery({
    queryKey: ['stats'],
    queryFn: fetchStats,
    refetchInterval: 10_000,
  })

  const { data: health, isError: healthError } = useQuery({
    queryKey: ['health'],
    queryFn: fetchHealth,
    refetchInterval: 5_000,
    retry: 1,
  })

  const { data: insights } = useQuery({
    queryKey: ['insights'],
    queryFn: fetchInsights,
    staleTime: 300_000,
  })

  const isConnected = !healthError && health?.status === 'ok'

  return (
    <div className="min-h-screen bg-ocean-900 flex flex-col">
      {/* Header */}
      <header className="border-b border-ocean-700 bg-ocean-950/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-[1600px] mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-900/40">
              <Waves size={16} className="text-white" />
            </div>
            <div>
              <span className="text-lg font-bold text-white tracking-tight">OrcaPath</span>
              <span className="text-lg font-bold text-cyan-400 tracking-tight"> AI</span>
              <span className="ml-2 text-xs text-slate-500 font-normal hidden sm:inline">
                Orca Call Detection System
              </span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className={`flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full border ${
              isConnected
                ? 'text-emerald-400 border-emerald-700 bg-emerald-900/30'
                : 'text-red-400 border-red-800 bg-red-900/20'
            }`}>
              {isConnected ? <Wifi size={12} /> : <WifiOff size={12} />}
              {isConnected ? 'API Connected' : 'API Offline'}
            </div>
            <button
              onClick={() => refetchStats()}
              className="p-1.5 rounded-lg text-slate-400 hover:text-cyan-400 hover:bg-ocean-700 transition-colors"
            >
              <RefreshCw size={14} />
            </button>
            <button className="flex items-center gap-1.5 text-xs bg-cyan-600 hover:bg-cyan-500 text-white px-3 py-1.5 rounded-lg transition-colors font-medium">
              <Upload size={12} />
              Detect Audio
            </button>
          </div>
        </div>
      </header>

      {/* Main */}
      <main className="flex-1 max-w-[1600px] mx-auto w-full px-4 py-5 space-y-4">
        <StatsPanel stats={stats} isLoading={statsLoading} />

        {/* Feed + Map */}
        <div className="grid grid-cols-1 lg:grid-cols-[380px_1fr] gap-4 min-h-0" style={{ height: '516px' }}>
          <DetectionFeed onSelect={setSelected} selected={selected} />
          <HydrophoneMap selected={selected} />
        </div>

        {/* Gemma 4 Insights */}
        {insights?.summary && (
          <div className="bg-ocean-800 border border-cyan-900 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-2">
              <div className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
              <span className="text-xs font-semibold text-cyan-400 uppercase tracking-wide">
                Gemma 4 Research Insights
              </span>
            </div>
            <p className="text-sm text-slate-300 leading-relaxed">{insights.summary}</p>
          </div>
        )}

        {/* Spectrogram + Chart */}
        <div className="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-4">
          <div>
            {selected ? (
              <SpectrogramViewer detection={selected} onClose={() => setSelected(null)} />
            ) : (
              <div className="bg-ocean-800 border border-ocean-700 border-dashed rounded-xl p-8 flex flex-col items-center justify-center text-slate-600 text-sm gap-2">
                <Waves size={28} className="text-ocean-700" />
                <p>Select a detection to view spectrogram analysis</p>
              </div>
            )}
          </div>
          <ConfidenceChart stats={stats} />
        </div>
      </main>

      <footer className="border-t border-ocean-700 py-3 text-center text-xs text-slate-600">
        OrcaPath AI · RandomForest classifier · 44.1 kHz · Mel spectrogram (128 bins · fmax 20 kHz)
      </footer>
    </div>
  )
}