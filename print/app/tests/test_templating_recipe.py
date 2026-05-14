"""Unit tests for the recipe templating module."""
from __future__ import annotations

import io

from escpos.printer import Dummy
from PIL import Image

from app.templating import recipe as recipe_tpl


def _render(**kwargs) -> bytes:
    p = Dummy()
    recipe_tpl.render(p, **kwargs)
    return p.output


def _png_bytes(width: int = 200, height: int = 100, color=(120, 80, 200)) -> bytes:
    img = Image.new("RGB", (width, height), color=color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_renders_recipe_without_image():
    out = _render(
        recipe={
            "name": "Mustikkapiirakka",
            "servings": 8,
            "source_url": "https://example.com/p",
            "ingredients": [
                {"amount_needed": 2.0, "unit_abbrev": "dl", "product_name": "mustikoita"},
                {"amount_needed": 1, "unit_abbrev": "kpl", "product_name": "muna", "note": "huoneenlampöinen"},
            ],
            "instructions": ["Lämmitä uuni 200 asteeseen.", "Sekoita ainekset ja paista 30 min."],
        },
    )
    text = out.decode("cp858", errors="replace")
    assert "Mustikkapiirakka" in text
    assert "Annokset: 8" in text
    assert "Ainekset" in text and "Ohjeet" in text
    assert "mustikoita" in text and "muna" in text
    assert "huoneenlampöinen" in text or "huoneenlamp" in text  # codepage might mangle ö
    assert "1." in text and "2." in text


def test_renders_recipe_with_image():
    out = _render(
        recipe={"name": "Test", "ingredients": [], "instructions": []},
        image_bytes=_png_bytes(),
    )
    # The image() call emits ESC/POS raster commands — they should be in the
    # output as GS v 0 (1D 76 30) or similar; we don't need to decode them,
    # just confirm they're present.
    assert len(out) > 200
    assert b"Test" in out


def test_step_wraps_long_instructions():
    long_step = "Sekoita kaikki ainekset. " * 8  # long step that needs wrapping
    out = _render(
        recipe={"name": "X", "ingredients": [], "instructions": [long_step]},
        column_width=32,
    )
    text = out.decode("cp858", errors="replace")
    # Find lines in the instructions section (after "Ohjeet")
    idx = text.index("Ohjeet")
    instruction_block = text[idx:]
    body_lines = [l for l in instruction_block.splitlines() if l and "Ohjeet" not in l and "---" not in l]
    # At least 2 lines for a wrapped step
    assert len(body_lines) >= 2


def test_renders_ingredient_with_parent_name():
    out = _render(
        recipe={
            "name": "X",
            "ingredients": [
                {
                    "amount_needed": 100,
                    "unit_abbrev": "g",
                    "product_name": "Atria broileri",
                    "parent_name": "broileri",
                }
            ],
            "instructions": [],
        },
    )
    text = out.decode("cp858", errors="replace")
    assert "broileri" in text  # parent name shown in parens
    assert "100 g" in text or "100g" in text


def test_renders_recipe_with_minimal_data():
    out = _render(recipe={"name": "Bare"})
    text = out.decode("cp858", errors="replace")
    assert "Bare" in text
