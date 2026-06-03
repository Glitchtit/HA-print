import { useRef } from 'react'

const PRESETS = {
  heading: { type: 'text', w: 528, h: 64, text: 'Heading', fontSize: 44, bold: true, align: 'center' },
  text: { type: 'text', w: 528, h: 48, text: 'Text', fontSize: 28, bold: false, align: 'left' },
  divider: { type: 'divider', w: 528, h: 16, lineStyle: 'solid', thickness: 2 },
  blank: { type: 'divider', w: 528, h: 40, lineStyle: 'blank' },
  qr: { type: 'qr', w: 160, h: 160, data: 'https://example.com', ecc: 'M' },
  barcode: { type: 'barcode', w: 320, h: 100, data: '1234567890', format: 'CODE128', displayValue: true },
}

function Btn({ emoji, label, onClick }) {
  return (
    <button
      onClick={onClick}
      className="flex flex-col items-center gap-1 rounded-xl bg-gray-800 hover:bg-gray-700 px-2 py-3 text-xs text-gray-200"
    >
      <span className="text-xl leading-none">{emoji}</span>
      <span>{label}</span>
    </button>
  )
}

export default function BlockPalette({ onAdd }) {
  const fileRef = useRef(null)

  const onImage = (e) => {
    const f = e.target.files?.[0]
    if (!f) return
    const reader = new FileReader()
    reader.onload = () => {
      const img = new Image()
      img.onload = () => {
        const w = Math.min(528, img.width)
        const h = Math.max(1, Math.round(img.height * (w / img.width)))
        onAdd({ type: 'image', w, h, src: reader.result })
      }
      img.src = reader.result
    }
    reader.readAsDataURL(f)
    e.target.value = ''
  }

  return (
    <div className="grid grid-cols-2 gap-2">
      <Btn emoji="📰" label="Heading" onClick={() => onAdd({ ...PRESETS.heading })} />
      <Btn emoji="📝" label="Text" onClick={() => onAdd({ ...PRESETS.text })} />
      <Btn emoji="🖼" label="Image" onClick={() => fileRef.current?.click()} />
      <Btn emoji="➖" label="Divider" onClick={() => onAdd({ ...PRESETS.divider })} />
      <Btn emoji="␣" label="Blank feed" onClick={() => onAdd({ ...PRESETS.blank })} />
      <Btn emoji="🔳" label="QR code" onClick={() => onAdd({ ...PRESETS.qr })} />
      <Btn emoji="▌▏" label="Barcode" onClick={() => onAdd({ ...PRESETS.barcode })} />
      <input
        ref={fileRef}
        type="file"
        accept="image/png,image/jpeg"
        onChange={onImage}
        className="hidden"
      />
    </div>
  )
}
