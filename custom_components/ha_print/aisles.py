"""Finnish grocery-store aisle ordering.

Mirrors `FI_AISLE_ORDER` / `aisleFor()` in
`HA-stock/stock/frontend/src/App.jsx:112-155`.
KEEP IN SYNC if the JS list changes.
"""
from __future__ import annotations

from typing import Any

# (substring_lower, aisle_index, label_finnish)
FI_AISLE_ORDER: list[tuple[str, int, str]] = [
    ("hedelm", 1, "Hedelmät & vihannekset"),
    ("vihannes", 1, "Hedelmät & vihannekset"),
    ("kasvi", 1, "Hedelmät & vihannekset"),
    ("leip", 2, "Leipä & leivonnaiset"),
    ("leivonn", 2, "Leipä & leivonnaiset"),
    ("maito", 3, "Maitotuotteet"),
    ("juusto", 3, "Maitotuotteet"),
    ("jogurt", 3, "Maitotuotteet"),
    ("muna", 3, "Maitotuotteet"),
    ("liha", 4, "Liha & kala"),
    ("kala", 4, "Liha & kala"),
    ("einek", 5, "Eineet"),
    ("valmis", 5, "Eineet"),
    ("pakast", 6, "Pakaste"),
    ("kuiva", 7, "Kuivamuonat"),
    ("mauste", 7, "Kuivamuonat"),
    ("säilyk", 7, "Kuivamuonat"),
    ("sailyk", 7, "Kuivamuonat"),
    ("makeis", 8, "Makeiset & naposteltavat"),
    ("snack", 8, "Makeiset & naposteltavat"),
    ("naposteltav", 8, "Makeiset & naposteltavat"),
    ("juoma", 9, "Juomat"),
    ("kahvi", 9, "Juomat"),
    ("tee", 9, "Juomat"),
    ("olu", 10, "Alkoholi"),
    ("viini", 10, "Alkoholi"),
    ("pesu", 11, "Pesuaineet & kodinhoito"),
    ("siivous", 11, "Pesuaineet & kodinhoito"),
    ("hygien", 12, "Hygienia & kosmetiikka"),
    ("kosmetiik", 12, "Hygienia & kosmetiikka"),
    ("vauva", 13, "Vauva & lemmikki"),
    ("lemmik", 13, "Vauva & lemmikki"),
]
OTHER_AISLE = (99, "Muut")


def aisle_for(group_name: str | None) -> tuple[int, str]:
    """Return (aisle_index, aisle_label) for a product group name."""
    n = (group_name or "").lower()
    if not n:
        return OTHER_AISLE
    for key, idx, label in FI_AISLE_ORDER:
        if key in n:
            return idx, label
    return OTHER_AISLE


def group_items_by_aisle(
    items: list[dict[str, Any]],
    products_by_id: dict[int, dict[str, Any]],
    groups_by_id: dict[int, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Group raw shopping-list rows into aisle buckets ready to POST to HA-print.

    Returns: [{"label": "...", "items": [{name, amount, unit, done, note}, ...]}, ...]
    sorted by aisle index, items sorted with done items at the bottom.
    """
    buckets: dict[int, dict[str, Any]] = {}

    for item in items:
        product = products_by_id.get(int(item.get("product_id") or 0))
        group_name = ""
        if product and product.get("product_group_id") is not None:
            grp = groups_by_id.get(int(product["product_group_id"]))
            if grp:
                group_name = grp.get("name") or ""
        idx, label = aisle_for(group_name)
        if idx not in buckets:
            buckets[idx] = {"idx": idx, "label": label, "items": []}
        name = (product or {}).get("name") or item.get("ha_item_name") or "(item)"
        amount = item.get("amount")
        unit = None
        if product and product.get("qu_id_purchase") is not None:
            # unit is resolved upstream — keep simple here
            unit = None
        buckets[idx]["items"].append(
            {
                "name": name,
                "amount": amount,
                "unit": unit,
                "done": bool(item.get("done")),
                "note": item.get("note"),
                "_group_name": group_name,
            }
        )

    out: list[dict[str, Any]] = []
    for bucket in sorted(buckets.values(), key=lambda b: b["idx"]):
        bucket["items"].sort(
            key=lambda it: (
                1 if it.get("done") else 0,
                it.get("_group_name") or "",
                (it.get("name") or "").lower(),
            )
        )
        # Strip internal sort key before returning
        for it in bucket["items"]:
            it.pop("_group_name", None)
        out.append({"label": bucket["label"], "items": bucket["items"]})
    return out
