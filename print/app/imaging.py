"""Shared image → 1-bit pipeline for thermal printing.

Used by the recipe hero image, the generic ``/api/print/image`` endpoint, and
the SVG-upload endpoint. Two reduction modes:

  - ``dither``    — Floyd-Steinberg (best for photographs / grayscale gradients)
  - ``threshold`` — hard luminance cutoff (best for QR codes, barcodes, text and
                    line art — dithering shreds QR finder patterns and thin
                    strokes, making them unscannable / fuzzy)
"""
from __future__ import annotations

import io
from typing import Literal

from PIL import Image

# Font A full printable width on the XP-80T at 203 dpi (576 dots / 72 mm).
# See CHANGELOG 0.1.3 — the selftest confirmed 48 chars/line == 576 dots.
FULL_WIDTH_PX = 576

ReduceMode = Literal["dither", "threshold"]


def prepare_image(
    raw: bytes,
    *,
    target_width: int = FULL_WIDTH_PX,
    mode: ReduceMode = "dither",
    threshold: int = 128,
    height_scale: float = 1.0,
) -> Image.Image:
    """Decode ``raw`` image bytes → resize to ``target_width`` → 1-bit mode.

    Transparency is flattened onto white first (thermal paper is white, so
    "transparent" should read as unprinted, not black).

    ``height_scale`` vertically stretches the bitmap before reduction — used to
    calibrate for a printer whose paper feed differs from its nominal dpi, so
    physical lengths (e.g. the drill guide) come out correct.
    """
    img = Image.open(io.BytesIO(raw))

    # Flatten any alpha / palette transparency onto a white background.
    if img.mode in ("RGBA", "LA", "P"):
        img = img.convert("RGBA")
        bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
        img = Image.alpha_composite(bg, img).convert("RGB")
    elif img.mode != "RGB":
        img = img.convert("RGB")

    w, h = img.size
    if w != target_width:
        new_h = max(1, round(h * (target_width / w)))
        img = img.resize((target_width, new_h), Image.LANCZOS)

    if abs(height_scale - 1.0) > 1e-6:
        w2, h2 = img.size
        img = img.resize((w2, max(1, round(h2 * height_scale))), Image.LANCZOS)

    gray = img.convert("L")
    if mode == "threshold":
        # point() with a boolean expression yields a 1-bit ("1") image with a
        # hard cutoff — no dithering, so edges stay crisp.
        return gray.point(lambda p: 255 if p >= threshold else 0, mode="1")
    return gray.convert("1", dither=Image.FLOYDSTEINBERG)
