/**
 * Alignment snapping for the designer canvas. Given a dragged block's box and
 * the other blocks, find the nearest snap for each axis to either a canvas
 * center line or another block's edge/center, and report which guideline(s) to
 * draw. All coordinates are in logical canvas pixels (the 576px space).
 */
export const SNAP_THRESHOLD = 6

export function computeSnap(w, h, x, y, others, canvasW, canvasH, threshold = SNAP_THRESHOLD) {
  // Candidate lines: canvas center, plus each other block's near/center/far edge.
  const vTargets = [canvasW / 2, ...others.flatMap((o) => [o.x, o.x + o.w / 2, o.x + o.w])]
  const hTargets = [canvasH / 2, ...others.flatMap((o) => [o.y, o.y + o.h / 2, o.y + o.h])]

  // The dragged block can snap by its left/center/right (and top/center/bottom).
  let bestX = null
  for (const off of [0, w / 2, w]) {
    for (const t of vTargets) {
      const d = t - (x + off)
      if (Math.abs(d) <= threshold && (!bestX || Math.abs(d) < Math.abs(bestX.d))) bestX = { d, pos: t }
    }
  }
  let bestY = null
  for (const off of [0, h / 2, h]) {
    for (const t of hTargets) {
      const d = t - (y + off)
      if (Math.abs(d) <= threshold && (!bestY || Math.abs(d) < Math.abs(bestY.d))) bestY = { d, pos: t }
    }
  }

  const guides = []
  if (bestX) guides.push({ axis: 'v', pos: bestX.pos })
  if (bestY) guides.push({ axis: 'h', pos: bestY.pos })

  return {
    x: Math.round(bestX ? x + bestX.d : x),
    y: Math.round(bestY ? y + bestY.d : y),
    guides,
  }
}
