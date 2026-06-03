"""Named designer templates persisted as JSON under ``/data/templates``.

A template is the browser's element model (positions / sizes / text / style /
image data URLs). The backend never renders it — it only stores and serves the
blob; the frontend re-renders it on load.

One file per template (``<id>.json``) keeps delete trivial and avoids a
read-modify-write race on a shared file. The ``id`` is always server-issued
(uuid hex) and validated before it touches the filesystem, so a template id can
never escape ``TEMPLATES_DIR`` (path-traversal guard).
"""
from __future__ import annotations

import json
import os
import re
import time
import uuid
from typing import Any

DATA_DIR = os.environ.get("DATA_DIR", "/data")
TEMPLATES_DIR = os.path.join(DATA_DIR, "templates")

_SLUG_RE = re.compile(r"[^a-z0-9]+")
_ID_RE = re.compile(r"[0-9a-f]{8,32}")


def _slug(name: str) -> str:
    s = _SLUG_RE.sub("-", name.strip().lower()).strip("-")
    return s or "template"


def _path(tid: str) -> str:
    if not _ID_RE.fullmatch(tid):
        raise ValueError("bad template id")
    return os.path.join(TEMPLATES_DIR, f"{tid}.json")


def list_templates() -> list[dict[str, Any]]:
    """Return template summaries (id / name / updated_at), newest first."""
    os.makedirs(TEMPLATES_DIR, exist_ok=True)
    out: list[dict[str, Any]] = []
    for fn in os.listdir(TEMPLATES_DIR):
        if not fn.endswith(".json"):
            continue
        try:
            with open(os.path.join(TEMPLATES_DIR, fn), encoding="utf-8") as f:
                d = json.load(f)
            out.append(
                {"id": d["id"], "name": d.get("name", ""), "updated_at": d.get("updated_at", 0)}
            )
        except (OSError, ValueError, KeyError):
            continue
    out.sort(key=lambda t: t.get("updated_at", 0), reverse=True)
    return out


def get_template(tid: str) -> dict[str, Any]:
    """Return the full template document. Raises FileNotFoundError if missing."""
    with open(_path(tid), encoding="utf-8") as f:
        return json.load(f)


def save_template(name: str, elements: list, *, tid: str | None = None) -> dict[str, Any]:
    """Create or overwrite a template. Returns the stored document."""
    os.makedirs(TEMPLATES_DIR, exist_ok=True)
    tid = tid or uuid.uuid4().hex
    doc = {
        "id": tid,
        "name": name,
        "slug": _slug(name),
        "elements": elements,
        "updated_at": int(time.time()),
    }
    dest = _path(tid)
    tmp = dest + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False)
    os.replace(tmp, dest)  # atomic
    return doc


def delete_template(tid: str) -> bool:
    """Delete a template. Returns True if it existed."""
    try:
        os.remove(_path(tid))
        return True
    except FileNotFoundError:
        return False
