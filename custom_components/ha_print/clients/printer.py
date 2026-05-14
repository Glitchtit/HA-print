"""Lightweight client for the HA-print add-on itself."""
from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class PrinterClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    async def health(self) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(f"{self.base_url}/api/health")
            r.raise_for_status()
            return r.json()

    async def print_shopping_list(self, payload: dict[str, Any]) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.post(
                f"{self.base_url}/api/print/shopping-list", json=payload
            )
            r.raise_for_status()
            return r.json()

    async def print_recipe(self, payload: dict[str, Any]) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.post(f"{self.base_url}/api/print/recipe", json=payload)
            r.raise_for_status()
            return r.json()
