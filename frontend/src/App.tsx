import { ChangeEvent, FormEvent, useEffect, useRef, useState } from 'react'
import { CheckCircle2, FileAudio, LoaderCircle, SlidersHorizontal, Upload, Waves, XCircle } from 'lucide-react'
import { saveDetectionFeedback, uploadAudio } from './api/client'
import type { AudioClassification, FeedbackChoice } from './types'


const MAX_FILE_SIZE = 50 * 1024 * 1024
const feedbackOptions: ReadonlyArray<readonly [FeedbackChoice, string]> = [
  ['confirmed_orca', 'Confirmed orca'],
  ['false_positive', 'False positive'],
  ['unsure', 'Unsure'],
]
const HERO_CLIPS = [
  { src: '/media/orca-hero.mp4', startAt: 0, position: 'object-left' },
  { src: '/media/underwater-b-roll.mp4', startAt: 3, position: 'object-center' },
  { src: '/media/ocean-waves.mp4', startAt: 5, position: 'object-right' },
]

function formatDuration(seconds: number) {
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = Math.round(seconds % 60)
  return minutes > 0 ? `${minutes}m ${remainingSeconds}s` : `${remainingSeconds}s`
}

function HeroClip({ src, startAt, className }: { src: string; startAt: number; className?: string }) {
  return <video
    aria-hidden="true"
    className={`hero-clip ${className ?? ''}`}
    autoPlay
    muted
    loop
    playsInline
    onLoadedMetadata={(event) => { event.currentTarget.currentTime = startAt }}
  >
    <source src={src} type="video/mp4" />
  </video>
}

