"""HA-print custom integration: registers two services that fetch data
from HA-storage / HA-recipes and POST it to the HA-print add-on for printing.
"""
from __future__ import annotations

import base64
import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError

from .aisles import group_items_by_aisle
from .clients.printer import PrinterClient
from .clients.recipes import RecipesClient
from .clients.storage import StorageClient
from .const import (
    ADDON_SLUG_RECIPES_PATTERN,
    ADDON_SLUG_STORAGE_PATTERN,
    CONF_ADDON_URL,
    DOMAIN,
    SERVICE_RECIPE,
    SERVICE_SHOPPING_LIST,
)
from .discovery import discover_addon_url

_LOGGER = logging.getLogger(__name__)

SHOPPING_LIST_SCHEMA = vol.Schema(
    {
        vol.Optional("done_filter", default="strike"): vol.In(
            ["strike", "skip", "include"]
        ),
    }
)

RECIPE_SCHEMA = vol.Schema(
    {
        vol.Required("recipe_id"): vol.Coerce(int),
    }
)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    addon_url = entry.data[CONF_ADDON_URL]

    storage_url = await discover_addon_url(
        slug_patterns=[ADDON_SLUG_STORAGE_PATTERN], port=8099
    )
    recipes_url = await discover_addon_url(
        slug_patterns=[ADDON_SLUG_RECIPES_PATTERN], port=8100
    )

    storage = StorageClient(storage_url) if storage_url else None
    recipes = RecipesClient(recipes_url) if recipes_url else None
    printer = PrinterClient(addon_url)

    hass.data[DOMAIN][entry.entry_id] = {
        "printer": printer,
        "storage": storage,
        "recipes": recipes,
    }

    async def _shopping_list_service(call: ServiceCall) -> None:
        if storage is None:
            raise HomeAssistantError(
                "HA-storage add-on was not auto-discovered; cannot fetch shopping list."
            )
        done_filter = call.data.get("done_filter", "strike")
        try:
            items = await storage.fetch_shopping_list()
            products = await storage.fetch_products()
            groups = await storage.fetch_product_groups()
        except Exception as exc:  # noqa: BLE001
            raise HomeAssistantError(f"Failed to fetch list: {exc}") from exc

        products_by_id = {int(p["id"]): p for p in products if "id" in p}
        groups_by_id = {int(g["id"]): g for g in groups if "id" in g}
        aisles = group_items_by_aisle(items, products_by_id, groups_by_id)

        try:
            await printer.print_shopping_list(
                {"aisles": aisles, "done_filter": done_filter}
            )
        except Exception as exc:  # noqa: BLE001
            raise HomeAssistantError(f"Print failed: {exc}") from exc

    async def _recipe_service(call: ServiceCall) -> None:
        if recipes is None:
            raise HomeAssistantError(
                "HA-recipes add-on was not auto-discovered; cannot fetch recipe."
            )
        recipe_id = int(call.data["recipe_id"])
        try:
            recipe = await recipes.fetch_recipe(recipe_id)
        except FileNotFoundError as exc:
            raise HomeAssistantError(str(exc)) from exc
        except Exception as exc:  # noqa: BLE001
            raise HomeAssistantError(f"Failed to fetch recipe: {exc}") from exc

        image_b64: str | None = None
        picture = recipe.get("picture_filename")
        if picture and storage is not None:
            try:
                img = await storage.fetch_recipe_image(picture)
                if img:
                    image_b64 = base64.b64encode(img).decode("ascii")
            except Exception as exc:  # noqa: BLE001
                _LOGGER.warning("Failed to fetch recipe image: %s", exc)

        # Translate HA-recipes ingredient field names → HA-print accepted shape
        ingredients = []
        for ing in recipe.get("ingredients") or []:
            ingredients.append(
                {
                    "name": ing.get("product_name"),
                    "amount": ing.get("amount_needed"),
                    "unit": ing.get("unit_abbrev"),
                    "parent_name": ing.get("parent_name"),
                    "note": ing.get("note"),
                }
            )
        payload = {
            "recipe": {
                "name": recipe.get("name", "Recipe"),
                "servings": recipe.get("servings"),
                "source_url": recipe.get("source_url"),
                "ingredients": ingredients,
                "instructions": recipe.get("instructions") or [],
            },
            "image_b64": image_b64,
        }
        try:
            await printer.print_recipe(payload)
        except Exception as exc:  # noqa: BLE001
            raise HomeAssistantError(f"Print failed: {exc}") from exc

    if not hass.services.has_service(DOMAIN, SERVICE_SHOPPING_LIST):
        hass.services.async_register(
            DOMAIN,
            SERVICE_SHOPPING_LIST,
            _shopping_list_service,
            schema=SHOPPING_LIST_SCHEMA,
        )
    if not hass.services.has_service(DOMAIN, SERVICE_RECIPE):
        hass.services.async_register(
            DOMAIN, SERVICE_RECIPE, _recipe_service, schema=RECIPE_SCHEMA
        )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    # Unregister services only if no entries left
    if not hass.data.get(DOMAIN):
        hass.services.async_remove(DOMAIN, SERVICE_SHOPPING_LIST)
        hass.services.async_remove(DOMAIN, SERVICE_RECIPE)
    return True
