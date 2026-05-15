import axios from 'axios'
import type { Detection, DetectionStats, Hydrophone, SpectrogramInfo } from '../types'

const api = axios.create({ baseURL: '/api' })

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
