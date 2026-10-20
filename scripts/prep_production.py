"""prep_production.py — ABS agricultural production for Section 3.

"""

import csv
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SRC = DATA / "VACPDCLGA202021.xlsx"
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def read_table(path):
    """Rows of 'Table 1' as dicts: region_code, region, code, desc, gross."""
    z = zipfile.ZipFile(path)
    strings = [
        "".join(t.text or "" for t in si.iter("{%s}t" % NS["m"]))
        for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", NS)
    ]
    # Locate the sheet named "Table 1" through the workbook relationships.
    wb = ET.fromstring(z.read("xl/workbook.xml"))
    rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    rid = next(s.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id")
               for s in wb.iter("{%s}sheet" % NS["m"]) if s.get("name") == "Table 1")
    target = next(r.get("Target") for r in rels if r.get("Id") == rid)
    sheet = ET.fromstring(z.read("xl/" + target.lstrip("/").replace("xl/", "")))

    out = []
    for row in sheet.iter("{%s}row" % NS["m"]):
        cells = {}
        for c in row.findall("m:c", NS):
            v = c.find("m:v", NS)
            if v is None:
                continue
            col = "".join(ch for ch in c.get("r") if ch.isalpha())
            cells[col] = strings[int(v.text)] if c.get("t") == "s" else v.text
        code = cells.get("A", "").strip()
        if not code.isdigit() or not cells.get("C", "").isdigit():
            continue  # title rows, header, footnotes
        out.append({
            "region_code": code,
            "region": cells.get("B", "").strip(),
            "code": cells["C"],
            "desc": cells.get("D", "").strip(),
            "gross": float(cells.get("E") or 0),
        })
    return out


# ------------------------------------------------------------------ tree
# Category -> leaves. Each leaf: (ABS commodity code, display name, map key).
# The map key is the map's commodity option a click on that tile selects.
# Categories follow the ABS groupings, re-labelled in plain language
# ("Livestock slaughtered and other disposals" is meat).
TREE = [
    ("Meat", "meat", [
        ("9100158", "Cattle (beef)", "cattle"),
        ("9100258", "Sheep and lambs", "sheep"),
        ("9100658", "Poultry (chicken)", "poultry"),
        ("9100358", "Pigs (pork)", "pigs"),
        ("9100916", "Other livestock", "meat"),
    ]),
    ("Grains and hay", "broadacre", [
        ("1500158", "Wheat", "broadacre"),
        ("1501758", "Barley", "broadacre"),
        ("1900958", "Canola", "broadacre"),
        ("1803258", "Cotton", "broadacre"),
        ("1902158", "Sugar cane", "broadacre"),
        ("1905258", "Lentils", "broadacre"),
        ("1901916", "Other pulses", "broadacre"),
        ("1500858", "Oats", "broadacre"),
        ("1504158", "Sorghum", "broadacre"),
        ("1900358", "Chickpeas", "broadacre"),
        ("1807058", "Lupins", "broadacre"),
        ("1510458", "Other crops", "broadacre"),
        ("1508558", "Rice", "broadacre"),
        ("1505358", "Maize", "broadacre"),
        ("1901716", "Other oilseeds", "broadacre"),
        ("1510316", "Other cereals", "broadacre"),
        ("3307859", "Hay", "hay"),
    ]),
    ("Fruit and nuts", "fruit_nuts", [
        ("5109958", "Wine grapes", "grapes"),
        ("4800558", "Table and dried grapes", "grapes"),
        ("4202258", "Apples", "fruit_nuts"),
        ("4304658", "Bananas", "fruit_nuts"),
        ("4200758", "Oranges", "fruit_nuts"),
        ("4208158", "Almonds", "fruit_nuts"),
        ("4302558", "Other berries", "fruit_nuts"),
        ("4201458", "Mandarins", "fruit_nuts"),
        ("4302258", "Strawberries", "fruit_nuts"),
        ("4204158", "Avocados", "fruit_nuts"),
        ("4209058", "Macadamias", "fruit_nuts"),
        ("4204358", "Cherries", "fruit_nuts"),
        ("4201658", "Other citrus", "fruit_nuts"),
        ("4205358", "Mangoes", "fruit_nuts"),
        ("4205558", "Nectarines", "fruit_nuts"),
        ("4209758", "Other nuts", "fruit_nuts"),
        ("4205758", "Olives", "fruit_nuts"),
        ("4207858", "Other orchard fruit", "fruit_nuts"),
        ("4207358", "Other stone fruit", "fruit_nuts"),
        ("4307058", "Other fruit", "fruit_nuts"),
        ("4202658", "Pears", "fruit_nuts"),
        ("4206258", "Peaches", "fruit_nuts"),
        ("4306058", "Pineapples", "fruit_nuts"),
    ]),
    ("Milk, eggs and wool", "livestock_products", [
        ("9200258", "Milk", "milk"),
        ("9200159", "Wool", "wool"),
        ("9200348", "Eggs", "eggs"),
    ]),
    ("Vegetables", "vegetables", [
        ("3630016", "Other vegetables", "vegetables"),
        ("3505958", "Potatoes", "vegetables"),
        ("3608858", "Tomatoes", "vegetables"),
        ("3605858", "Mushrooms", "vegetables"),
        ("3602458", "Carrots", "vegetables"),
        ("3611758", "Sweet corn", "vegetables"),
        ("3610658", "Lettuces", "vegetables"),
        ("3604258", "Herbs", "vegetables"),
        ("3614058", "Melons", "vegetables"),
        ("3601358", "Beans", "vegetables"),
        ("3611558", "Onions", "vegetables"),
        ("3613658", "Capsicums", "vegetables"),
        ("3601758", "Broccoli", "vegetables"),
        ("3603258", "Cucumbers", "vegetables"),
        ("3607158", "Pumpkins", "vegetables"),
        ("3601958", "Cabbages", "vegetables"),
        ("3602758", "Cauliflowers", "vegetables"),
    ]),
    ("Nurseries and flowers", "nurseries", [
        ("1919259", "Nurseries", "nurseries"),
        ("1908558", "Turf", "nurseries"),
        ("1919459", "Cut flowers", "nurseries"),
    ]),
]
TOTAL_CODE = "9019959"

