"""Tests for the text-style spec parser."""
from __future__ import annotations

from app.templating.style import TextStyle


def test_default():
    s = TextStyle.parse(None)
    assert s == TextStyle()
    assert s.font == "a" and s.width == 1 and s.height == 1
    assert not s.bold and not s.underline


def test_shorthand_font_only():
    assert TextStyle.parse("a") == TextStyle(font="a")
    assert TextStyle.parse("b") == TextStyle(font="b")


def test_shorthand_size_both():
    assert TextStyle.parse("a2") == TextStyle(font="a", width=2, height=2)
    assert TextStyle.parse("b3") == TextStyle(font="b", width=3, height=3)


def test_explicit_wh():
    assert TextStyle.parse("a1x2") == TextStyle(font="a", width=1, height=2)
    assert TextStyle.parse("a2x1") == TextStyle(font="a", width=2, height=1)


def test_modifiers():
    assert TextStyle.parse("a-bold") == TextStyle(font="a", bold=True)
    assert TextStyle.parse("b-bold-underline") == TextStyle(font="b", bold=True, underline=True)
    assert TextStyle.parse("a1x2-bold") == TextStyle(font="a", width=1, height=2, bold=True)


def test_clamping():
    assert TextStyle.parse("a99").width == 4
    assert TextStyle.parse("a99").height == 4
    assert TextStyle.parse("a0").width == 1  # 0 clamped to min 1


def test_invalid_fragment_ignored():
    assert TextStyle.parse("a-foo") == TextStyle(font="a")


def test_width_chars_font_a():
    s = TextStyle(font="a", width=1)
    assert s.width_chars(32) == 32
    assert TextStyle(font="a", width=2).width_chars(32) == 16


def test_width_chars_font_b():
    # Font B is ~33% narrower per char → more chars fit on the same width.
    s = TextStyle(font="b")
    assert s.width_chars(32) > 32
    assert s.width_chars(32) <= int(32 * 1.34)


def test_apply_sets_double_for_2x():
    calls = []

    class FakePrinter:
        def set(self, **kw):
            calls.append(kw)

    TextStyle.parse("a2-bold").apply(FakePrinter())
    assert calls
    kw = calls[0]
    assert kw["font"] == "a"
    assert kw["bold"] is True
    assert kw["double_width"] is True
    assert kw["double_height"] is True
    assert kw.get("custom_size") is False
