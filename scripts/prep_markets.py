#!/usr/bin/env python3
"""
prep_markets.py — clean the scraped AFMA directory into analysis-ready files.

Input   data/afma_markets_raw.tsv   (178 records scraped from the AFMA
        "Find a Market" WP Store Locator endpoint, 10 Sep 2026)

Output  data/markets.csv            one row per market, cleaned + derived fields
        data/markets_by_state.csv   counts and rates by state
        data/frequency_by_state.csv frequency x state, long form
        data/day_time_heatmap.csv   opening day x start hour
        data/operators.csv          operator -> market count
        data/data_quality.csv       issues found, for the write-up

Run from the repo root:  python3 scripts/prep_markets.py
"""

from __future__ import annotations

import csv
import math
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday",
        "Friday", "Saturday", "Sunday"]


#  helpers #


def norm(s: str) -> str:
    """Normalise a name for duplicate detection."""
    s = unicodedata.normalize("NFKD", s or "")
    s = s.replace("’", "'").lower()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    s = re.sub(r"\b(farmers?|growers?|producers?|market|markets|the|and|community)\b", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def parse_time(t: str) -> float | None:
    """'8:30 AM' -> 8.5 (hours after midnight)."""
    if not t:
        return None
    m = re.match(r"\s*(\d{1,2})(?::(\d{2}))?\s*([AaPp])\.?[Mm]", t)
    if not m:
        return None
    h = int(m.group(1)) % 12
    mins = int(m.group(2) or 0)
    if m.group(3).lower() == "p":
        h += 12
    return h + mins / 60


def frequency_of(market_days: str) -> str:
    """Classify the free-text market_days field into a trading frequency."""
    s = (market_days or "").lower().replace("ist", "1st")
    if not s.strip():
        return "Unknown"
    if re.search(r"various|contact manager|by arrangement", s):
        return "Irregular"
    # count how many ordinal week markers appear ("1st & 3rd" -> 2 per month)
    ordinals = set(re.findall(r"(1st|2nd|3rd|4th|5th|last|first|second|third|fourth)", s))
    weekly = bool(re.search(r"\bevery\b", s)) or bool(
        re.search(r"(monday|tuesday|wednesday|thursday|friday|saturday|sunday)s\b", s)
    )
    if weekly and not ordinals:
        return "Weekly"
    if len(ordinals) >= 2:
        return "Fortnightly"
    if len(ordinals) == 1:
        return "Monthly"
    # bare "Saturday" with no qualifier: the directory uses this for weekly markets
    if re.search(r"(monday|tuesday|wednesday|thursday|friday|saturday|sunday)", s):
        return "Weekly"
    return "Unknown"


def trading_day(market_days: str, hours_day: str) -> str:
    """Prefer the day named in market_days; fall back to the opening-hours table."""
    s = (market_days or "").lower()
    for d in DAYS:
        if d.lower() in s:
            return d
    for d in DAYS:
        if d.lower() in (hours_day or "").lower():
            return d
    return "Unknown"


def markets_per_month(freq: str) -> float:
    return {"Weekly": 4.33, "Fortnightly": 2.0, "Monthly": 1.0,
            "Irregular": 0.5, "Unknown": 1.0}[freq]


def haversine(lat1, lon1, lat2, lon2) -> float:
    """Great-circle distance in km."""
    r = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


# Rough state bounding boxes, used only to catch obviously wrong geocodes. 
STATE_BOX = {
    "NSW": (-37.6, -28.1, 140.9, 153.7),
    "VIC": (-39.2, -33.9, 140.9, 150.1),
    "QLD": (-29.2, -9.0, 137.9, 153.6),
    "SA":  (-38.2, -25.9, 129.0, 141.1),
    "WA":  (-35.2, -13.6, 112.9, 129.1),
    "TAS": (-43.7, -39.1, 143.8, 148.6),
    "NT":  (-26.1, -10.9, 128.9, 138.1),
    "ACT": (-35.95, -35.1, 148.7, 149.5),
}


def main() -> None:
    rows = list(csv.DictReader((DATA / "afma_markets_raw.tsv").open(), delimiter="\t"))
    issues: list[dict] = []

    # clean rows
    clean = []
    for r in rows:
        lat, lng = float(r["lat"]), float(r["lng"])
        state = r["state"].strip().upper()

        # geocode sanity check against the state bounding box
        geocode_ok = True
        if state in STATE_BOX:
            s, n, w, e = STATE_BOX[state]
            if not (s <= lat <= n and w <= lng <= e):
                geocode_ok = False
                issues.append({"id": r["id"], "store": r["store"],
                               "issue": "coordinates fall outside the stated state",
                               "detail": f"{state} at {lat:.4f},{lng:.4f}"})

        # Roving listings ("Various Locations", no postcode) carry a placeholder
        # coordinate — Limestone Coast Farmers' Markets sits in the SA outback,
        # 300 km from the region it names. Excluded from the spatial analysis.
        if re.search(r"various", r["address"], re.I) and not r["postcode"].strip():
            geocode_ok = False
            issues.append({"id": r["id"], "store": r["store"],
                           "issue": "roving market with a placeholder coordinate",
                           "detail": f"address={r['address']!r}, no postcode"})

        freq = frequency_of(r["market_days"])
        day = trading_day(r["market_days"], r["hours_days"])

        if (r["hours_days"] and day != "Unknown"
                and r["hours_days"].strip() and day.lower() not in r["hours_days"].lower()):
            issues.append({"id": r["id"], "store": r["store"],
                           "issue": "trading day disagrees with opening-hours table",
                           "detail": f"market_days={r['market_days']!r} hours={r['hours_days']!r}"})

        o, c = parse_time(r["open_time"]), parse_time(r["close_time"])
        hours = round(c - o, 2) if (o is not None and c is not None and c > o) else None
        if hours is None:
            issues.append({"id": r["id"], "store": r["store"],
                           "issue": "opening hours could not be parsed",
                           "detail": f"{r['open_time']!r} - {r['close_time']!r}"})

        clean.append({
            "id": r["id"],
            "name": r["store"],
            "lat": lat,
            "lng": lng,
            "suburb": r["city"],
            "state": state,
            "postcode": r["postcode"],
            "url": r["url"],
            "operator": (r["operator"] or "").strip(),
            "market_days_raw": r["market_days"],
            "frequency": freq,
            "trading_day": day,
            "open_hour": o,
            "close_hour": c,
            "hours_open": hours,
            "hours_per_month": round(hours * markets_per_month(freq), 2) if hours else None,
            "geocode_ok": int(geocode_ok),
        })

    #  duplicate detection
    by_key = defaultdict(list)
    for m in clean:
        by_key[(norm(m["name"]), m["state"])].append(m)
    dup_ids = set()
    for key, group in by_key.items():
        if len(group) < 2:
            continue
        for i, a in enumerate(group):
            for b in group[i + 1:]:
                if a["trading_day"] != b["trading_day"]:
                    continue
                if haversine(a["lat"], a["lng"], b["lat"], b["lng"]) < 5:
                    keep, drop = sorted([a, b], key=lambda m: int(m["id"]))
                    dup_ids.add(drop["id"])
                    issues.append({"id": drop["id"], "store": drop["name"],
                                   "issue": "duplicate listing",
                                   "detail": f"same market as id {keep['id']} ({keep['name']})"})
    for m in clean:
        m["is_duplicate"] = int(m["id"] in dup_ids)

    # Distinct markets sharing a coordinate to within ~100 m indicate a
    # copy-pasted geocode instead of co-location, more like a duplicate
    for i, a in enumerate(clean):
        for b in clean[i + 1:]:
            if a["is_duplicate"] or b["is_duplicate"]:
                continue
            if haversine(a["lat"], a["lng"], b["lat"], b["lng"]) < 0.1:
                issues.append({"id": b["id"], "store": b["name"],
                               "issue": "coordinate shared with a different market",
                               "detail": f"within 100 m of id {a['id']} ({a['name']})"})

    active = [m for m in clean if not m["is_duplicate"]]

    #  outputs #
    write_csv(DATA / "markets.csv", clean)

    # by state
    pop = {r["state"]: int(r["erp"]) for r in
           csv.DictReader((DATA / "abs_population_2025.csv").open())
           if r["region_type"] == "STE"}
    by_state = []
    counts = Counter(m["state"] for m in active)
    for st, n in sorted(counts.items(), key=lambda kv: -kv[1]):
        p = pop.get(st)
        by_state.append({
            "state": st,
            "markets": n,
            "population": p,
            "markets_per_100k": round(n / p * 100_000, 3) if p else "",
            "hours_per_month": round(sum(m["hours_per_month"] or 0
                                         for m in active if m["state"] == st), 1),
        })
    # states with no listed markets still belong on the chart
    for st, p in pop.items():
        if st not in counts:
            by_state.append({"state": st, "markets": 0, "population": p,
                             "markets_per_100k": 0, "hours_per_month": 0})
    write_csv(DATA / "markets_by_state.csv", by_state)

    # frequency x state
    freq_rows = [{"state": st, "frequency": f, "markets": n}
                 for (st, f), n in
                 Counter((m["state"], m["frequency"]) for m in active).items()]
    freq_rows.sort(key=lambda r: (r["state"], r["frequency"]))
    write_csv(DATA / "frequency_by_state.csv", freq_rows)

    # day x start hour
    heat = Counter((m["trading_day"], int(m["open_hour"]))
                   for m in active if m["open_hour"] is not None)
    write_csv(DATA / "day_time_heatmap.csv",
              [{"day": d, "start_hour": h, "markets": n} for (d, h), n in sorted(heat.items())])

    # operators
    ops = Counter(m["operator"] for m in active if m["operator"])
    write_csv(DATA / "operators.csv",
              [{"operator": o, "markets": n,
                "states": "/".join(sorted({m["state"] for m in active if m["operator"] == o}))}
               for o, n in ops.most_common()])

    write_csv(DATA / "data_quality.csv", issues)

    print(f"{len(clean)} scraped, {len(dup_ids)} duplicates, {len(active)} distinct markets")
    print(f"{len(issues)} data-quality issues written to data/data_quality.csv")


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("")
        return
    with path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    main()