# ------------------------------------------------------------------- map
# Map commodity options -> the ABS aggregate code for that option.
MAP_COLS = [
    ("total", TOTAL_CODE),
    ("broadacre", "1910758"),
    ("hay", "3307859"),
    ("fruit_nuts", "4309359"),   # excludes grapes, as ABS publishes it
    ("grapes", "5110058"),
    ("vegetables", "3630059"),
    ("meat", "9015959"),
    ("cattle", "9100158"),
    ("sheep", "9100258"),
    ("pigs", "9100358"),
    ("poultry", "9100658"),
    ("livestock_products", "9017959"),
    ("milk", "9200258"),
    ("eggs", "9200348"),
    ("wool", "9200159"),
    ("nurseries", "1919559"),
]
# Each council's main type of produce, for the symbol shape on the map. Six
# types, the categories of the treemap with hay folded into grains and grapes
# into fruit (single-commodity categories would otherwise get a shape each).
MAIN_TYPES = [
    ("Meat", ["9015959"]),
    ("Grains and hay", ["1910758", "3307859"]),
    ("Milk, eggs and wool", ["9017959"]),
    ("Fruit and nuts", ["4309359", "5110058"]),
    ("Vegetables", ["3630059"]),
    ("Nurseries and flowers", ["1919559"]),
]

STATES = {"1": "NSW", "2": "VIC", "3": "QLD", "4": "SA",
          "5": "WA", "6": "TAS", "7": "NT", "8": "ACT", "9": "OT"}


def main():
    rows = read_table(SRC)
    nat = {r["code"]: r["gross"] for r in rows if r["region_code"] == "0"}

    # ---- tree
    tree = [("root", "", "Australian agriculture", "", "", "")]
    leaf_sum = 0.0
    for cat, cat_key, leaves in TREE:
        cid = "c:" + cat_key
        tree.append((cid, "root", cat, cat, "", cat_key))
        for code, name, key in leaves:
            v = nat[code]
            leaf_sum += v
            tree.append(("l:" + code, cid, name, cat, f"{v:.0f}", key))
    total = nat[TOTAL_CODE]
    gap = abs(leaf_sum - total) / total
    print(f"tree: {len(tree)} nodes, leaves sum {leaf_sum/1e6:,.0f}m "
          f"vs total {total/1e6:,.0f}m ({gap:.4%} apart)")
    if gap > 0.001:
        sys.exit("tree leaves do not add up to total agriculture — check TREE")

    with open(DATA / "abs_production_tree.csv", "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["id", "parent", "name", "category", "value", "map_key"])
        w.writerows(tree)

    # ---- LGA wide table
    area = {}
    with open(DATA / "lga_distance.csv", newline="") as f:
        for r in csv.DictReader(f):
            area[r["lga_code"]] = float(r["area_sqkm"])

    lga = {}
    for r in rows:
        if len(r["region_code"]) != 5:     # 0 = Australia, 1-8 = states
            continue
        d = lga.setdefault(r["region_code"], {"name": r["region"]})
        d[r["code"]] = r["gross"]

    # LGA codes changed between the 2021 edition (ABS file) and the 2023
    # boundaries the maps use. Only one affects a council with data.
    RENAMED = {"25250": "24700"}   # Moreland -> Merri-bek (renamed 2022)
    for old, new in RENAMED.items():
        if old in lga:
            lga[new] = lga.pop(old)
            lga[new]["name"] = "Merri-bek"

    missing_area = sorted(f"{c} {d['name']}" for c, d in lga.items() if c not in area)
    print(f"LGAs in ABS file: {len(lga)}; without a 2023 boundary/area: "
          f"{len(missing_area)}")
    for m in missing_area:
        print("   no boundary:", m)

    with open(DATA / "abs_production_lga.csv", "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["lga_code", "lga", "state", "area_sqkm", "main_type", "main_share"] +
                   [k for k, _ in MAP_COLS])
        for c in sorted(lga):
            if c not in area:
                continue
            d = lga[c]
            by_type = {t: sum(d.get(code, 0) for code in codes) for t, codes in MAIN_TYPES}
            whole = sum(by_type.values())
            main = max(by_type, key=by_type.get) if whole > 0 else ""
            share = f"{by_type[main] / whole:.3f}" if whole > 0 else ""
            w.writerow([c, d["name"], STATES[c[0]], f"{area[c]:.1f}", main, share] +
                       [f"{d.get(code, 0):.0f}" for _, code in MAP_COLS])

    # How much of each national total the LGA rows can show. The rest is
    # suppressed at SA2 level and appears nowhere on the map.
    print("\nshare of national value visible at LGA level:")
    for key, code in MAP_COLS:
        s = sum(d.get(code, 0) for c, d in lga.items() if c in area)
        print(f"   {key:<20} {s / nat[code]:6.1%}")


if __name__ == "__main__":
    main()
