"""ha_print.shopping_list rows: units and quantity text from Storage, aisle
order mirrored from HA-stock — pure, no Home Assistant import."""
from __future__ import annotations

import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "ha_print_aisles", Path(__file__).resolve().parents[1] / "custom_components/ha_print/aisles.py")
aisles = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(aisles)

GROUPS = {1: {"id": 1, "name": "Maitotuotteet"}, 2: {"id": 2, "name": "Juurekset"},
          3: {"id": 3, "name": "Vauvanhoito"}}


def _group(rows, products):
    return aisles.group_items_by_aisle(rows, {p["id"]: p for p in products}, GROUPS)


def test_rows_carry_storage_unit_and_quantity_text():
    products = [{"id": 10, "name": "Kerma", "product_group_id": 1}]
    rows = [{"id": 1, "product_id": 10, "amount": 3.5, "done": False, "note": "Reseptistä: Kastike",
             "display": {"qty_text": "3,5 dl", "unit_abbr": "dl", "unit_dimension": "volume"}}]
    [aisle] = _group(rows, products)
    assert aisle["items"] == [{"name": "Kerma", "amount": 3.5, "unit": "dl", "qty_text": "3,5 dl",
                               "done": False, "note": "Reseptistä: Kastike"}]


def test_note_rows_print_the_note_as_the_name():
    products = [{"id": 11, "name": "Muistilappu"}]
    rows = [{"id": 2, "product_id": 11, "amount": 1, "done": False, "note": "Synttärikakku",
             "display": {"qty_text": "1", "unit_abbr": None, "unit_dimension": "package"}}]
    [aisle] = _group(rows, products)
    assert aisle["items"] == [{"name": "Synttärikakku", "amount": 1, "unit": None, "qty_text": None,
                               "done": False, "note": None}]


def test_aisle_order_follows_ha_stock():
    assert aisles.aisle_for("Perunat") == (1, "Hedelmät & vihannekset")
    assert aisles.aisle_for("Kananmunat") == (3, "Maitotuotteet")
    assert aisles.aisle_for("Lastenpyyhe") == (13, "Vauva & lemmikki")  # baby before hygiene
    assert aisles.aisle_for("Käsipyyhe") == (12, "Hygienia & kosmetiikka")
    assert len(aisles.FI_AISLE_ORDER) == 116


def test_a_generic_row_prints_the_product_to_buy_in_its_aisle():
    products = [{"id": 20, "name": "Crème fraîche", "kind": "concept", "product_group_id": 2},
                {"id": 21, "name": "Pirkka creme fraiche 150g", "product_group_id": 1}]
    rows = [{"id": 3, "product_id": 20, "amount": 1, "done": False, "note": "",
             "display": {"qty_text": "1", "unit_abbr": None, "unit_dimension": "package",
                         "buy_product_id": 21, "buy_product_name": "Pirkka creme fraiche 150g"}}]
    [aisle] = _group(rows, products)
    assert aisle["label"] == aisles.aisle_for("Maitotuotteet")[1]
    assert aisle["items"][0]["name"] == "Pirkka creme fraiche 150g"


def test_a_generic_row_without_a_pick_prints_the_generic_name():
    products = [{"id": 22, "name": "Juustokreemi", "kind": "concept", "product_group_id": 1}]
    rows = [{"id": 4, "product_id": 22, "amount": 1, "done": False, "note": "",
             "display": {"qty_text": "1", "unit_abbr": None, "unit_dimension": "package",
                         "buy_product_id": None, "buy_product_name": None}}]
    [aisle] = _group(rows, products)
    assert aisle["items"][0]["name"] == "Juustokreemi"
