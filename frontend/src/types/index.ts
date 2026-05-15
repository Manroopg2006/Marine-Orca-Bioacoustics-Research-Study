export interface Detection {
  id: number
  start_sec: number
  end_sec: number
  confidence: number
  file: string
  location: string
  lat: number
  lon: number
  date: string
}

export interface DetectionStats {
  total: number
  by_location: Record<string, number>
  avg_confidence: number
  max_confidence: number
  high_confidence_count: number
  date_range: { min: string; max: string }
}

export interface Hydrophone {
  name: string
  lat: number
  lon: number
  color: string
  detection_count: number
  avg_confidence: number
  last_detection_date: string | null
}

export interface SpectrogramInfo {
  filename: string
  url: string
  title: string
}
