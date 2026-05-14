"""Lightweight client for the HA-recipes add-on backend."""
from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class RecipesClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    async def fetch_recipe(self, recipe_id: int) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(f"{self.base_url}/api/recipe/{int(recipe_id)}")
            if r.status_code == 404:
                raise FileNotFoundError(f"Recipe {recipe_id} not found")
            r.raise_for_status()
            return r.json()
