import { useEffect, useState } from 'react'
import { deleteTemplate, getTemplate, listTemplates, saveTemplate } from '../api'

export default function TemplateManager({ elements, onLoad }) {
  const [items, setItems] = useState([])
  const [name, setName] = useState('')
  const [err, setErr] = useState(null)

  const refresh = () =>
    listTemplates()
      .then((d) => setItems(d.templates || []))
      .catch(() => setErr('Could not load templates.'))

  useEffect(() => {
    refresh()
  }, [])

  const save = async () => {
    if (!name.trim()) return
    setErr(null)
    try {
      await saveTemplate({ name: name.trim(), elements })
      setName('')
      refresh()
    } catch {
      setErr('Save failed.')
    }
  }

  const load = async (id) => {
    try {
      const t = await getTemplate(id)
      onLoad(t.elements || [])
    } catch {
      setErr('Load failed.')
    }
  }

  const del = async (id) => {
    try {
      await deleteTemplate(id)
      refresh()
    } catch {
      setErr('Delete failed.')
    }
  }

  return (
    <div className="space-y-2">
      <div className="space-y-2">
        <input
          className="w-full rounded-lg bg-gray-800 border border-gray-700 px-2 py-1 text-sm text-gray-100 focus:border-[#0047AB] outline-none"
          placeholder="Template name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && save()}
        />
        <button
          onClick={save}
          className="w-full rounded-xl bg-[#0047AB] hover:bg-[#0a57c4] px-3 py-1.5 text-sm text-white"
        >
          Save
        </button>
      </div>

      {err && <p className="text-xs text-red-400">{err}</p>}

      <ul className="space-y-1 max-h-48 overflow-auto">
        {items.length === 0 && <li className="text-xs text-gray-500">No saved templates yet.</li>}
        {items.map((t) => (
          <li key={t.id} className="flex items-center gap-2 rounded-lg bg-gray-800 px-2 py-1 text-sm">
            <button onClick={() => load(t.id)} className="flex-1 text-left hover:text-[#FF4F00] truncate">
              {t.name || '(unnamed)'}
            </button>
            <button onClick={() => del(t.id)} className="text-gray-500 hover:text-red-400" title="Delete">
              ✕
            </button>
          </li>
        ))}
      </ul>
    </div>
  )
}
