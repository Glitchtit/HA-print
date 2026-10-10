"""ha_print.recipe reads the recipe out of HA-recipes' {"success", "recipe"} envelope.

Needs the `homeassistant` package (skipped in a bare pytest environment).
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import pytest

pytest.importorskip("homeassistant")

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "custom_components"))

from ha_print.clients import recipes as recipes_mod  # noqa: E402


class _Response:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self):
        return self._payload


def _client_answering(response):
    class _Client:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc):
            return False

        async def get(self, url):
            return response

    return _Client


def test_the_recipe_comes_out_of_the_envelope(monkeypatch):
    recipe = {"id": 3, "name": "Kastike", "ingredients": [], "instructions": ["Sekoita."]}
    monkeypatch.setattr(recipes_mod.httpx, "AsyncClient",
                        _client_answering(_Response(200, {"success": True, "recipe": recipe})))
    got = asyncio.run(recipes_mod.RecipesClient("http://recipes:8100").fetch_recipe(3))
    assert got == recipe


def test_a_failed_answer_raises(monkeypatch):
    monkeypatch.setattr(recipes_mod.httpx, "AsyncClient",
                        _client_answering(_Response(500, {"success": False, "error": "Recipe 3 not found"})))
    with pytest.raises(Exception, match="Recipe 3 not found"):
        asyncio.run(recipes_mod.RecipesClient("http://recipes:8100").fetch_recipe(3))
