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

from . import svg as svg_mod
from . import templates_store
from .escpos_driver import PrinterError, probe_printer, thermal_printer
from .imaging import prepare_image
from .options import Options
from .templating import recipe as recipe_tpl
from .templating import shopping_list as list_tpl
from .templating.style import TextStyle

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


class PrintImageRequest(BaseModel):
    """A pre-composed bitmap to print as-is (the receipt designer's output)."""

    model_config = ConfigDict(extra="ignore")

    image_b64: str  # base64 PNG; may carry a `data:image/png;base64,` prefix
    dither: bool = False  # composites are line-art-heavy → threshold by default
    width_px: int = Field(default=576, ge=8, le=576)
    threshold: int = Field(default=128, ge=1, le=254)


class PrintSvgRequest(BaseModel):
    """An uploaded SVG, rasterized server-side then printed."""

    model_config = ConfigDict(extra="ignore")

    svg_b64: str
    dither: bool | None = None  # None → use the add-on's svg_default_dither
    width_px: int = Field(default=576, ge=8, le=576)


class SaveTemplateRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str | None = None
    name: str
    elements: list[dict] = Field(default_factory=list)


# ──── Routes ───────────────────────────────────────────────────────────────


def _decode_b64(s: str) -> bytes:
    """Decode base64, stripping an optional `data:...;base64,` data-URL prefix."""
    if s.strip().startswith("data:") and "," in s:
        s = s.split(",", 1)[1]
    return base64.b64decode(s)


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
                title_style=TextStyle.parse(OPTIONS.title_style),
                header_style=TextStyle.parse(OPTIONS.header_style),
                item_style=TextStyle.parse(OPTIONS.item_style),
                note_style=TextStyle.parse(OPTIONS.note_style),
                header_text=OPTIONS.header_text or None,
                footer_text=OPTIONS.footer_text or None,
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
                title_style=TextStyle.parse(OPTIONS.title_style),
                header_style=TextStyle.parse(OPTIONS.header_style),
                item_style=TextStyle.parse(OPTIONS.item_style),
                note_style=TextStyle.parse(OPTIONS.note_style),
                header_text=OPTIONS.header_text or None,
                footer_text=OPTIONS.footer_text or None,
            )
    except PrinterError as exc:
        logger.warning("Printer error on recipe: %s", exc)
        raise HTTPException(503, str(exc))

    return {"ok": True, **summary}


@app.post("/api/print/image")
async def print_image(body: PrintImageRequest):
    """Print a pre-composed bitmap (the receipt designer's canvas export)."""
    if not OPTIONS.printer_host:
        raise HTTPException(503, "printer_host is not configured in add-on options")

    try:
        raw = _decode_b64(body.image_b64)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(400, f"invalid image_b64: {exc}")

    try:
        img = prepare_image(
            raw,
            target_width=body.width_px,
            mode="dither" if body.dither else "threshold",
            threshold=body.threshold,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(400, f"could not decode image: {exc}")

    try:
        with thermal_printer(OPTIONS) as p:
            p.set(align="center")
            p.image(img, impl=OPTIONS.image_impl, center=False)
            p.set(align="left")
            p.text("\n")
    except PrinterError as exc:
        logger.warning("Printer error on image: %s", exc)
        raise HTTPException(503, str(exc))

    return {"ok": True, "width_px": img.size[0], "height_px": img.size[1]}


@app.post("/api/print/svg")
async def print_svg(body: PrintSvgRequest):
    """Rasterize an uploaded SVG server-side, then print it."""
    if not OPTIONS.printer_host:
        raise HTTPException(503, "printer_host is not configured in add-on options")

    try:
        svg_bytes = _decode_b64(body.svg_b64)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(400, f"invalid svg_b64: {exc}")

    try:
        png = svg_mod.render_svg_to_png(svg_bytes, width_px=body.width_px)
    except svg_mod.SvgError as exc:
        raise HTTPException(400, str(exc))

    dither = OPTIONS.svg_default_dither if body.dither is None else body.dither
    try:
        img = prepare_image(png, target_width=body.width_px, mode="dither" if dither else "threshold")
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(400, f"could not rasterize SVG: {exc}")

    try:
        with thermal_printer(OPTIONS) as p:
            p.set(align="center")
            p.image(img, impl=OPTIONS.image_impl, center=False)
            p.set(align="left")
            p.text("\n")
    except PrinterError as exc:
        logger.warning("Printer error on svg: %s", exc)
        raise HTTPException(503, str(exc))

    return {"ok": True, "width_px": img.size[0], "height_px": img.size[1]}


# ──── Designer templates (persisted in /data/templates) ──────────────────────


@app.get("/api/templates")
async def list_templates():
    return {"templates": templates_store.list_templates()}


@app.get("/api/templates/{template_id}")
async def get_template(template_id: str):
    try:
        return templates_store.get_template(template_id)
    except FileNotFoundError:
        raise HTTPException(404, "template not found")
    except ValueError:
        raise HTTPException(400, "bad template id")


@app.post("/api/templates")
async def save_template(body: SaveTemplateRequest):
    if not body.name.strip():
        raise HTTPException(400, "name is required")
    try:
        return templates_store.save_template(body.name.strip(), body.elements, tid=body.id)
    except ValueError:
        raise HTTPException(400, "bad template id")


@app.delete("/api/templates/{template_id}")
async def delete_template(template_id: str):
    try:
        existed = templates_store.delete_template(template_id)
    except ValueError:
        raise HTTPException(400, "bad template id")
    return {"ok": True, "deleted": existed}


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
