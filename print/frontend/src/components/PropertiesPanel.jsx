const inputCls =
  'rounded-lg bg-gray-800 border border-gray-700 px-2 py-1 text-sm text-gray-100 focus:border-[#0047AB] outline-none'

function Row({ label, children }) {
  return (
    <label className="flex items-center justify-between gap-3 text-sm">
      <span className="text-gray-400">{label}</span>
      {children}
    </label>
  )
}

export default function PropertiesPanel({ element, onChange, onRemove }) {
  if (!element) {
    return <p className="text-sm text-gray-500">Select a block on the canvas to edit it.</p>
  }
  const set = (patch) => onChange(element.id, patch)

  return (
    <div className="space-y-3">
      {element.type === 'text' && (
        <>
          <textarea
            className={`${inputCls} w-full`}
            rows={3}
            value={element.text}
            onChange={(e) => set({ text: e.target.value })}
          />
          <Row label="Size">
            <input
              type="number"
              min={10}
              max={120}
              className={`${inputCls} w-20`}
              value={element.fontSize}
              onChange={(e) => set({ fontSize: Number(e.target.value) })}
            />
          </Row>
          <Row label="Bold">
            <input
              type="checkbox"
              checked={element.bold}
              onChange={(e) => set({ bold: e.target.checked })}
            />
          </Row>
          <Row label="Align">
            <select
              className={inputCls}
              value={element.align}
              onChange={(e) => set({ align: e.target.value })}
            >
              <option value="left">Left</option>
              <option value="center">Center</option>
              <option value="right">Right</option>
            </select>
          </Row>
        </>
      )}

      {element.type === 'divider' && (
        <>
          <Row label="Style">
            <select
              className={inputCls}
              value={element.lineStyle}
              onChange={(e) => set({ lineStyle: e.target.value })}
            >
              <option value="solid">Solid line</option>
              <option value="dashed">Dashed line</option>
              <option value="blank">Blank feed</option>
            </select>
          </Row>
          {element.lineStyle !== 'blank' && (
            <Row label="Thickness">
              <input
                type="number"
                min={1}
                max={12}
                className={`${inputCls} w-20`}
                value={element.thickness}
                onChange={(e) => set({ thickness: Number(e.target.value) })}
              />
            </Row>
          )}
        </>
      )}

      {element.type === 'qr' && (
        <>
          <textarea
            className={`${inputCls} w-full`}
            rows={2}
            value={element.data}
            onChange={(e) => set({ data: e.target.value })}
          />
          <Row label="Error correction">
            <select
              className={inputCls}
              value={element.ecc}
              onChange={(e) => set({ ecc: e.target.value })}
            >
              <option value="L">L (7%)</option>
              <option value="M">M (15%)</option>
              <option value="Q">Q (25%)</option>
              <option value="H">H (30%)</option>
            </select>
          </Row>
        </>
      )}

      {element.type === 'barcode' && (
        <>
          <input
            className={`${inputCls} w-full`}
            value={element.data}
            onChange={(e) => set({ data: e.target.value })}
          />
          <Row label="Symbology">
            <select
              className={inputCls}
              value={element.format}
              onChange={(e) => set({ format: e.target.value })}
            >
              {['CODE128', 'EAN13', 'EAN8', 'UPC', 'CODE39', 'ITF14'].map((f) => (
                <option key={f} value={f}>
                  {f}
                </option>
              ))}
            </select>
          </Row>
          <Row label="Show text">
            <input
              type="checkbox"
              checked={element.displayValue !== false}
              onChange={(e) => set({ displayValue: e.target.checked })}
            />
          </Row>
        </>
      )}

      {element.type === 'image' && (
        <p className="text-xs text-gray-500">Drag the corners to resize. Add a new image to replace this one.</p>
      )}

      <button
        onClick={() => onRemove(element.id)}
        className="w-full rounded-xl bg-red-900/40 text-red-300 hover:bg-red-900/60 px-3 py-2 text-sm"
      >
        🗑 Remove block
      </button>
    </div>
  )
}
