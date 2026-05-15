import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { X, ChevronLeft, ChevronRight, ImageIcon } from 'lucide-react'
import { fetchSpectrograms } from '../api/client'
import type { Detection } from '../types'

interface Props {
  detection: Detection
  onClose: () => void
}

export default function SpectrogramViewer({ detection, onClose }: Props) {
  const [imgIdx, setImgIdx] = useState(0)

  const { data: spectrograms, isLoading } = useQuery({
    queryKey: ['spectrograms'],
    queryFn: fetchSpectrograms,
    staleTime: 300_000,
  })

  const pct = Math.round(detection.confidence * 100)
  const confColor = pct >= 90 ? 'text-emerald-400' : pct >= 70 ? 'text-amber-400' : 'text-red-400'

  return (
    <div className="bg-ocean-800 border border-ocean-700 rounded-xl p-4 animate-in slide-in-from-bottom-2">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div>
          <p className="text-sm font-semibold text-slate-200">Spectrogram Analysis</p>
          <p className="text-xs text-slate-500 mt-0.5">
            {detection.location} &nbsp;·&nbsp; {detection.date} &nbsp;·&nbsp;
            {detection.start_sec.toFixed(1)}s–{detection.end_sec.toFixed(1)}s &nbsp;·&nbsp;
            <span className={confColor}>{pct}% confidence</span>
          </p>
        </div>
        <button
          onClick={onClose}
          className="text-slate-500 hover:text-slate-300 transition-colors p-1 rounded-lg hover:bg-ocean-700"
        >
          <X size={16} />
        </button>
      </div>

      <div className="flex gap-4">
        {/* Detection detail card */}
        <div className="w-48 shrink-0 space-y-2 text-xs">
          <div className="bg-ocean-900 rounded-lg p-3 space-y-2 border border-ocean-700">
            <p className="font-semibold text-slate-300 uppercase tracking-wide text-xs">Detection</p>
            <div>
              <p className="text-slate-500">File</p>
              <p className="text-slate-300 break-all">{detection.file}</p>
            </div>
            <div>
              <p className="text-slate-500">Segment</p>
              <p className="text-slate-300">
                {detection.start_sec.toFixed(1)}s → {detection.end_sec.toFixed(1)}s
              </p>
            </div>
            <div>
              <p className="text-slate-500">Confidence</p>
              <div className="flex items-center gap-2 mt-1">
                <div className="flex-1 h-1.5 bg-ocean-700 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full ${
                      pct >= 90 ? 'bg-emerald-400' : pct >= 70 ? 'bg-amber-400' : 'bg-red-400'
                    }`}
                    style={{ width: `${pct}%` }}
                  />
                </div>
                <span className={`font-bold ${confColor}`}>{pct}%</span>
              </div>
            </div>
            <div>
              <p className="text-slate-500">Coordinates</p>
              <p className="text-slate-300">
                {detection.lat.toFixed(4)}, {detection.lon.toFixed(4)}
              </p>
            </div>
          </div>
        </div>

        {/* Spectrogram image carousel */}
        <div className="flex-1">
          {isLoading && (
            <div className="h-40 bg-ocean-900 rounded-lg animate-pulse flex items-center justify-center text-slate-600">
              <ImageIcon size={24} />
            </div>
          )}

          {spectrograms && spectrograms.length > 0 && (
            <>
              <div className="relative bg-ocean-900 rounded-lg overflow-hidden">
                <img
                  src={spectrograms[imgIdx].url}
                  alt={spectrograms[imgIdx].title}
                  className="w-full h-44 object-cover object-top"
                  onError={(e) => {
                    ;(e.target as HTMLImageElement).style.display = 'none'
                  }}
                />
                <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-ocean-900/90 px-3 py-2">
                  <p className="text-xs text-slate-300 font-medium">{spectrograms[imgIdx].title}</p>
                </div>
              </div>

              {/* Navigation */}
              {spectrograms.length > 1 && (
                <div className="flex items-center justify-between mt-2">
                  <button
                    onClick={() => setImgIdx((i) => Math.max(0, i - 1))}
                    disabled={imgIdx === 0}
                    className="p-1 rounded-lg bg-ocean-700 hover:bg-ocean-600 disabled:opacity-30 text-slate-300 transition-colors"
                  >
                    <ChevronLeft size={14} />
                  </button>
                  <div className="flex gap-1.5">
                    {spectrograms.map((_, i) => (
                      <button
                        key={i}
                        onClick={() => setImgIdx(i)}
                        className={`w-1.5 h-1.5 rounded-full transition-colors ${
                          i === imgIdx ? 'bg-cyan-400' : 'bg-ocean-600 hover:bg-ocean-500'
                        }`}
                      />
                    ))}
                  </div>
                  <button
                    onClick={() => setImgIdx((i) => Math.min(spectrograms.length - 1, i + 1))}
                    disabled={imgIdx === spectrograms.length - 1}
                    className="p-1 rounded-lg bg-ocean-700 hover:bg-ocean-600 disabled:opacity-30 text-slate-300 transition-colors"
                  >
                    <ChevronRight size={14} />
                  </button>
                </div>
              )}
            </>
          )}

          {spectrograms?.length === 0 && !isLoading && (
            <div className="h-40 bg-ocean-900 rounded-lg flex flex-col items-center justify-center text-slate-500 text-xs gap-2">
              <ImageIcon size={24} className="text-slate-600" />
              <p>No spectrograms available</p>
              <p className="text-slate-600">Run the ML pipeline to generate spectrograms</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
