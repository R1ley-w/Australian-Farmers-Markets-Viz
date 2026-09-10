#!/usr/bin/env python3
"""
prep_spatial.py — the spatial joins behind the four map idioms.

Reads the ASGS Edition 3 TopoJSON boundary files and the cleaned market list,
and produces:

  data/gccsa_market_density.csv   markets per 100k people, by Greater Capital
                                  City Statistical Area / rest-of-state
  data/lga_distance.csv           distance from each LGA's centre to the
                                  nearest farmers' market ("market deserts")
  data/coverage_curve.csv         share of LGAs and of land area within N km
  data/states.topo.json           trimmed state boundaries for the map base
  data/gccsa.topo.json            trimmed GCCSA boundaries
  data/lga.topo.json              trimmed LGA boundaries

TopoJSON is decoded in pure Python (no geopandas dependency) — the format is
just quantised delta-encoded arcs plus an index, so decoding it is ~40 lines.

Run from the repo root:  python3 scripts/prep_spatial.py
"""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
BOUND = DATA / "boundaries"

EARTH_R = 6371.0088


# --------------------------------------------------------------- topojson

def decode_arcs(topo: dict) -> list[list[tuple[float, float]]]:
    """Undo quantisation and delta encoding, returning absolute lon/lat arcs."""
    tr = topo.get("transform")
    out = []
    for arc in topo["arcs"]:
        pts, x, y = [], 0, 0
        for dx, dy in arc:
            x += dx
            y += dy
            if tr:
                pts.append((x * tr["scale"][0] + tr["translate"][0],
                            y * tr["scale"][1] + tr["translate"][1]))
            else:
                pts.append((x, y))
        out.append(pts)
    return out


def stitch(arc_ids: list[int], arcs) -> list[tuple[float, float]]:
    """Join an arc index list into one ring; negative ids mean reversed."""
    ring: list[tuple[float, float]] = []
    for i in arc_ids:
        a = arcs[~i][::-1] if i < 0 else arcs[i]
        ring.extend(a[1:] if ring else a)
    return ring


def polygons_of(geom: dict, arcs) -> list[list[list[tuple[float, float]]]]:
    """Return a list of polygons; each polygon is [outer_ring, *holes]."""
    t = geom.get("type")
    if t == "Polygon":
        return [[stitch(r, arcs) for r in geom["arcs"]]]
    if t == "MultiPolygon":
        return [[stitch(r, arcs) for r in poly] for poly in geom["arcs"]]
    return []


def load_topo(name: str):
    topo = json.loads((BOUND / name).read_text())
    arcs = decode_arcs(topo)
    (obj_name, obj), = topo["objects"].items()
    feats = []
    for g in obj["geometries"]:
        polys = polygons_of(g, arcs)
        if polys:
            feats.append({"props": g.get("properties", {}), "polys": polys})
    return topo, obj_name, feats


# ----------------------------------------------------------------- geometry

def point_in_ring(x: float, y: float, ring) -> bool:
    inside = False
    n = len(ring)
    for i in range(n):
        x1, y1 = ring[i]
        x2, y2 = ring[(i + 1) % n]
        if (y1 > y) != (y2 > y):
            xin = (x2 - x1) * (y - y1) / (y2 - y1) + x1
            if x < xin:
                inside = not inside
    return inside


def point_in_polys(x: float, y: float, polys) -> bool:
    for rings in polys:
        if point_in_ring(x, y, rings[0]) and not any(
                point_in_ring(x, y, h) for h in rings[1:]):
            return True
    return False


def bbox(polys):
    xs = [p[0] for rings in polys for r in rings for p in r]
    ys = [p[1] for rings in polys for r in rings for p in r]
    return min(xs), min(ys), max(xs), max(ys)


def ring_area_centroid(ring):
    """Planar signed area and centroid of a ring (good enough at this scale)."""
    a = cx = cy = 0.0
    n = len(ring)
    for i in range(n):
        x1, y1 = ring[i]
        x2, y2 = ring[(i + 1) % n]
        f = x1 * y2 - x2 * y1
        a += f
        cx += (x1 + x2) * f
        cy += (y1 + y2) * f
    if a == 0:
        return 0.0, ring[0]
    return a / 2, (cx / (3 * a), cy / (3 * a))


def centroid_of(polys):
    """Area-weighted centroid, nudged inside the shape if it lands outside."""
    tot = 0.0
    sx = sy = 0.0
    for rings in polys:
        a, (cx, cy) = ring_area_centroid(rings[0])
        a = abs(a)
        tot += a
        sx += cx * a
        sy += cy * a
    if tot == 0:
        return polys[0][0][0]
    c = (sx / tot, sy / tot)
    if point_in_polys(c[0], c[1], polys):
        return c
    # concave shape: fall back to the vertex of the largest ring nearest the
    # centroid, which is always on the boundary and therefore inside the region
    big = max((r[0] for r in polys), key=lambda r: abs(ring_area_centroid(r)[0]))
    return min(big, key=lambda p: (p[0] - c[0]) ** 2 + (p[1] - c[1]) ** 2)


