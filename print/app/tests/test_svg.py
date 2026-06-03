"""Tests for server-side SVG rasterization and its security blocklist."""
from __future__ import annotations

import pytest

from app.svg import SvgError, render_svg_to_png, rsvg_available

VALID = (
    b'<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10">'
    b'<rect width="10" height="10"/></svg>'
)


def test_rejects_empty():
    with pytest.raises(SvgError):
        render_svg_to_png(b"")


def test_rejects_script():
    with pytest.raises(SvgError):
        render_svg_to_png(b"<svg><script>alert(1)</script></svg>")


def test_rejects_doctype_entity():
    with pytest.raises(SvgError):
        render_svg_to_png(b'<!DOCTYPE svg [<!ENTITY x "y">]><svg/>')


def test_rejects_remote_reference():
    with pytest.raises(SvgError):
        render_svg_to_png(b'<svg><image href="http://evil.example/x.png"/></svg>')


def test_rejects_oversize():
    with pytest.raises(SvgError):
        render_svg_to_png(b"<svg/>" + b" " * (5 * 1024 * 1024))


@pytest.mark.skipif(not rsvg_available(), reason="rsvg-convert not installed")
def test_valid_svg_renders_png():
    png = render_svg_to_png(VALID, width_px=576)
    assert png[:8] == b"\x89PNG\r\n\x1a\n"
