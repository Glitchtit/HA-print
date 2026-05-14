"""Unit tests for the shopping-list templating module."""
from __future__ import annotations

from escpos.printer import Dummy

from app.templating import shopping_list as list_tpl


def _strip(raw: bytes) -> str:
    """Byte-accurate scrub of ESC/POS control sequences before decoding."""
    out = bytearray()
    i = 0
    while i < len(raw):
        b = raw[i]
        if b == 0x1B:  # ESC + cmd + (optional 1-byte param)
            cmd = raw[i + 1] if i + 1 < len(raw) else 0
            i += 2 if cmd == 0x40 else 3  # ESC @ has no param; everything else 1
        elif b == 0x1D:  # GS + cmd + 1 or 2 param bytes
            cmd = raw[i + 1] if i + 1 < len(raw) else 0
            i += 4 if cmd == 0x56 else 3  # GS V (cut) takes 2 params
        elif b == 0x1C:  # FS + cmd
            i += 2
        elif b in (0x00, 0x07):
            i += 1
        else:
            out.append(b)
            i += 1
    return bytes(out).decode("cp858", errors="replace")


def _render(**kwargs) -> bytes:
    p = Dummy()
    list_tpl.render(p, **kwargs)
    return p.output


def test_renders_empty_list_with_placeholder():
    out = _render(aisles=[], timestamp="2026-05-14 12:00")
    text = out.decode("cp858", errors="replace")
    assert "Ostoslista" in text
    assert "2026-05-14 12:00" in text
    assert "tyhja lista" in text


def test_renders_two_aisles_in_order():
    out = _render(
        aisles=[
            {
                "label": "Hedelmät & vihannekset",
                "items": [
                    {"name": "Banaani", "amount": 2, "unit": "kpl"},
                    {"name": "Omena", "amount": 1, "unit": "kg"},
                ],
            },
            {
                "label": "Maitotuotteet",
                "items": [
                    {"name": "Maito", "amount": 1, "unit": "l", "note": "rasvaton"},
                ],
            },
        ],
        timestamp="2026-05-14 12:00",
    )
    text = out.decode("cp858", errors="replace")
    assert text.index("Hedelmät") < text.index("Maitotuotteet")
    assert "Banaani" in text and "Omena" in text and "Maito" in text
    assert "rasvaton" in text  # per-item note prints


def test_done_filter_skip_omits_done_items():
    out = _render(
        aisles=[
            {
                "label": "Aisle",
                "items": [
                    {"name": "Done item", "done": True},
                    {"name": "Open item", "done": False},
                ],
            }
        ],
        done_filter="skip",
    )
    text = out.decode("cp858", errors="replace")
    assert "Open item" in text
    assert "Done item" not in text


def test_done_filter_strike_prints_marker():
    out = _render(
        aisles=[
            {
                "label": "Aisle",
                "items": [
                    {"name": "Done item", "done": True},
                ],
            }
        ],
        done_filter="strike",
    )
    text = out.decode("cp858", errors="replace")
    assert "[x]" in text
    assert "Done item" in text
    # The strike-through bar of dashes should appear right after the item
    assert "---" in text


def test_done_filter_include_prints_as_normal():
    out = _render(
        aisles=[
            {
                "label": "Aisle",
                "items": [
                    {"name": "Done item", "done": True},
                ],
            }
        ],
        done_filter="include",
    )
    text = out.decode("cp858", errors="replace")
    assert "[x] " in text
    assert "Done item" in text


def test_long_name_wraps_with_indent():
    long = ("Banaani " * 12).strip()  # repeating word, forces word-wrap
    out = _render(
        aisles=[{"label": "A", "items": [{"name": long, "amount": 1}]}],
        column_width=32,
    )
    text = _strip(out)
    item_lines = [l for l in text.splitlines() if "Banaani" in l]
    # At least two lines for a wrapped long name
    assert len(item_lines) >= 2
    # No line should exceed the column width
    for line in item_lines:
        assert len(line) <= 48, f"Line too long ({len(line)}): {line!r}"
    # No "?" droppings from missing-codepage chars
    assert "?" not in "\n".join(item_lines)


def test_compact_prefix_no_wide_padding():
    out = _render(
        aisles=[{"label": "A", "items": [{"name": "Banaani", "amount": 2, "unit": "kpl"}]}],
        column_width=32,
    )
    text = _strip(out)
    # Compact format with no chasm between qty and name
    assert "[ ] 2 kpl Banaani" in text
    # Negative: no wide-padding from a fixed qty column
    assert "[ ] 2 kpl       Banaani" not in text


def test_header_and_footer_text():
    out = _render(
        aisles=[{"label": "A", "items": [{"name": "Banaani", "amount": 1}]}],
        header_text="Wredlund household",
        footer_text="Tervetuloa kauppaan!",
    )
    text = _strip(out)
    # Header appears before "Ostoslista" title
    assert text.index("Wredlund household") < text.index("Ostoslista")
    # Footer appears after the items
    assert text.index("Banaani") < text.index("Tervetuloa kauppaan!")