def haversine(lat1, lon1, lat2, lon2) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * EARTH_R * math.asin(math.sqrt(a))


def nearest_market(lat, lng, markets):
    """Nearest market by great-circle distance, with a cheap bbox prefilter."""
    best, best_m = float("inf"), None
    coslat = math.cos(math.radians(lat))
    for m in markets:
        # planar pre-check in degrees, converted to an optimistic km bound
        dy = (m["lat"] - lat) * 111.32
        dx = (m["lng"] - lng) * 111.32 * coslat
        if dx * dx + dy * dy > best * best:
            continue
        d = haversine(lat, lng, m["lat"], m["lng"])
        if d < best:
            best, best_m = d, m
    return best, best_m


def trim(path_in: Path, path_out: Path, keep: dict[str, str], drop_codes=()):
    """Rewrite a TopoJSON keeping only the properties the charts need."""
    topo = json.loads(path_in.read_text())
    for obj in topo["objects"].values():
        geoms = []
        for g in obj["geometries"]:
            p = g.get("properties", {})
            code = next((p.get(k) for k in keep if k.endswith("CODE21")
                         or k.endswith("CODE23")), None)
            if code in drop_codes or not g.get("arcs"):
                continue
            g["properties"] = {new: p.get(old) for old, new in keep.items() if old in p}
            geoms.append(g)
        obj["geometries"] = geoms
    path_out.write_text(json.dumps(topo, separators=(",", ":")))
    return sum(len(o["geometries"]) for o in topo["objects"].values())


# --------------------------------------------------------------------- main

