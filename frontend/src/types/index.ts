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

export interface AudioDetection {
  id?: number
  start_sec: number
  end_sec: number
  confidence: number
  feedback?: FeedbackChoice | null
}

export type FeedbackChoice = 'confirmed_orca' | 'false_positive' | 'unsure'

export interface AudioClassification {
  analysis_id: number
  file: string
  classification: 'orca' | 'no_orca'
  confidence: number
  duration_seconds: number
  sample_rate: number
  segments_analyzed: number
  total_detections: number
  threshold: number
  model_version: string
  detections: AudioDetection[]
  segment_scores: SegmentScore[]
}

export interface AnalysisSummary {
  id: number
  file: string
  created_at: string
  classification: 'orca' | 'no_orca'
  confidence: number
  duration_seconds: number
  total_detections: number
  threshold: number
  model_version: string
}

export interface SegmentScore {
  start_sec: number
  end_sec: number
  confidence: number
  detected: boolean
}