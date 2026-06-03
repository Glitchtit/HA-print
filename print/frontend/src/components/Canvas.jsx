import { useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react'
import { Rnd } from 'react-rnd'
import { CANVAS_WIDTH, measureInkBottom, renderToCanvas } from '../lib/render'
import { computeSnap } from '../lib/snap'

/**
 * The design surface. The visible pixels come from a single <canvas> drawn by
 * render.js (identical to what prints); transparent <Rnd> boxes float on top to
 * provide drag/resize/selection. While dragging, the canvas re-renders live
 * with the dragged block at its (snapped) position, and alignment guidelines
 * are drawn over it. The whole thing is CSS-scaled to fit.
 */
export default function Canvas({ elements, selectedId, onSelect, onChange, height }) {
  const canvasRef = useRef(null)
  const wrapRef = useRef(null)
  const [scale, setScale] = useState(1)
  const [drag, setDrag] = useState(null) // { id, x, y } while dragging
  const [guides, setGuides] = useState([])
  const [cutY, setCutY] = useState(0) // measured ink bottom (where the paper cuts)

  // Elements as currently displayed: the dragged block follows its live position.
  const displayElements = useMemo(() => {
    if (!drag) return elements
    return elements.map((e) => (e.id === drag.id ? { ...e, x: drag.x, y: drag.y } : e))
  }, [elements, drag])

  // Single-flight render scheduler — coalesces rapid drag updates (last wins)
  // so async image/QR draws never pile up or land out of order.
  const renderingRef = useRef(false)
  const pendingRef = useRef(null)
  useEffect(() => {
    const run = async (els, h) => {
      if (renderingRef.current) {
        pendingRef.current = [els, h]
        return
      }
      renderingRef.current = true
      try {
        if (canvasRef.current) {
          await renderToCanvas(canvasRef.current, els, h)
          setCutY(measureInkBottom(canvasRef.current, 8))
        }
      } finally {
        renderingRef.current = false
        if (pendingRef.current) {
          const [pe, ph] = pendingRef.current
          pendingRef.current = null
          run(pe, ph)
        }
      }
    }
    run(displayElements, height)
  }, [displayElements, height])

  useLayoutEffect(() => {
    const measure = () => {
      const avail = wrapRef.current?.parentElement?.clientWidth || CANVAS_WIDTH
      setScale(Math.min(1, avail / CANVAS_WIDTH))
    }
    measure()
    window.addEventListener('resize', measure)
    return () => window.removeEventListener('resize', measure)
  }, [])

  // Hold Ctrl (or ⌘) while dragging to bypass snapping for free placement.
  const snapFor = (el, x, y, ev) => {
    if (ev?.ctrlKey || ev?.metaKey) return { x: Math.round(x), y: Math.round(y), guides: [] }
    return computeSnap(el.w, el.h, x, y, elements.filter((o) => o.id !== el.id), CANVAS_WIDTH, height)
  }

  return (
    <div style={{ width: CANVAS_WIDTH * scale, height: height * scale }}>
      <div
        ref={wrapRef}
        className="relative bg-white shadow-xl"
        style={{ width: CANVAS_WIDTH, height, transform: `scale(${scale})`, transformOrigin: 'top left' }}
        onMouseDown={(e) => {
          if (e.target === e.currentTarget || e.target === canvasRef.current) onSelect(null)
        }}
      >
        <canvas
          ref={canvasRef}
          className="absolute inset-0 pointer-events-none"
          style={{ width: CANVAS_WIDTH, height }}
        />

        {cutY > 0 && cutY < height && (
          <div
            className="absolute left-0 right-0 border-t border-dashed border-red-500 pointer-events-none"
            style={{ top: cutY, zIndex: 40 }}
            title="Paper cut — anything below this is trimmed off the print"
          />
        )}

        {/* Alignment guidelines (only while dragging) */}
        {guides.map((g, i) =>
          g.axis === 'v' ? (
            <div
              key={i}
              className="absolute top-0 bottom-0 pointer-events-none"
              style={{ left: g.pos, width: 1, background: '#FF4F00', zIndex: 50 }}
            />
          ) : (
            <div
              key={i}
              className="absolute left-0 right-0 pointer-events-none"
              style={{ top: g.pos, height: 1, background: '#FF4F00', zIndex: 50 }}
            />
          ),
        )}

        {elements.map((el) => (
          <Rnd
            key={el.id}
            scale={scale}
            bounds="parent"
            enableResizing={el.type !== 'drillguide'}
            size={{ width: el.w, height: el.h }}
            position={drag && drag.id === el.id ? { x: drag.x, y: drag.y } : { x: el.x, y: el.y }}
            onDragStart={() => {
              onSelect(el.id)
              setDrag({ id: el.id, x: el.x, y: el.y })
            }}
            onDrag={(e, d) => {
              const s = snapFor(el, d.x, d.y, e)
              setDrag({ id: el.id, x: s.x, y: s.y })
              setGuides(s.guides)
            }}
            onDragStop={(e, d) => {
              const s = snapFor(el, d.x, d.y, e)
              onChange(el.id, { x: s.x, y: s.y })
              setDrag(null)
              setGuides([])
            }}
            onResizeStop={(e, dir, ref, delta, pos) =>
              onChange(el.id, {
                w: Math.round(ref.offsetWidth),
                h: Math.round(ref.offsetHeight),
                x: Math.round(pos.x),
                y: Math.round(pos.y),
              })
            }
            className={
              selectedId === el.id
                ? 'ring-2 ring-[#FF4F00] ring-inset'
                : 'hover:ring-1 hover:ring-[#0047AB] ring-inset'
            }
            style={{ zIndex: selectedId === el.id ? 10 : 1 }}
          >
            <div className="w-full h-full" onMouseDown={() => onSelect(el.id)} />
          </Rnd>
        ))}
      </div>
    </div>
  )
}
