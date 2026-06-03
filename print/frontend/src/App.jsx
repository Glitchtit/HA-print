import { useEffect, useState } from 'react'
import BlockPalette from './components/BlockPalette'
import Canvas from './components/Canvas'
import HealthBadge from './components/HealthBadge'
import PropertiesPanel from './components/PropertiesPanel'
import SvgUpload from './components/SvgUpload'
import TemplateManager from './components/TemplateManager'
import { exportPng } from './lib/render'
import { printImage } from './api'

let seq = 1
const uid = () => `el${seq++}_${Math.round(performance.now())}`

export default function App() {
  const [tab, setTab] = useState('designer')
  const [elements, setElements] = useState([])
  const [selectedId, setSelectedId] = useState(null)
  const [height, setHeight] = useState(700)
  const [photoMode, setPhotoMode] = useState(false)
  const [busy, setBusy] = useState(false)
  const [msg, setMsg] = useState(null)

  const selected = elements.find((e) => e.id === selectedId) || null

  const addElement = (partial) => {
    const id = uid()
    setElements((prev) => [...prev, { id, x: 24, y: 24, ...partial }])
    setSelectedId(id)
  }
  const updateElement = (id, patch) =>
    setElements((prev) => prev.map((e) => (e.id === id ? { ...e, ...patch } : e)))
  const removeElement = (id) => {
    setElements((prev) => prev.filter((e) => e.id !== id))
    setSelectedId(null)
  }
  const loadTemplate = (els) => {
    // Re-key on load so ids never collide with the in-memory counter.
    setElements((els || []).map((e) => ({ ...e, id: uid() })))
    setSelectedId(null)
  }

  // Delete / Backspace removes the selected block — unless you're typing in a
  // field (editing text content, a template name, etc.).
  useEffect(() => {
    const onKey = (e) => {
      if (e.key !== 'Delete' && e.key !== 'Backspace') return
      const t = e.target
      const tag = t?.tagName
      if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT' || t?.isContentEditable) return
      if (tab !== 'designer' || !selectedId) return
      e.preventDefault()
      removeElement(selectedId)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [tab, selectedId])

  const handlePrint = async () => {
    setBusy(true)
    setMsg(null)
    try {
      const dataUrl = await exportPng(elements)
      const res = await printImage({ image_b64: dataUrl, dither: photoMode })
      setMsg({ ok: true, text: `Sent to printer (${res.width_px}×${res.height_px}px).` })
    } catch (e) {
      setMsg({ ok: false, text: e?.response?.data?.detail || e.message || 'Print failed.' })
    } finally {
      setBusy(false)
    }
  }

  const tabBtn = (id, label) =>
    `px-3 py-1.5 rounded-xl text-sm ${tab === id ? 'bg-[#FF4F00] text-white' : 'bg-gray-800 text-gray-300 hover:bg-gray-700'}`

  return (
    <div className="min-h-full">
      <header className="sticky top-0 z-20 bg-gray-900/90 backdrop-blur-md border-b border-gray-800 px-4 py-3 flex items-center gap-3 flex-wrap">
        <h1 className="text-lg font-semibold">🖨 Print designer</h1>
        <div className="flex gap-2">
          <button className={tabBtn('designer', 'Designer')} onClick={() => setTab('designer')}>
            Designer
          </button>
          <button className={tabBtn('svg', 'SVG upload')} onClick={() => setTab('svg')}>
            SVG upload
          </button>
        </div>
        <div className="ml-auto">
          <HealthBadge />
        </div>
      </header>

      {tab === 'designer' ? (
        <div className="flex flex-col lg:flex-row gap-4 p-4">
          {/* Left: palette + properties + templates */}
          <aside className="w-full lg:w-72 shrink-0 space-y-4">
            <section className="rounded-xl bg-gray-900 border border-gray-800 p-3">
              <h2 className="text-sm font-medium text-gray-300 mb-2">Add block</h2>
              <BlockPalette onAdd={addElement} />
            </section>

            <section className="rounded-xl bg-gray-900 border border-gray-800 p-3">
              <h2 className="text-sm font-medium text-gray-300 mb-2">Properties</h2>
              <PropertiesPanel element={selected} onChange={updateElement} onRemove={removeElement} />
            </section>

            <section className="rounded-xl bg-gray-900 border border-gray-800 p-3">
              <h2 className="text-sm font-medium text-gray-300 mb-2">Templates</h2>
              <TemplateManager elements={elements} onLoad={loadTemplate} />
            </section>
          </aside>

          {/* Center: canvas */}
          <main className="flex-1 min-w-0">
            <div className="flex items-center gap-3 mb-3 flex-wrap">
              <button
                onClick={handlePrint}
                disabled={busy || elements.length === 0}
                className="rounded-xl bg-[#FF4F00] hover:bg-[#ff6a2b] disabled:opacity-40 px-4 py-2 text-white font-medium"
              >
                🖨 {busy ? 'Printing…' : 'Print'}
              </button>
              <label className="flex items-center gap-2 text-sm text-gray-300">
                <input type="checkbox" checked={photoMode} onChange={(e) => setPhotoMode(e.target.checked)} />
                Photo mode (dither)
              </label>
              <div className="flex items-center gap-1 text-sm text-gray-400">
                <span>Length</span>
                <button
                  onClick={() => setHeight((h) => Math.max(200, h - 100))}
                  className="rounded-lg bg-gray-800 hover:bg-gray-700 w-7 h-7"
                >
                  −
                </button>
                <button
                  onClick={() => setHeight((h) => h + 100)}
                  className="rounded-lg bg-gray-800 hover:bg-gray-700 w-7 h-7"
                >
                  +
                </button>
              </div>
              {msg && (
                <span className={`text-sm ${msg.ok ? 'text-emerald-400' : 'text-red-400'}`}>{msg.text}</span>
              )}
            </div>

            <div className="overflow-auto">
              <Canvas
                elements={elements}
                selectedId={selectedId}
                onSelect={setSelectedId}
                onChange={updateElement}
                height={height}
              />
            </div>
            <p className="mt-2 text-xs text-gray-500">
              80mm receipt · 576px wide.
              <br />
              Drag blocks to position, drag corners to resize.
              <br />
              Blocks snap to the center and to each other — hold Ctrl to place freely.
              <br />
              Select a block and press Delete to remove it.
              <br />
              The red dashed line marks the end of the print.
            </p>
          </main>
        </div>
      ) : (
        <div className="p-4">
          <SvgUpload />
        </div>
      )}
    </div>
  )
}
