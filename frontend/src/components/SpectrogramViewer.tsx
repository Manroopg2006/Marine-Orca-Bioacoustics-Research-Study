import { useState, useEffect } from 'react'
import { X, ImageIcon } from 'lucide-react'
import { generateSpectrogram } from '../api/client'
import type { Detection } from '../types'

interface Props {
  detection: Detection
  onClose: () => void
}

// Map filenames to their full paths
function resolveFilePath(detection: Detection): string {
  const file = detection.file
  if (file.startsWith('KWSR')) {
    return `C:/Users/xxman/data/raw_audio/onc_digby/${file}`
  }
  if (file.startsWith('OS_9_27')) {
    return `C:/projects/orcapath-ai/data/raw_audio/labeled/orca/${file}`
  }
  return `C:/projects/orcapath-ai/data/raw_audio/labeled/orca/${file}`
}

export default function SpectrogramViewer({ detection, onClose }: Props) {
  const [spectrogramUrl, setSpectrogramUrl] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState(false)

  const pct = Math.round(detection.confidence * 100)
  const confColor = pct >= 90 ? 'text-emerald-400' : pct >= 70 ? 'text-amber-400' : 'text-red-400'

useEffect(() => {
    setIsLoading(true)
    setSpectrogramUrl(null)
    setError(false)

    const filePath = resolveFilePath(detection)

    generateSpectrogram(filePath, detection.start_sec, detection.end_sec)
      .then(url => {
        console.log('Spectrogram URL:', url)
        setSpectrogramUrl(url)
        setIsLoading(false)
      })
      .catch((err) => {
        console.error('Spectrogram error:', err)
        setError(true)
        setIsLoading(false)
      })
  }, [detection]) 
  

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
        <div className="w-48 shrink-0 text-xs">
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

        {/* Spectrogram */}
        <div className="flex-1">
          {isLoading && (
            <div className="h-44 bg-ocean-900 rounded-lg animate-pulse flex items-center justify-center text-slate-600">
              <ImageIcon size={24} />
            </div>
          )}

          {spectrogramUrl && !isLoading && (
            <div className="relative bg-ocean-900 rounded-lg overflow-hidden">
              <img
                src={spectrogramUrl}
                alt="Detection spectrogram"
                className="w-full h-44 object-cover object-top"
              />
              <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-ocean-900/90 px-3 py-2">
                <p className="text-xs text-slate-300 font-medium">
                  Mel Spectrogram · {detection.start_sec.toFixed(1)}s–{detection.end_sec.toFixed(1)}s
                </p>
              </div>
            </div>
          )}

          {error && !isLoading && (
            <div className="h-44 bg-ocean-900 rounded-lg flex flex-col items-center justify-center text-slate-500 text-xs gap-2">
              <ImageIcon size={24} className="text-slate-600" />
              <p>Could not generate spectrogram</p>
              <p className="text-slate-600">{detection.file}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}


