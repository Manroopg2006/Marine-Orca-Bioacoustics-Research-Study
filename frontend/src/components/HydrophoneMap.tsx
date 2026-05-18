import { useEffect, useMemo, memo } from 'react'
import { MapContainer, TileLayer, CircleMarker, Marker, Popup, useMap } from 'react-leaflet'
import L from 'leaflet'
import { useQuery } from '@tanstack/react-query'
import { fetchHydrophones } from '../api/client'
import type { Detection } from '../types'

// Fix Leaflet default icon paths (broken in bundlers)
delete (L.Icon.Default.prototype as unknown as Record<string, unknown>)._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
})

const LOCATION_COLORS: Record<string, string> = {
  'Dyes Inlet South': '#ef4444',
  'Dyes Inlet North': '#f97316',
  'Orcasound Lab - San Juan Island': '#3b82f6',
}

// Calls invalidateSize once on mount so tiles fill the container correctly
function InvalidateSize() {
  const map = useMap()
  useEffect(() => {
    map.invalidateSize()
  }, [map])
  return null
}

// Isolated child — only flies when selected.id changes, never causes parent rerender
function FlyToSelected({ detection }: { detection: Detection | null }) {
  const map = useMap()
  useEffect(() => {
    if (detection) {
      map.flyTo([detection.lat, detection.lon], 11, { duration: 1.2 })
    }
  }, [detection?.id]) // eslint-disable-line react-hooks/exhaustive-deps
  return null
}

function createHydrophoneIcon(color: string) {
  return L.divIcon({
    className: '',
    html: `<div style="
      width:14px;height:14px;
      background:${color};
      border:2px solid white;
      border-radius:50%;
      box-shadow:0 0 8px ${color};
    "></div>`,
    iconSize: [14, 14],
    iconAnchor: [7, 7],
  })
}

interface Props {
  selected: Detection | null
}

// Memoized markers — only re-render when hydrophone data actually changes
const HydrophoneMarkers = memo(function HydrophoneMarkers({
  hydrophones,
}: {
  hydrophones: ReturnType<typeof fetchHydrophones> extends Promise<infer T> ? T : never
}) {
  return (
    <>
      {hydrophones.map((h) => {
        const color = LOCATION_COLORS[h.name] ?? '#94a3b8'
        return (
          <Marker key={h.name} position={[h.lat, h.lon]} icon={createHydrophoneIcon(color)}>
            <Popup>
              <div className="text-slate-100 text-xs space-y-1 min-w-[160px]">
                <p className="font-bold text-sm" style={{ color }}>
                  {h.name}
                </p>
                <p>
                  <span className="text-slate-400">Detections: </span>
                  <span className="font-semibold">{h.detection_count.toLocaleString()}</span>
                </p>
                <p>
                  <span className="text-slate-400">Avg confidence: </span>
                  <span className="font-semibold">{(h.avg_confidence * 100).toFixed(1)}%</span>
                </p>
                {h.last_detection_date && (
                  <p>
                    <span className="text-slate-400">Last active: </span>
                    <span>{h.last_detection_date}</span>
                  </p>
                )}
                <p className="text-slate-500">
                  {h.lat.toFixed(4)}, {h.lon.toFixed(4)}
                </p>
              </div>
            </Popup>
          </Marker>
        )
      })}
    </>
  )
})

function HydrophoneMap({ selected }: Props) {
  const { data: hydrophones } = useQuery({
    queryKey: ['hydrophones'],
    queryFn: fetchHydrophones,
    staleTime: 300_000,   // hydrophone list rarely changes
    refetchInterval: false,
  })

  const legend = useMemo(
    () => [
      { label: 'Dyes Inlet S', color: '#ef4444' },
      { label: 'Dyes Inlet N', color: '#f97316' },
      { label: 'San Juan', color: '#3b82f6' },
    ],
    []
  )

  return (
    <div className="bg-ocean-800 border border-ocean-700 rounded-xl overflow-hidden flex flex-col h-full">
      {/* Header */}
      <div className="px-4 py-3 border-b border-ocean-700 flex items-center justify-between shrink-0">
        <span className="text-sm font-semibold text-slate-200">Hydrophone Network</span>
        <div className="flex items-center gap-3 text-xs text-slate-500">
          {legend.map((h) => (
            <span key={h.label} className="flex items-center gap-1">
              <span
                className="inline-block w-2.5 h-2.5 rounded-full border border-white/30"
                style={{ background: h.color }}
              />
              {h.label}
            </span>
          ))}
        </div>
      </div>

      {/* Explicit pixel height — Leaflet must know its size at mount time */}
        <div className="flex-1 min-h-0">
          <MapContainer
            center={[48.0, -122.9]}
            zoom={8}
            style={{ height: '100%', width: '100%' }}
            zoomControl
            preferCanvas
        >
          <TileLayer
            url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
            subdomains="abcd"
            maxZoom={19}
          />

          <InvalidateSize />
          <FlyToSelected detection={selected} />

          {hydrophones && <HydrophoneMarkers hydrophones={hydrophones} />}

          {/* Selected detection ring */}
          {selected && (
            <CircleMarker
              center={[selected.lat, selected.lon]}
              radius={18}
              pathOptions={{ color: '#06b6d4', fillColor: '#06b6d4', fillOpacity: 0.12, weight: 1.5 }}
            />
          )}

          {/* Selected detection dot */}
          {selected && (
            <CircleMarker
              center={[selected.lat, selected.lon]}
              radius={5}
              pathOptions={{ color: '#06b6d4', fillColor: '#06b6d4', fillOpacity: 0.9, weight: 2 }}
            >
              <Popup>
                <div className="text-slate-100 text-xs space-y-1">
                  <p className="font-bold text-cyan-300">Selected Detection</p>
                  <p>{selected.location}</p>
                  <p>Confidence: <strong>{(selected.confidence * 100).toFixed(1)}%</strong></p>
                  <p>Time: {selected.start_sec.toFixed(1)}s – {selected.end_sec.toFixed(1)}s</p>
                </div>
              </Popup>
            </CircleMarker>
          )}
        </MapContainer>
      </div>
    </div>
  )
}

export default memo(HydrophoneMap)
