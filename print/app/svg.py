"""Rasterize an uploaded SVG to a fixed-width PNG via ``rsvg-convert`` (librsvg).

librsvg is chosen over cairosvg because it ships as a single Alpine package
(``librsvg`` — no cairo/pango/gdk-pixbuf build chain), renders SVG more
completely, and rasterizes directly at the target width so Pillow only has to
reduce to 1-bit.

Security: librsvg does not execute scripts, but ``<image href="file://...">``
/ remote references and DTD entities are real SSRF / XXE / local-file-disclosure
/ billion-laughs risks. We add a cheap byte-level blocklist on top of librsvg's
own sandboxing, cap the input size, and bound the subprocess wall-clock.
"""
from __future__ import annotations

import logging
import re
import shutil
import subprocess

logger = logging.getLogger(__name__)


class SvgError(RuntimeError):
    """Raised when an SVG is rejected or cannot be rasterized."""


MAX_SVG_BYTES = 4 * 1024 * 1024

# Reject scripts, DTD entities (XXE / billion-laughs), local-file refs, and
# remote http(s) references before handing anything to the renderer.
_BLOCK = re.compile(
    rb"<script|<!ENTITY|<!DOCTYPE|\bfile:|href\s*=\s*['\"]\s*https?:",
    re.IGNORECASE,
)


def rsvg_available() -> bool:
    """True if the ``rsvg-convert`` binary is on PATH."""
    return shutil.which("rsvg-convert") is not None


def render_svg_to_png(svg_bytes: bytes, *, width_px: int = 576, timeout: float = 15.0) -> bytes:
    """Render ``svg_bytes`` to a PNG ``width_px`` wide. Returns PNG bytes."""
    if not svg_bytes:
        raise SvgError("empty SVG")
    if len(svg_bytes) > MAX_SVG_BYTES:
        raise SvgError("SVG too large")
    if _BLOCK.search(svg_bytes):
        raise SvgError("SVG contains scripts, external references, or DTD entities (not allowed)")

    try:
        proc = subprocess.run(
            [
                "rsvg-convert",
                "--width", str(width_px),
                "--keep-aspect-ratio",
                "--background-color", "white",
                "--format", "png",
            ],
            input=svg_bytes,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise SvgError("SVG rendering timed out") from exc
    except FileNotFoundError as exc:
        raise SvgError("rsvg-convert is not installed") from exc

    if proc.returncode != 0 or not proc.stdout:
        detail = proc.stderr.decode("utf-8", "replace")[:200]
        raise SvgError(f"rsvg-convert failed: {detail}")
    return proc.stdout
