"""Lightweight client for the HA-storage add-on (shopping list + recipe images)."""
from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class StorageClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    async def fetch_shopping_list(self) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(f"{self.base_url}/api/shopping-list")
            r.raise_for_status()
            data = r.json()
        return data if isinstance(data, list) else data.get("items", [])

    async def fetch_products(self) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(f"{self.base_url}/api/products")
            r.raise_for_status()
            data = r.json()
        return data if isinstance(data, list) else data.get("items", [])

    async def fetch_product_groups(self) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(f"{self.base_url}/api/product-groups")
            r.raise_for_status()
            data = r.json()
        return data if isinstance(data, list) else data.get("items", [])

    async def fetch_recipe_image(self, filename: str) -> bytes | None:
        if not filename:
            return None
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(f"{self.base_url}/api/files/recipes/{filename}")
            if r.status_code == 404:
                return None
            r.raise_for_status()
            return r.content
