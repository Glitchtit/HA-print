"""Unit tests for the shopping-list templating module."""
from __future__ import annotations

import re

from escpos.printer import Dummy

from app.templating import shopping_list as list_tpl

# ESC sequences leak into decoded text when bold/underline reset codes land at
# the start of a line. Strip them when asserting on visible text.
_ESC_RE = re.compile(r"\x1b[!\-EGV][\x00-\xff]?")


def _strip(s: str) -> str:
    return _ESC_RE.sub("", s)


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
    text = out.decode("cp858", errors="replace")
    item_lines = [_strip(l) for l in text.splitlines() if "Banaani" in l]
    # At least two lines for a wrapped long name
    assert len(item_lines) >= 2
    # No line should exceed the column width (after stripping ESC bytes)
    for line in item_lines:
        assert len(line) <= 32, f"Line too long ({len(line)}): {line!r}"
    # No "?" droppings from missing-codepage chars (was caused by "…" truncation)
    assert "?" not in "\n".join(item_lines)


def test_compact_prefix_no_wide_padding():
    out = _render(
        aisles=[{"label": "A", "items": [{"name": "Banaani", "amount": 2, "unit": "kpl"}]}],
        column_width=32,
    )
    text = out.decode("cp858", errors="replace")
    line = next(_strip(l) for l in text.splitlines() if "Banaani" in l)
    # Compact format: "[ ] 2 kpl Banaani" — no big gap between qty and name
    assert line == "[ ] 2 kpl Banaani"
