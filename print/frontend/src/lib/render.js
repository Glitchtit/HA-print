/**
 * The WYSIWYG core. Renders the element model onto a 576px-wide canvas — both
 * the live on-screen preview and the bitmap POSTed to the printer come from
 * this exact code, so there is no preview-vs-print drift.
 */
import QRCode from 'qrcode'
import JsBarcode from 'jsbarcode'

// Font A full printable width on the XP-80T (576 dots / 72mm @ 203dpi).
export const CANVAS_WIDTH = 576
const FONT_FAMILY = "system-ui, -apple-system, 'Segoe UI', Roboto, 'DejaVu Sans', sans-serif"

function wrapLine(ctx, text, maxWidth) {
  const words = String(text ?? '').split(/\s+/).filter(Boolean)
  if (!words.length) return ['']
  const lines = []
  let line = ''
  for (const w of words) {
    const test = line ? `${line} ${w}` : w
    if (line && ctx.measureText(test).width > maxWidth) {
      lines.push(line)
      line = w
    } else {
      line = test
    }
  }
  if (line) lines.push(line)
  return lines
}

// Cache decoded images by source so live drag redraws don't re-decode each frame.
const imageCache = new Map()

function loadImage(src) {
  const hit = imageCache.get(src)
  if (hit) return hit
  const p = new Promise((resolve, reject) => {
    const img = new Image()
    img.onload = () => resolve(img)
    img.onerror = reject
    img.src = src
  })
  imageCache.set(src, p)
  return p
}

async function drawElement(ctx, el) {
  if (el.type === 'text') {
    const size = el.fontSize || 28
    ctx.fillStyle = '#000'
    ctx.textBaseline = 'top'
    ctx.font = `${el.bold ? 'bold ' : ''}${size}px ${FONT_FAMILY}`
    const lineH = Math.round(size * 1.25)
    const lines = String(el.text || '').split('\n').flatMap((l) => wrapLine(ctx, l, el.w))
    let y = el.y
    for (const line of lines) {
      const tw = ctx.measureText(line).width
      let x = el.x
      if (el.align === 'center') x = el.x + (el.w - tw) / 2
      else if (el.align === 'right') x = el.x + (el.w - tw)
      ctx.fillText(line, x, y)
      y += lineH
    }
  } else if (el.type === 'image' && el.src) {
    const img = await loadImage(el.src)
    ctx.drawImage(img, el.x, el.y, el.w, el.h)
  } else if (el.type === 'divider') {
    if (el.lineStyle === 'blank') return
    ctx.strokeStyle = '#000'
    ctx.lineWidth = el.thickness || 2
    ctx.setLineDash(el.lineStyle === 'dashed' ? [8, 6] : [])
    const yMid = Math.round(el.y + el.h / 2) + 0.5
    ctx.beginPath()
    ctx.moveTo(el.x, yMid)
    ctx.lineTo(el.x + el.w, yMid)
    ctx.stroke()
    ctx.setLineDash([])
  } else if (el.type === 'qr' && el.data) {
    // Render at the target size (no scaling) so finder patterns stay crisp.
    const s = Math.max(40, Math.min(el.w, el.h))
    const tmp = document.createElement('canvas')
    await QRCode.toCanvas(tmp, el.data, {
      margin: 1,
      width: s,
      errorCorrectionLevel: el.ecc || 'M',
      color: { dark: '#000000', light: '#ffffff' },
    })
    ctx.drawImage(tmp, el.x, el.y)
  } else if (el.type === 'barcode' && el.data) {
    const tmp = document.createElement('canvas')
    try {
      JsBarcode(tmp, el.data, {
        format: el.format || 'CODE128',
        width: 2,
        height: Math.max(20, el.h - (el.displayValue === false ? 0 : 22)),
        displayValue: el.displayValue !== false,
        margin: 4,
        font: FONT_FAMILY,
      })
      ctx.drawImage(tmp, el.x, el.y, el.w, el.h)
    } catch {
      // Invalid data for the chosen symbology — leave the area blank.
    }
  }
}

/** Lowest pixel occupied by any element (where the paper should be cut). */
export function contentBottom(elements, pad = 8) {
  if (!elements.length) return 0
  return Math.max(...elements.map((e) => e.y + e.h)) + pad
}

/** Draw the model into `canvas` at 576 x `height`. */
export async function renderToCanvas(canvas, elements, height) {
  const h = Math.max(1, Math.round(height))
  canvas.width = CANVAS_WIDTH
  canvas.height = h
  const ctx = canvas.getContext('2d')
  ctx.fillStyle = '#fff'
  ctx.fillRect(0, 0, CANVAS_WIDTH, h)
  for (const el of elements) {
    // Sequential so async image/QR draws land in document order.
    // eslint-disable-next-line no-await-in-loop
    await drawElement(ctx, el)
  }
  return ctx
}

/** Render the model, trimmed to content height, and return a PNG data URL. */
export async function exportPng(elements) {
  const h = contentBottom(elements)
  if (h <= 0) throw new Error('Add at least one block before printing.')
  const canvas = document.createElement('canvas')
  await renderToCanvas(canvas, elements, h)
  return canvas.toDataURL('image/png')
}
