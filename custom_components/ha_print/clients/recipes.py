"""Lightweight client for the HA-recipes add-on backend."""
from __future__ import annotations

import logging
from typing import Any

import httpx
from homeassistant.util.ssl import get_default_context

logger = logging.getLogger(__name__)


class RecipesClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    async def fetch_recipe(self, recipe_id: int) -> dict[str, Any]:
        """The recipe detail; HA-recipes wraps it as {"success": true, "recipe": {...}}."""
        async with httpx.AsyncClient(verify=get_default_context(), timeout=15) as client:
            r = await client.get(f"{self.base_url}/api/recipe/{int(recipe_id)}")
        if r.status_code == 404:
            raise FileNotFoundError(f"Recipe {recipe_id} not found")
        try:
            data = r.json()
        except ValueError:
            data = None
        if isinstance(data, dict) and data.get("success") is False:
            raise RuntimeError(data.get("error") or f"Recipe {recipe_id} could not be fetched")
        r.raise_for_status()
        if isinstance(data, dict) and isinstance(data.get("recipe"), dict):
            return data["recipe"]
        return data
