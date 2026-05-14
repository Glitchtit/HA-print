"""FastAPI route tests. We patch the printer driver so no real I/O happens."""
from __future__ import annotations

import base64
import io
from contextlib import contextmanager

import pytest
from escpos.printer import Dummy
from fastapi.testclient import TestClient
from PIL import Image

from app import main as main_mod
from app.options import Options


@pytest.fixture
def configured_options(monkeypatch):
    """Replace OPTIONS with a configured-looking one so endpoints don't 503."""
    opts = Options(
        printer_host="127.0.0.1",
        printer_port=9100,
        printer_profile="default",
        codepage="CP858",
        image_impl="bitImageRaster",
        enable_cut=False,
        column_width=48,
        debug=False,
    )
    monkeypatch.setattr(main_mod, "OPTIONS", opts)
    yield opts


@pytest.fixture
def fake_printer(monkeypatch):
    """Replace thermal_printer with a context manager yielding a Dummy."""
    captured: dict[str, Dummy] = {}

    @contextmanager
    def _fake(_options):
        d = Dummy()
        captured["dummy"] = d
        yield d

    monkeypatch.setattr(main_mod, "thermal_printer", _fake)
    yield captured


def test_health_endpoint(monkeypatch):
    opts = Options(
        printer_host="10.0.0.99",
        printer_port=9100,
        printer_profile="default",
        codepage="CP858",
        image_impl="bitImageRaster",
        enable_cut=True,
        column_width=48,
        debug=False,
    )
    monkeypatch.setattr(main_mod, "OPTIONS", opts)
    # The probe will fail (host unroutable), but the endpoint should still 200.
    monkeypatch.setattr(main_mod, "probe_printer", lambda host, port, timeout=2.0: False)

    with TestClient(main_mod.app) as client:
        r = client.get("/api/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["printer_host"] == "10.0.0.99"
    assert data["printer_reachable"] is False


def test_print_shopping_list_route(configured_options, fake_printer):
    with TestClient(main_mod.app) as client:
        r = client.post(
            "/api/print/shopping-list",
            json={
                "aisles": [
                    {
                        "label": "Maitotuotteet",
                        "items": [{"name": "Maito", "amount": 1, "unit": "l"}],
                    }
                ],
                "done_filter": "strike",
            },
        )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["ok"] is True
    assert body["items_printed"] == 1
    out = fake_printer["dummy"].output.decode("cp858", errors="replace")
    assert "Maito" in out
    assert "Maitotuotteet" in out


def test_print_shopping_list_unconfigured_returns_503(monkeypatch):
    opts = Options.load(path="/nonexistent.json")  # all defaults, host is ""
    monkeypatch.setattr(main_mod, "OPTIONS", opts)
    with TestClient(main_mod.app) as client:
        r = client.post("/api/print/shopping-list", json={"aisles": []})
    assert r.status_code == 503
    assert "printer_host" in r.json()["detail"]


def test_print_recipe_route(configured_options, fake_printer):
    img = Image.new("RGB", (100, 50), color=(0, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    image_b64 = base64.b64encode(buf.getvalue()).decode("ascii")

    with TestClient(main_mod.app) as client:
        r = client.post(
            "/api/print/recipe",
            json={
                "recipe": {
                    "name": "Pannukakku",
                    "servings": 6,
                    "ingredients": [{"product_name": "maito", "amount_needed": 5, "unit_abbrev": "dl"}],
                    "instructions": ["Vatkaa.", "Paista."],
                },
                "image_b64": image_b64,
            },
        )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["ok"] is True
    assert body["ingredients_printed"] == 1
    assert body["steps_printed"] == 2
    out = fake_printer["dummy"].output.decode("cp858", errors="replace")
    assert "Pannukakku" in out
    assert "Vatkaa" in out


def test_print_recipe_with_bad_image_b64_still_succeeds(configured_options, fake_printer):
    with TestClient(main_mod.app) as client:
        r = client.post(
            "/api/print/recipe",
            json={
                "recipe": {"name": "X", "ingredients": [], "instructions": []},
                "image_b64": "not-valid-base64!!!",
            },
        )
    # Bad image should be logged and skipped, not 500
    assert r.status_code == 200, r.text
    assert r.json()["ok"] is True
