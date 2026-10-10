"""Finnish grocery-store aisle ordering.

Mirrors `FI_AISLE_ORDER` / `aisleFor()` in HA-stock's
`stock/frontend/src/App.jsx`, entry for entry and in the same order (first
substring hit wins). KEEP IN SYNC if the JS list changes.
"""
from __future__ import annotations

from typing import Any

# The shopping-list product HA-stock keeps free-text notes under; such a row
# prints its note as the item name (as HA-stock's own print does).
NOTE_SENTINEL_NAME = "Muistilappu"

# (substring_lower, aisle_index, label_finnish)
FI_AISLE_ORDER: list[tuple[str, int, str]] = [
    # 1 — Hedelmät & vihannekset
    ("hedelm", 1, "Hedelmät & vihannekset"),
    ("vihannes", 1, "Hedelmät & vihannekset"),
    ("kasvi", 1, "Hedelmät & vihannekset"),
    ("juures", 1, "Hedelmät & vihannekset"),
    ("peruna", 1, "Hedelmät & vihannekset"),
    ("salaat", 1, "Hedelmät & vihannekset"),
    ("marja", 1, "Hedelmät & vihannekset"),
    ("sieni", 1, "Hedelmät & vihannekset"),
    ("yrt", 1, "Hedelmät & vihannekset"),
    # 2 — Leipä & leivonnaiset
    ("leip", 2, "Leipä & leivonnaiset"),
    ("leivonn", 2, "Leipä & leivonnaiset"),
    ("sämpyl", 2, "Leipä & leivonnaiset"),
    ("sampyl", 2, "Leipä & leivonnaiset"),
    ("pulla", 2, "Leipä & leivonnaiset"),
    ("keksi", 2, "Leipä & leivonnaiset"),
    # 3 — Maitotuotteet (muna must come before kana in aisle 4)
    ("maito", 3, "Maitotuotteet"),
    ("juusto", 3, "Maitotuotteet"),
    ("jogurt", 3, "Maitotuotteet"),
    ("rahka", 3, "Maitotuotteet"),
    ("viili", 3, "Maitotuotteet"),
    ("kerma", 3, "Maitotuotteet"),
    ("margar", 3, "Maitotuotteet"),
    ("levite", 3, "Maitotuotteet"),
    ("voi ", 3, "Maitotuotteet"),
    ("muna", 3, "Maitotuotteet"),
    # 4 — Liha & kala
    ("liha", 4, "Liha & kala"),
    ("kala", 4, "Liha & kala"),
    ("kana", 4, "Liha & kala"),
    ("broiler", 4, "Liha & kala"),
    ("kalkku", 4, "Liha & kala"),
    ("makkar", 4, "Liha & kala"),
    ("nakki", 4, "Liha & kala"),
    ("leikkele", 4, "Liha & kala"),
    ("jauheli", 4, "Liha & kala"),
    ("äyriäi", 4, "Liha & kala"),
    ("ayriai", 4, "Liha & kala"),
    # 5 — Eineet (valmiit ateriat / ready meals)
    ("einek", 5, "Eineet"),
    ("eines", 5, "Eineet"),
    ("valmis", 5, "Eineet"),
    ("pizz", 5, "Eineet"),
    ("lasagne", 5, "Eineet"),
    ("keitto", 5, "Eineet"),
    # 6 — Pakaste (jäätelö belongs here in Finnish stores)
    ("pakast", 6, "Pakaste"),
    ("jäätel", 6, "Pakaste"),
    ("jaatel", 6, "Pakaste"),
    # 7 — Kuivamuonat
    ("kuiva", 7, "Kuivamuonat"),
    ("mauste", 7, "Kuivamuonat"),
    ("säilyk", 7, "Kuivamuonat"),
    ("sailyk", 7, "Kuivamuonat"),
    ("pasta", 7, "Kuivamuonat"),
    ("riisi", 7, "Kuivamuonat"),
    ("jauho", 7, "Kuivamuonat"),
    ("sokeri", 7, "Kuivamuonat"),
    ("suola", 7, "Kuivamuonat"),
    ("murot", 7, "Kuivamuonat"),
    ("mysli", 7, "Kuivamuonat"),
    ("hiutal", 7, "Kuivamuonat"),
    ("kastike", 7, "Kuivamuonat"),
    ("liemi", 7, "Kuivamuonat"),
    ("öljy", 7, "Kuivamuonat"),
    ("oljy", 7, "Kuivamuonat"),
    ("etikk", 7, "Kuivamuonat"),
    ("höyste", 7, "Kuivamuonat"),
    ("hoyste", 7, "Kuivamuonat"),
    ("pavut", 7, "Kuivamuonat"),
    ("linss", 7, "Kuivamuonat"),
    # 8 — Makeiset & naposteltavat
    ("makeis", 8, "Makeiset & naposteltavat"),
    ("snack", 8, "Makeiset & naposteltavat"),
    ("naposteltav", 8, "Makeiset & naposteltavat"),
    ("suklaa", 8, "Makeiset & naposteltavat"),
    ("karkki", 8, "Makeiset & naposteltavat"),
    ("lakri", 8, "Makeiset & naposteltavat"),
    ("sipsi", 8, "Makeiset & naposteltavat"),
    ("pähkin", 8, "Makeiset & naposteltavat"),
    ("pahkin", 8, "Makeiset & naposteltavat"),
    ("purkka", 8, "Makeiset & naposteltavat"),
    # 9 — Juomat
    ("juoma", 9, "Juomat"),
    ("kahvi", 9, "Juomat"),
    ("tee", 9, "Juomat"),
    ("mehu", 9, "Juomat"),
    ("virvoit", 9, "Juomat"),
    ("limonad", 9, "Juomat"),
    ("kivenn", 9, "Juomat"),
    # 10 — Alkoholi
    ("olu", 10, "Alkoholi"),
    ("viini", 10, "Alkoholi"),
    ("alkoho", 10, "Alkoholi"),
    ("lonkero", 10, "Alkoholi"),
    ("siideri", 10, "Alkoholi"),
    ("viski", 10, "Alkoholi"),
    ("vodka", 10, "Alkoholi"),
    # 11 — Pesuaineet & kodinhoito  (use 'kodinh', not 'koti', to avoid 'kotimain*')
    ("pesu", 11, "Pesuaineet & kodinhoito"),
    ("siivous", 11, "Pesuaineet & kodinhoito"),
    ("puhdist", 11, "Pesuaineet & kodinhoito"),
    ("pyyk", 11, "Pesuaineet & kodinhoito"),
    ("astian", 11, "Pesuaineet & kodinhoito"),
    ("kodinh", 11, "Pesuaineet & kodinhoito"),
    # 13 — Vauva & lemmikki  (listed BEFORE aisle 12 so 'vauva'/'lasten' wins
    # over 'vaippa'/'pyyhe' for products like "Vauvanvaipat", "Lastenpyyhkeet")
    ("vauva", 13, "Vauva & lemmikki"),
    ("lemmik", 13, "Vauva & lemmikki"),
    ("lasten", 13, "Vauva & lemmikki"),
    ("lapsi", 13, "Vauva & lemmikki"),
    ("koira", 13, "Vauva & lemmikki"),
    ("kissa", 13, "Vauva & lemmikki"),
    ("eläin", 13, "Vauva & lemmikki"),
    ("elain", 13, "Vauva & lemmikki"),
    # 12 — Hygienia & kosmetiikka
    ("hygien", 12, "Hygienia & kosmetiikka"),
    ("kosmetiik", 12, "Hygienia & kosmetiikka"),
    ("sham", 12, "Hygienia & kosmetiikka"),
    ("saippua", 12, "Hygienia & kosmetiikka"),
    ("hammas", 12, "Hygienia & kosmetiikka"),
    ("terveys", 12, "Hygienia & kosmetiikka"),
    ("vitamii", 12, "Hygienia & kosmetiikka"),
    ("lääke", 12, "Hygienia & kosmetiikka"),
    ("laake", 12, "Hygienia & kosmetiikka"),
    ("paperi", 12, "Hygienia & kosmetiikka"),
    ("pyyhe", 12, "Hygienia & kosmetiikka"),
    ("vaippa", 12, "Hygienia & kosmetiikka"),
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

    Returns: [{"label": "...", "items": [{name, amount, unit, qty_text, done, note}, ...]}, ...]
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
        display = item.get("display") or {}
        if (product or {}).get("name") == NOTE_SENTINEL_NAME:
            name, unit, qty_text, note = item.get("note") or NOTE_SENTINEL_NAME, None, None, None
        else:
            name = (product or {}).get("name") or item.get("ha_item_name") or "(item)"
            # Storage's display block: "3,5 dl" for a recipe need, "2" for packages.
            unit, qty_text, note = display.get("unit_abbr"), display.get("qty_text"), item.get("note")
        buckets[idx]["items"].append(
            {
                "name": name,
                "amount": item.get("amount"),
                "unit": unit,
                "qty_text": qty_text,
                "done": bool(item.get("done")),
                "note": note,
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
