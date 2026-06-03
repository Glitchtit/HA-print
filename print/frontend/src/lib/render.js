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

// Physical scale: the bitmap prints 1px = 1 dot at 203 dpi (vertical raster is
// 1:1), so the drill guide renders at true size on paper.
export const PX_PER_MM = 203 / 25.4 // ≈ 7.99 dots per mm
export const DRILL_ARM = 12 // crosshair arm length in px (~3mm)
export const DRILL_WIDTH = 2 * DRILL_ARM + 8
// Box height so the two crosshair centers are exactly `mm` apart.
export const drillGuideHeight = (mm) => Math.round(Math.max(0, mm || 0) * PX_PER_MM) + 2 * DRILL_ARM

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
  } else if (el.type === 'drillguide') {
    // Two crosshairs a precise center-to-center distance apart, joined by a
    // vertical line. The centers sit DRILL_ARM in from the top/bottom edges, so
    // the box height encodes the distance (see drillGuideHeight).
    const arm = el.arm || DRILL_ARM
    const cx = el.x + el.w / 2
    const c1y = el.y + arm
    const c2y = el.y + el.h - arm
    ctx.strokeStyle = '#000'
    ctx.setLineDash([])
    ctx.lineWidth = el.lineWidth || 2
    ctx.beginPath()
    ctx.moveTo(cx, c1y)
    ctx.lineTo(cx, c2y)
    ctx.stroke()
    for (const cy of [c1y, c2y]) {
      ctx.beginPath()
      ctx.moveTo(cx - arm, cy)
      ctx.lineTo(cx + arm, cy)
      ctx.moveTo(cx, cy - arm)
      ctx.lineTo(cx, cy + arm)
      ctx.stroke()
      // Circle on the crosshair's outer bounds (touches the arm tips).
      ctx.beginPath()
      ctx.arc(cx, cy, arm, 0, Math.PI * 2)
      ctx.stroke()
    }
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

/** Lowest box edge of any element — a generous upper bound for the render height. */
export function contentBottom(elements, pad = 8) {
  if (!elements.length) return 0
  return Math.max(...elements.map((e) => e.y + e.h)) + pad
}

/**
 * Lowest box edge of any "blank feed" spacer block. These draw no ink but are
 * intentional trailing space, so they must still extend the print / cut.
 */
export function spacerBottom(elements) {
  const spacers = elements.filter((e) => e.type === 'divider' && e.lineStyle === 'blank')
  return spacers.length ? Math.max(...spacers.map((e) => e.y + e.h)) : 0
}

/**
 * The last row of `canvas` that actually has ink, + `pad`. This is where the
 * paper should be cut — using real pixels (not element boxes) so oversized
 * boxes around text/QR/barcodes don't leave a gap before the cut. Returns 0 if
 * the canvas is blank.
 */
export function measureInkBottom(canvas, pad = 8) {
  const { width, height } = canvas
  if (!width || !height) return 0
  const data = canvas.getContext('2d').getImageData(0, 0, width, height).data
  for (let y = height - 1; y >= 0; y--) {
    const row = y * width * 4
    for (let x = 0; x < width; x++) {
      const i = row + x * 4
      if (data[i] < 250 || data[i + 1] < 250 || data[i + 2] < 250) {
        return Math.min(height, y + 1 + pad)
      }
    }
  }
  return 0
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

/** Render the model, trimmed to the last inked row, and return a PNG data URL. */
export async function exportPng(elements) {
  const boxH = contentBottom(elements)
  if (boxH <= 0) throw new Error('Add at least one block before printing.')
  const canvas = document.createElement('canvas')
  await renderToCanvas(canvas, elements, boxH)
  // Cut at the last ink, or below a blank-feed spacer if one extends further.
  const cutH = Math.max(measureInkBottom(canvas, 8), Math.round(spacerBottom(elements)))
  if (cutH <= 0) throw new Error('Nothing to print — your blocks have no content.')
  if (cutH >= canvas.height) return canvas.toDataURL('image/png')
  const cropped = document.createElement('canvas')
  cropped.width = canvas.width
  cropped.height = cutH
  cropped.getContext('2d').drawImage(canvas, 0, 0)
  return cropped.toDataURL('image/png')
}
