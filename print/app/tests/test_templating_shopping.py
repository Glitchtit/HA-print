"""Unit tests for the shopping-list templating module."""
from __future__ import annotations

from escpos.printer import Dummy

from app.templating import shopping_list as list_tpl


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


def test_long_name_is_truncated_to_column_width():
    long = "X" * 200
    out = _render(
        aisles=[{"label": "A", "items": [{"name": long}]}],
        column_width=32,
    )
    text = out.decode("cp858", errors="replace")
    for line in text.splitlines():
        # Ignore initial header lines which use double-width
        if line.startswith("[ ]"):
            assert len(line) <= 32
