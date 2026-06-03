import { useState } from 'react'
import { printSvg } from '../api'

function fileToB64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(String(reader.result).split(',')[1] || '')
    reader.onerror = reject
    reader.readAsDataURL(file)
  })
}

export default function SvgUpload() {
  const [file, setFile] = useState(null)
  const [dither, setDither] = useState(false)
  const [busy, setBusy] = useState(false)
  const [msg, setMsg] = useState(null)

  const onPrint = async () => {
    if (!file) return
    setBusy(true)
    setMsg(null)
    try {
      const b64 = await fileToB64(file)
      const res = await printSvg({ svg_b64: b64, dither })
      setMsg({ ok: true, text: `Sent to printer (${res.width_px}×${res.height_px}px).` })
    } catch (e) {
      setMsg({ ok: false, text: e?.response?.data?.detail || e.message || 'Print failed.' })
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="max-w-xl mx-auto space-y-4">
      <div className="rounded-xl bg-gray-800 p-4 space-y-3">
        <input
          type="file"
          accept=".svg,image/svg+xml"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
          className="block w-full text-sm text-gray-300 file:mr-3 file:rounded-lg file:border-0 file:bg-[#0047AB] file:px-3 file:py-2 file:text-white"
        />
        {file && <p className="text-sm text-gray-400">Selected: {file.name}</p>}

        <label className="flex items-center gap-2 text-sm text-gray-300">
          <input type="checkbox" checked={dither} onChange={(e) => setDither(e.target.checked)} />
          Dither (only for photo-like SVGs — leave off for line art)
        </label>

        <button
          onClick={onPrint}
          disabled={!file || busy}
          className="w-full rounded-xl bg-[#FF4F00] hover:bg-[#ff6a2b] disabled:opacity-40 px-3 py-2 text-white font-medium"
        >
          🖨 {busy ? 'Printing…' : 'Print SVG'}
        </button>

        {msg && (
          <p className={`text-sm ${msg.ok ? 'text-emerald-400' : 'text-red-400'}`}>{msg.text}</p>
        )}
      </div>

      <div className="rounded-xl bg-gray-800/60 p-4 text-sm text-gray-400 space-y-1">
        <p className="text-gray-300 font-medium">Sizing notes</p>
        <ul className="list-disc list-inside space-y-1">
          <li>Canvas width: <strong>576px</strong> (72mm @ 203dpi). Width is scaled to fit.</li>
          <li>Any height — the receipt prints top to bottom.</li>
          <li>Design in <strong>pure black on white</strong>.</li>
          <li>Thin strokes and gradients dither poorly on a 1-bit thermal head.</li>
          <li>Convert text to paths so fonts render identically.</li>
          <li>Scripts, external/remote references, and DTD entities are rejected.</li>
        </ul>
      </div>
    </div>
  )
}
