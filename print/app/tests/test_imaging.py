"""Tests for the shared image → 1-bit pipeline."""
from __future__ import annotations

import io

from PIL import Image

from app.imaging import prepare_image


def _png(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_threshold_yields_pure_black_and_white():
    img = Image.new("RGB", (10, 4), (255, 255, 255))
    for y in range(4):
        for x in range(5):
            img.putpixel((x, y), (0, 0, 0))
    out = prepare_image(_png(img), target_width=10, mode="threshold")
    assert out.mode == "1"
    assert set(out.convert("L").getdata()) <= {0, 255}


def test_resizes_to_target_width_keeping_aspect():
    out = prepare_image(_png(Image.new("RGB", (100, 50), (0, 0, 0))), target_width=576, mode="threshold")
    assert out.size == (576, 288)  # 50 * 576 / 100


def test_dither_gradient_is_1bit():
    grad = Image.new("L", (64, 8))
    for x in range(64):
        for y in range(8):
            grad.putpixel((x, y), min(255, x * 4))
    out = prepare_image(_png(grad.convert("RGB")), target_width=64, mode="dither")
    assert out.mode == "1"


def test_height_scale_stretches_only_height():
    raw = _png(Image.new("RGB", (100, 100), (0, 0, 0)))
    base = prepare_image(raw, target_width=100, mode="threshold")
    scaled = prepare_image(raw, target_width=100, mode="threshold", height_scale=1.1)
    assert scaled.size[0] == base.size[0] == 100  # width unchanged
    assert scaled.size[1] == round(base.size[1] * 1.1)  # height calibrated up


def test_transparent_rgba_flattens_onto_white():
    out = prepare_image(_png(Image.new("RGBA", (8, 8), (0, 0, 0, 0))), target_width=8, mode="threshold")
    # Fully transparent must read as white (unprinted), not black.
    assert set(out.convert("L").getdata()) == {255}