export default function App() {
  const uploadRef = useRef<HTMLInputElement>(null)
  const [file, setFile] = useState<File | null>(null)
  const [result, setResult] = useState<AudioClassification | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [feedbackError, setFeedbackError] = useState<string | null>(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [threshold, setThreshold] = useState(0.4)
  const audioRef = useRef<HTMLAudioElement>(null)
  const [audioUrl, setAudioUrl] = useState<string | null>(null)
  const [selectedSecond, setSelectedSecond] = useState(0)

  useEffect(() => () => {
    if (audioUrl) URL.revokeObjectURL(audioUrl)
  }, [audioUrl])

  const selectFile = (selectedFile: File | undefined) => {
    setResult(null)
    setError(null)
    if (!selectedFile) return
    if (!selectedFile.name.toLowerCase().endsWith('.wav')) {
      setFile(null); setError('Please choose a WAV audio file.'); return
    }
    if (selectedFile.size > MAX_FILE_SIZE) {
      setFile(null); setError('Please choose a WAV file smaller than 50 MB.'); return
    }
    setFile(selectedFile)
    setAudioUrl(URL.createObjectURL(selectedFile))
    setSelectedSecond(0)
  }

  const seekToSecond = (second: number) => {
    setSelectedSecond(second)

    if (audioRef.current) {
      audioRef.current.currentTime = second
    }
  }

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    if (!file) { setError('Choose a WAV audio file first.'); return }
    setIsAnalyzing(true); setError(null); setResult(null)
    try {
      setResult(await uploadAudio(file, threshold))
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Unable to analyze this file.')
    } finally { setIsAnalyzing(false) }
  }

  const saveFeedback = async (detectionId: number | undefined, feedback: FeedbackChoice) => {
    if (!detectionId) return
    setFeedbackError(null)
    try {
      await saveDetectionFeedback(detectionId, feedback)
      setResult(current => current ? {
        ...current,
        detections: current.detections.map(item => item.id === detectionId ? { ...item, feedback } : item),
      } : current)
    } catch { setFeedbackError('Could not save your feedback. Please try again.') }
  }

  const scrollToUpload = () => document.getElementById('upload')?.scrollIntoView({ behavior: 'smooth' })
  const detectedOrca = result?.classification === 'orca'

const selectedSegment = result?.segment_scores.find(
  (segment) => Math.floor(segment.start_sec) === selectedSecond
)

  return <main className="min-h-screen bg-slate-950 text-slate-100">
    <section className="hero relative isolate flex min-h-screen items-center overflow-hidden px-6 py-20">
      <div className="hero-montage absolute inset-0 grid grid-cols-3 gap-1" aria-hidden="true">
        {HERO_CLIPS.map((clip) => <div key={clip.src}><HeroClip {...clip} className={clip.position} /></div>)}
      </div>
      <div className="absolute inset-0 bg-slate-950/60" />
      <div className="absolute inset-0 bg-gradient-to-b from-slate-950/25 via-slate-950/15 to-slate-950" />
      <div className="relative mx-auto w-full max-w-5xl text-center">
        <div className="mb-7 inline-flex items-center gap-2 rounded-full border border-cyan-300/30 bg-slate-950/40 px-4 py-2 text-sm text-cyan-100 backdrop-blur"><Waves size={16} />Acoustic wildlife classifier</div>
        <h1 className="text-5xl font-semibold tracking-tight text-white sm:text-7xl">OrcaCall Detector</h1>
        <p className="mx-auto mt-6 max-w-2xl text-lg leading-8 text-slate-200 sm:text-xl">Upload an underwater WAV recording and check it for possible orca vocalizations.</p>
        <button onClick={scrollToUpload} className="mt-10 rounded-full bg-cyan-400 px-7 py-3.5 font-semibold text-slate-950 transition hover:bg-cyan-300 focus:outline-none focus:ring-4 focus:ring-cyan-200/40">Start detecting</button>
      </div>
    </section>

    <section className="border-y border-slate-800 bg-slate-900/55 px-6 py-16">
      <div className="mx-auto grid max-w-5xl gap-8 md:grid-cols-[1.1fr_.9fr] md:items-center">
        <div><p className="text-sm font-semibold uppercase tracking-[0.2em] text-cyan-300">About this project</p><h2 className="mt-3 text-3xl font-semibold tracking-tight text-white">A practical tool for reviewing underwater audio.</h2></div>
        <p className="leading-7 text-slate-300">OrcaCall Detector breaks recordings into one second sections and highlights sections that may contain orca vocalizations. It is designed to help prioritize human review, not to scientifically confirm species presence. Your feedback is saved for future model improvements.</p>
      </div>
    </section>

    <section id="upload" className="scroll-mt-8 bg-slate-950 px-6 py-20 sm:py-28"><div className="mx-auto max-w-3xl">
      <p className="text-center text-sm font-semibold uppercase tracking-[0.2em] text-cyan-300">Analyze a recording</p><h2 className="mt-3 text-center text-3xl font-semibold tracking-tight text-white sm:text-4xl">Upload a WAV file</h2>
      <p className="mx-auto mt-4 max-w-xl text-center leading-7 text-slate-400">We analyze one second sections of your audio and return a simple result with the strongest model confidence.</p>
      <form onSubmit={handleSubmit} className="mt-10 rounded-3xl border border-slate-700 bg-slate-900 p-5 shadow-2xl shadow-cyan-950/20 sm:p-8">
        <button type="button" onClick={() => uploadRef.current?.click()} className="flex w-full flex-col items-center rounded-2xl border border-dashed border-cyan-400/50 bg-cyan-950/20 px-6 py-12 text-center transition hover:border-cyan-300 hover:bg-cyan-950/35"><Upload size={30} className="text-cyan-300" /><span className="mt-4 font-semibold text-white">Choose a WAV file</span><span className="mt-2 text-sm text-slate-400">Maximum: 50 MB and 10 minutes</span></button>
        <input ref={uploadRef} aria-label="Choose WAV file" onChange={(event: ChangeEvent<HTMLInputElement>) => selectFile(event.target.files?.[0])} accept="audio/wav,.wav" type="file" className="hidden" />
        {file && <div className="mt-4 flex items-center gap-3 rounded-xl bg-slate-800 px-4 py-3 text-sm"><FileAudio className="shrink-0 text-cyan-300" size={20} /><span className="min-w-0 flex-1 truncate text-slate-200">{file.name}</span><span className="text-slate-400">{(file.size / (1024 * 1024)).toFixed(1)} MB</span></div>}
        <div className="mt-5 rounded-xl border border-slate-700 bg-slate-950/40 p-4"><div className="flex items-center justify-between text-sm"><label htmlFor="threshold" className="flex items-center gap-2 font-medium text-slate-200"><SlidersHorizontal size={16} className="text-cyan-300" />Detection threshold</label><span className="font-semibold text-cyan-300">{Math.round(threshold * 100)}%</span></div><input id="threshold" aria-label="Detection threshold" type="range" min="0.05" max="0.95" step="0.05" value={threshold} onChange={(event) => setThreshold(Number(event.target.value))} className="mt-4 w-full accent-cyan-400" /><p className="mt-2 text-xs text-slate-400">Higher thresholds show fewer, more confident possible calls.</p></div>
        {error && <p role="alert" className="mt-4 rounded-xl bg-red-950/50 px-4 py-3 text-sm text-red-200">{error}</p>}
        <p className="mt-4 text-center text-xs text-slate-400">Analysis may take up to a minute for longer recordings.</p>
        <button disabled={!file || isAnalyzing} className="mt-3 flex w-full items-center justify-center gap-2 rounded-xl bg-cyan-400 px-5 py-3.5 font-semibold text-slate-950 transition hover:bg-cyan-300 disabled:cursor-not-allowed disabled:opacity-50">{isAnalyzing ? <LoaderCircle className="animate-spin" size={19} /> : <Waves size={19} />}{isAnalyzing ? 'Analyzing audio...' : 'Analyze audio'}</button>
      </form>
      {result && (<>
{audioUrl && (
  <section className="mt-6 border-t border-emerald-200/10 pt-5">
    <p className="text-sm font-semibold text-slate-200">
      Explore the recording
    </p>

    <audio
      ref={audioRef}
      src={audioUrl}
      controls
      className="mt-3 w-full"
      onTimeUpdate={(event) => {
        setSelectedSecond(Math.floor(event.currentTarget.currentTime))
      }}
    />

    <input
      aria-label="Recording position"
      type="range"
      min="0"
      max={Math.max(0, Math.ceil(result.duration_seconds) - 1)}
      step="1"
      value={selectedSecond}
      onChange={(event) => seekToSecond(Number(event.target.value))}
      className="mt-5 w-full accent-cyan-400"
    />
  </section>
)}

{selectedSegment && (
  <div className="mt-4 rounded-xl bg-slate-950/60 p-4">
    <p className="text-sm text-slate-400">
      Selected time: {formatDuration(selectedSegment.start_sec)}
    </p>

    <p className="mt-1 text-lg font-semibold text-white">
      {Math.round(selectedSegment.confidence * 100)}% confidence
    </p>

    <p className={selectedSegment.detected ? 'text-emerald-300' : 'text-slate-400'}>
      {selectedSegment.detected
        ? 'Possible orca call at this threshold'
        : 'Below the selected detection threshold'}
    </p>
  </div>
)}
<div className="mt-5 overflow-x-auto pb-2">
  <div
    className="flex h-12 min-w-[480px] items-end gap-px"
    aria-label="Confidence timeline"
  >
    {result.segment_scores.map((segment) => (
      <button
        key={segment.start_sec}
        type="button"
        title={`${formatDuration(segment.start_sec)}: ${Math.round(segment.confidence * 100)}%`}
        onClick={() => seekToSecond(Math.floor(segment.start_sec))}
        style={{
          height: `${Math.max(12, segment.confidence * 100)}%`,
        }}
        className={`min-w-[4px] flex-1 rounded-t transition ${
          Math.floor(segment.start_sec) === selectedSecond
            ? 'bg-white'
            : segment.detected
              ? 'bg-emerald-400'
              : 'bg-cyan-800'
        }`}
      />
    ))}
  </div>

  <div className="mt-2 flex justify-between text-xs text-slate-500">
    <span>0s</span>
    <span>{formatDuration(result.duration_seconds)}</span>
  </div>
</div>

<article className={`mt-8 rounded-3xl border p-6 sm:p-8 ${detectedOrca ? 'border-emerald-400/40 bg-emerald-950/20' : 'border-slate-700 bg-slate-900'}`}><div className="flex items-start gap-4">{detectedOrca ? <CheckCircle2 className="mt-1 shrink-0 text-emerald-300" size={30} /> : <XCircle className="mt-1 shrink-0 text-slate-400" size={30} />}<div><p className="text-sm font-semibold uppercase tracking-[0.16em] text-slate-400">Classification result</p><h3 className="mt-2 text-2xl font-semibold text-white">{detectedOrca ? 'Possible orca calls detected' : 'No orca calls detected'}</h3><p className="mt-2 text-slate-300">Highest model confidence: <strong className="text-white">{Math.round(result.confidence * 100)}%</strong></p></div></div>
        <dl className="mt-7 grid grid-cols-2 gap-3 sm:grid-cols-4"><div className="rounded-xl bg-slate-950/50 p-3"><dt className="text-xs text-slate-400">Duration</dt><dd className="mt-1 font-semibold">{formatDuration(result.duration_seconds)}</dd></div><div className="rounded-xl bg-slate-950/50 p-3"><dt className="text-xs text-slate-400">Sample rate</dt><dd className="mt-1 font-semibold">{(result.sample_rate / 1000).toFixed(1)} kHz</dd></div><div className="rounded-xl bg-slate-950/50 p-3"><dt className="text-xs text-slate-400">Segments</dt><dd className="mt-1 font-semibold">{result.segments_analyzed}</dd></div><div className="rounded-xl bg-slate-950/50 p-3"><dt className="text-xs text-slate-400">Possible calls</dt><dd className="mt-1 font-semibold">{result.total_detections}</dd></div></dl>
        <p className="mt-4 text-xs text-slate-400">Model: {result.model_version} · Detection threshold: {Math.round(result.threshold * 100)}%</p>
        {detectedOrca && <div className="mt-6 border-t border-emerald-200/10 pt-5"><p className="text-sm font-semibold text-slate-200">Detected sections</p><p className="mt-1 text-xs text-slate-400">Anonymous review feedback helps improve future model evaluations.</p>{feedbackError && <p className="mt-2 text-sm text-red-200">{feedbackError}</p>}<ul className="mt-3 space-y-2">{result.detections.map(detection => <li key={`${detection.start_sec}-${detection.end_sec}`} className="rounded-lg bg-slate-950/45 px-3 py-2 text-sm text-slate-300"><div className="flex justify-between"><span>{formatDuration(detection.start_sec)}–{formatDuration(detection.end_sec)}</span><span>{Math.round(detection.confidence * 100)}% confidence</span></div><div className="mt-2 flex flex-wrap gap-2 text-xs">{feedbackOptions.map(([value, label]) => <button key={value} onClick={() => saveFeedback(detection.id, value)} className={`rounded-full px-2 py-1 ${detection.feedback === value ? 'bg-cyan-400 text-slate-950' : 'bg-slate-800 text-slate-300 hover:bg-slate-700'}`}>{label}</button>)}</div></li>)}</ul></div>}
      </article></>)}
      <p className="mt-8 text-center text-xs leading-5 text-slate-500">This is a machine learning prediction and not a scientific confirmation of species presence.</p>
    </div></section>
    <footer className="border-t border-slate-800 px-6 py-5 text-center text-xs text-slate-500">Orca footage: <a className="underline hover:text-slate-300" href="https://www.pexels.com/download/video/5607993/" target="_blank" rel="noreferrer">Pexels video 5607993</a> · OrcaPath AI</footer>
  </main>
}
