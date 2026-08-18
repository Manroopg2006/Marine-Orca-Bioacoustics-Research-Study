import axios from 'axios'
import type { AnalysisSummary, AudioClassification, Detection, DetectionStats, FeedbackChoice, Hydrophone, SpectrogramInfo } from '../types'

const api = axios.create({ baseURL: import.meta.env.VITE_API_BASE_URL ?? '/api' })

export async function uploadAudio(
  file: File,
  threshold: number
): Promise<AudioClassification> {  const formData = new FormData()
  formData.append('file', file)
  formData.append('threshold', threshold.toString())
  try {
    const { data } = await api.post<AudioClassification>('/audio/detect', formData)
    return data
  } catch (error) {
    if (axios.isAxiosError(error)) {
      throw new Error(error.response?.data?.detail ?? 'Unable to analyze this file.')
    }
    throw error
  }
}

export async function fetchAnalyses(): Promise<AnalysisSummary[]> {
  const { data } = await api.get<AnalysisSummary[]>('/analyses')
  return data
}

export async function saveDetectionFeedback(detectionId: number, feedback: FeedbackChoice) {
  const { data } = await api.post(`/analyses/detections/${detectionId}/feedback`, { feedback })
  return data
}

export async function fetchDetections(params?: {
  location?: string
  min_confidence?: number
  limit?: number
  offset?: number
}): Promise<Detection[]> {
  const { data } = await api.get<Detection[]>('/detections', { params })
  return data
}

export async function fetchStats(): Promise<DetectionStats> {
  const { data } = await api.get<DetectionStats>('/detections/stats')
  return data
}

export async function fetchHydrophones(): Promise<Hydrophone[]> {
  const { data } = await api.get<Hydrophone[]>('/hydrophones')
  return data
}

export async function fetchSpectrograms(): Promise<SpectrogramInfo[]> {
  const { data } = await api.get<SpectrogramInfo[]>('/spectrograms')
  return data
}

export async function fetchHealth(): Promise<{ status: string }> {
  const { data } = await api.get('/health')
  return data
}




export async function generateSpectrogram(
  filePath: string,
  startSec: number,
  endSec: number
): Promise<string> {
  const params = new URLSearchParams({
    file_path: filePath,
    start_sec: startSec.toString(),
    end_sec: endSec.toString(),
  })
  const response = await api.get(`/spectrograms/generate?${params}`, {
    responseType: 'blob',
  })
  return URL.createObjectURL(response.data)
}

export async function fetchInsights(): Promise<{ summary: string; stats: any }> {
  const { data } = await api.get('/insights')
  return data
}
