"""HA-print FastAPI service.

Pure renderer + printer driver. Callers (HA-stock, HA-recipes, or the ha_print
HA integration) submit the data they already have. No upstream fetches.
"""
from __future__ import annotations

import base64
import logging
import os
from contextlib import asynccontextmanager
from typing import Any, Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from .escpos_driver import PrinterError, probe_printer, thermal_printer
from .options import Options
from .templating import recipe as recipe_tpl
from .templating import shopping_list as list_tpl

logging.basicConfig(
    level=logging.DEBUG if os.environ.get("DEBUG") == "1" else logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("ha_print")

OPTIONS = Options.load()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    logger.info(
        "HA-print ready (printer=%s:%d profile=%s codepage=%s impl=%s cut=%s width=%d)",
        OPTIONS.printer_host or "(unset)",
        OPTIONS.printer_port,
        OPTIONS.printer_profile,
        OPTIONS.codepage,
        OPTIONS.image_impl,
        OPTIONS.enable_cut,
        OPTIONS.column_width,
    )
    yield


app = FastAPI(title="HA-print", version="0.1.0", lifespan=lifespan)


# ──── Request schemas ──────────────────────────────────────────────────────


class ShoppingItem(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str
    amount: float | int | None = None
    unit: str | None = None
    done: bool = False
    note: str | None = None


class Aisle(BaseModel):
    model_config = ConfigDict(extra="ignore")

    label: str
    items: list[ShoppingItem] = Field(default_factory=list)


class PrintShoppingListRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    title: str | None = "Ostoslista"
    timestamp: str | None = None
    aisles: list[Aisle] = Field(default_factory=list)
    done_filter: Literal["skip", "strike", "include"] = "strike"


class RecipeIngredient(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str | None = None
    product_name: str | None = None
    amount: float | int | None = None
    amount_needed: float | int | None = None
    unit: str | None = None
    unit_abbrev: str | None = None
    parent_name: str | None = None
    note: str | None = None


class Recipe(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str
    servings: float | int | None = None
    source_url: str | None = None
    ingredients: list[RecipeIngredient] = Field(default_factory=list)
    instructions: list[str] = Field(default_factory=list)


class PrintRecipeRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    recipe: Recipe
    image_b64: str | None = None


# ──── Routes ───────────────────────────────────────────────────────────────


@app.get("/api/health")
async def health():
    reachable = probe_printer(OPTIONS.printer_host, OPTIONS.printer_port, timeout=2.0)
    return JSONResponse(
        {
            "status": "ok",
            "printer_host": OPTIONS.printer_host,
            "printer_port": OPTIONS.printer_port,
            "printer_reachable": reachable,
            "version": "0.1.0",
        }
    )


@app.post("/api/print/shopping-list")
async def print_shopping_list(body: PrintShoppingListRequest):
    if not OPTIONS.printer_host:
        raise HTTPException(503, "printer_host is not configured in add-on options")

    aisles = [a.model_dump() for a in body.aisles]
    try:
        with thermal_printer(OPTIONS) as p:
            summary = list_tpl.render(
                p,
                title=body.title or "Ostoslista",
                timestamp=body.timestamp,
                aisles=aisles,
                done_filter=body.done_filter,
                column_width=OPTIONS.column_width,
            )
    except PrinterError as exc:
        logger.warning("Printer error on shopping-list: %s", exc)
        raise HTTPException(503, str(exc))

    return {"ok": True, **summary}


@app.post("/api/print/recipe")
async def print_recipe(body: PrintRecipeRequest):
    if not OPTIONS.printer_host:
        raise HTTPException(503, "printer_host is not configured in add-on options")

    image_bytes: bytes | None = None
    if body.image_b64:
        try:
            image_bytes = base64.b64decode(body.image_b64)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to decode image_b64: %s", exc)
            image_bytes = None

    recipe_dict = body.recipe.model_dump()
    try:
        with thermal_printer(OPTIONS) as p:
            summary = recipe_tpl.render(
                p,
                recipe=recipe_dict,
                image_bytes=image_bytes,
                column_width=OPTIONS.column_width,
                image_impl=OPTIONS.image_impl,
            )
    except PrinterError as exc:
        logger.warning("Printer error on recipe: %s", exc)
        raise HTTPException(503, str(exc))

    return {"ok": True, **summary}


def main() -> None:
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8100,
        log_level="info",
    )


if __name__ == "__main__":
    main()
