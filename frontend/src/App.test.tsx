import { cleanup, fireEvent, render, screen, within } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

const apiMocks = vi.hoisted(() => ({
  saveDetectionFeedback: vi.fn(),
  uploadAudio: vi.fn(),
}))

vi.mock('./api/client', () => apiMocks)

import App from './App'

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

const timelineResult = {
  analysis_id: 1,
  file: 'fixture.wav',
  classification: 'orca' as const,
  confidence: 0.83,
  duration_seconds: 2,
  sample_rate: 44_100,
  segments_analyzed: 2,
  total_detections: 1,
  threshold: 0.4,
  model_version: 'test-model',
  detections: [{ id: 1, start_sec: 1, end_sec: 2, confidence: 0.83 }],
  segment_scores: [
    { start_sec: 0, end_sec: 1, confidence: 0.2, detected: false },
    { start_sec: 1, end_sec: 2, confidence: 0.83, detected: true },
  ],
}

describe('Orca Detector', () => {
  it('shows the upload entry point', () => {
    render(<App />)
    expect(screen.getByRole('heading', { name: 'OrcaCall Detector' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Choose a WAV file/ })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Analyze audio' })).toBeDisabled()
  })

  it('updates the selected confidence when a timeline bar is clicked', async () => {
    vi.stubGlobal('URL', { createObjectURL: vi.fn(() => 'blob:fixture'), revokeObjectURL: vi.fn() })
    apiMocks.uploadAudio.mockResolvedValueOnce(timelineResult)
    render(<App />)

    const file = new File(['audio'], 'fixture.wav', { type: 'audio/wav' })
    fireEvent.change(screen.getByLabelText('Choose WAV file'), { target: { files: [file] } })
    fireEvent.click(screen.getByRole('button', { name: 'Analyze audio' }))

    expect(await screen.findByText('20% confidence')).toBeInTheDocument()
    fireEvent.click(screen.getByTitle('1s: 83%'))
    const selectedPanel = screen.getByText('Selected time: 1s').parentElement
    expect(selectedPanel).not.toBeNull()
    expect(within(selectedPanel!).getByText('83% confidence')).toBeInTheDocument()
  })
})