def main() -> None:
    markets = [
        {"name": r["name"], "lat": float(r["lat"]), "lng": float(r["lng"]),
         "state": r["state"]}
        for r in csv.DictReader((DATA / "markets.csv").open())
        if r["is_duplicate"] == "0" and r["geocode_ok"] == "1"
    ]
    print(f"{len(markets)} markets with usable coordinates")

    pop = list(csv.DictReader((DATA / "abs_population_2025.csv").open()))
    state_pop = {r["state"]: int(r["erp"]) for r in pop if r["region_type"] == "STE"}
    capital_pop = {r["region"]: int(r["erp"]) for r in pop if r["region_type"] == "GCCSA"}

    # -------------------------------------------------- GCCSA market density
    # STE code 9 is "Other Territories" (Christmas Island, Cocos, Jervis Bay);
    # it has no farmers' markets and no matching ERP row, so it is excluded.
    STATE_OF = {"1": "NSW", "2": "VIC", "3": "QLD", "4": "SA",
                "5": "WA", "6": "TAS", "7": "NT", "8": "ACT"}
    CAPITAL_OF = {"NSW": "Greater Sydney", "VIC": "Greater Melbourne",
                  "QLD": "Greater Brisbane", "SA": "Greater Adelaide",
                  "WA": "Greater Perth", "TAS": "Greater Hobart",
                  "NT": "Greater Darwin", "ACT": "Australian Capital Territory"}

    _, _, gccsa = load_topo("GCCSA_2021_AUST_GDA2020.json")
    gccsa = [f for f in gccsa
             if f["props"].get("STE_CODE21") in STATE_OF
             and not f["props"]["GCC_NAME21"].startswith(
                 ("No usual address", "Migratory", "Outside"))]

    # rest-of-state population = state total - capital city
    region_pop = {}
    for f in gccsa:
        name, st = f["props"]["GCC_NAME21"], STATE_OF[f["props"]["STE_CODE21"]]
        region_pop[name] = (capital_pop[name] if name in capital_pop
                            else state_pop[st] - capital_pop[CAPITAL_OF[st]])

    # assign each market to a GCCSA by point-in-polygon
    boxes = [(f, bbox(f["polys"])) for f in gccsa]
    counts: dict[str, int] = {f["props"]["GCC_NAME21"]: 0 for f in gccsa}
    unassigned = 0
    for m in markets:
        hit = None
        for f, (x0, y0, x1, y1) in boxes:
            if x0 <= m["lng"] <= x1 and y0 <= m["lat"] <= y1 and \
                    point_in_polys(m["lng"], m["lat"], f["polys"]):
                hit = f["props"]["GCC_NAME21"]
                break
        if not hit:
            # Coastal markets can fall just outside a simplified boundary.
            # Assign them to the nearest region centre rather than dropping them.
            unassigned += 1
            hit = min(gccsa, key=lambda f: haversine(
                m["lat"], m["lng"], *reversed(centroid_of(f["polys"]))
            ))["props"]["GCC_NAME21"]
        counts[hit] += 1
    print(f"{unassigned} markets fell outside every GCCSA polygon "
          f"(simplified boundaries) and were snapped to the nearest region")

    rows = []
    for f in gccsa:
        name = f["props"]["GCC_NAME21"]
        p = region_pop.get(name, 0)
        n = counts[name]
        # Capital cities are slivers at national scale, so the map draws them as
        # circles at their centre rather than as fills nobody can see.
        clng, clat = centroid_of(f["polys"])
        rows.append({
            "gccsa_code": f["props"]["GCC_CODE21"],
            "gccsa": name,
            "state": STATE_OF[f["props"]["STE_CODE21"]],
            "kind": "Capital city" if name.startswith("Greater")
                    or name == "Australian Capital Territory" else "Rest of state",
            "markets": n,
            "population": p,
            "markets_per_100k": round(n / p * 100_000, 3) if p else 0,
            "area_sqkm": round(f["props"].get("AREASQKM21") or 0, 1),
            "lat": round(clat, 4),
            "lng": round(clng, 4),
        })
    rows.sort(key=lambda r: -r["markets_per_100k"])
    write_csv(DATA / "gccsa_market_density.csv", rows)

    # ------------------------------------------------ LGA distance to market
    _, _, lgas = load_topo("LGA_2023_AUST_GDA2020.json")
    lga_rows = []
    for f in lgas:
        p = f["props"]
        name = p.get("LGA_NAME23") or ""
        # Other Territories (STE code 9) — Christmas Is., Cocos, Jervis Bay —
        # are thousands of km offshore and would dominate the distance scale.
        if (not name or p.get("STE_CODE21") not in STATE_OF
                or name.startswith(("No usual address", "Migratory",
                                    "Unincorporated (Other"))):
            continue
        lng, lat = centroid_of(f["polys"])
        d, nm = nearest_market(lat, lng, markets)
        lga_rows.append({
            "lga_code": p["LGA_CODE23"],
            "lga": name,
            "state": STATE_OF.get(p.get("STE_CODE21"), ""),
            "lat": round(lat, 5),
            "lng": round(lng, 5),
            "area_sqkm": round(p.get("AREASQKM") or 0, 1),
            "km_to_nearest_market": round(d, 1),
            "nearest_market": nm["name"] if nm else "",
        })
    lga_rows.sort(key=lambda r: r["km_to_nearest_market"])
    write_csv(DATA / "lga_distance.csv", lga_rows)

    # ------------------------------------------------------- coverage curve
    total_area = sum(r["area_sqkm"] for r in lga_rows)
    curve = []
    for km in list(range(0, 101, 5)) + [125, 150, 200, 300, 500, 1000]:
        within = [r for r in lga_rows if r["km_to_nearest_market"] <= km]
        curve.append({
            "km": km,
            "lgas_within": len(within),
            "pct_lgas": round(len(within) / len(lga_rows) * 100, 1),
            "pct_land_area": round(sum(r["area_sqkm"] for r in within) / total_area * 100, 1),
        })
    write_csv(DATA / "coverage_curve.csv", curve)

    # ------------------------------------------------------- trimmed basemaps
    n = trim(BOUND / "STE_2021_AUST_GDA2020.json", DATA / "states.topo.json",
             {"STE_CODE21": "code", "STE_NAME21": "name"}, drop_codes=("9", "Z"))
    print(f"states.topo.json      {n} features")
    # Other Territories (Christmas Is., Cocos, Jervis Bay) have no ERP row and
    # no markets, so they are dropped rather than drawn as an unfilled hole.
    n = trim(BOUND / "GCCSA_2021_AUST_GDA2020.json", DATA / "gccsa.topo.json",
             {"GCC_CODE21": "code", "GCC_NAME21": "name", "STE_NAME21": "state"},
             drop_codes=("9OTER", "99499", "99799"))
    print(f"gccsa.topo.json       {n} features")
    n = trim(BOUND / "LGA_2023_AUST_GDA2020.json", DATA / "lga.topo.json",
             {"LGA_CODE23": "code", "LGA_NAME23": "name", "STE_NAME21": "state"},
             drop_codes=tuple(
                 g["props"]["LGA_CODE23"] for g in lgas
                 if g["props"].get("STE_CODE21") not in STATE_OF))
    print(f"lga.topo.json         {n} features")

    print(f"\n{len(lga_rows)} LGAs; median distance to a market "
          f"{sorted(r['km_to_nearest_market'] for r in lga_rows)[len(lga_rows)//2]:.0f} km")


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    main()
