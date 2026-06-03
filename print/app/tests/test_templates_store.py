"""Tests for the JSON template store, including the path-traversal guard."""
from __future__ import annotations

import pytest

from app import templates_store


@pytest.fixture
def store(tmp_path, monkeypatch):
    monkeypatch.setattr(templates_store, "DATA_DIR", str(tmp_path))
    monkeypatch.setattr(templates_store, "TEMPLATES_DIR", str(tmp_path / "templates"))
    return templates_store


def test_save_get_list_delete(store):
    doc = store.save_template("My label", [{"type": "text", "text": "hi"}])
    tid = doc["id"]
    assert store.get_template(tid)["elements"] == [{"type": "text", "text": "hi"}]
    assert any(t["id"] == tid for t in store.list_templates())
    assert store.delete_template(tid) is True
    with pytest.raises(FileNotFoundError):
        store.get_template(tid)


def test_overwrite_same_id(store):
    tid = store.save_template("a", [])["id"]
    store.save_template("b", [{"type": "qr"}], tid=tid)
    assert store.get_template(tid)["name"] == "b"
    assert len(store.list_templates()) == 1


def test_delete_missing_returns_false(store):
    assert store.delete_template("deadbeef") is False


def test_id_traversal_guard(store):
    with pytest.raises(ValueError):
        store._path("../etc/passwd")
    with pytest.raises(ValueError):
        store.get_template("../../evil")
