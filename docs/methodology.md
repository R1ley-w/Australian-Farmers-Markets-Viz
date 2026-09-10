# Methodology

Everything on the page comes from `data/`, and everything in `data/` is either a
primary source file or a product of the two scripts in `scripts/`. This is the
record of what was done to the raw data and why.

---

## 1. Getting the market data

There is no official register of Australian farmers' markets — no ABS series, no
data.gov.au entry. The Australian Farmers' Markets Association runs the only
national directory, at <https://farmersmarkets.org.au/find-a-market/>.

The page is a WP Store Locator plugin, which exposes an undocumented JSON
endpoint:

```
https://farmersmarkets.org.au/wp-admin/admin-ajax.php
  ?action=store_search&lat=-25&lng=134&search_radius=4000&max_results=3000
```

**The directory holds 178 listings.** That was verified two ways: a single
wide-radius query returns 178, and a 1,248-cell grid of small-radius queries
covering the continent returns exactly the same 178 records. The "300-plus"
figure that circulates in the literature is not what the directory currently
contains.

Per-record fields used: `store`, `lat`, `lng`, `address`, `city`, `state`, `zip`,
`url`, `hours`, `market_days`, `market_operator`, `market_manager`.

Scraped 10 September 2026 and saved verbatim as `data/afma_markets_raw.tsv`, with
the `hours` HTML table parsed to a day and an open/close time at capture. No
licence is stated on the directory; it is reproduced here for a student
assignment, with attribution.

### What the directory does *not* contain

Worth stating, because several plausible chart ideas die here:

- **No product data.** Not as a field, not as free text. "How many markets sell
  honey" cannot be answered from this source.
- **No size measure.** No stall count, no visitor count, no revenue. Trading
  hours and frequency are the only size proxies available.
- **No usable accreditation flag.** The `thumb` field carries an AFMA
  accreditation tick for exactly four of the 178 listings, which is too few to
  read as a real accreditation variable.

---

## 2. Cleaning it (`scripts/prep_markets.py`)

### Trading frequency

Derived from the free-text `market_days` field, which is written by whoever
registered the market and is not standardised. Examples in the data: `Saturdays`,
`Every Saturday`, `1st & 3rd Sundays`, `Ist & 3rd Saturdays` (sic), `4th Saturday
January, April, July, October`, `Various dates (contact manager)`.

The rule:

| Pattern | Frequency |
|---|---|
| "various", "contact manager" | Irregular |
| "every", or a pluralised day name, with no ordinal | Weekly |
| Two or more ordinal week markers (`1st & 3rd`) | Fortnightly |
| Exactly one ordinal week marker (`4th Saturday`) | Monthly |
| A bare day name with no qualifier | Weekly |

"Fortnightly" is a slight abuse of the word — `1st & 3rd Saturday` is twice a
month, not every fourteen days — but it is the closest of the four labels and it
is applied consistently.

### Trading day

Taken from `market_days` where a day name appears there, falling back to the
opening-hours table. **Four listings disagree with themselves** — Parramatta says
Wednesday in one field and Friday in the other; Heathmont, Bindoon and Freo have
similar conflicts. `market_days` wins, and all four are logged.

### Duplicate listings

Two records are treated as the same market when they share a normalised name (case
folded, punctuation stripped, the words *farmers / growers / producers / market /
community* removed), the same state, the **same trading day**, and sit within 5 km
of each other.

The trading-day condition matters. Bellingen has two genuinely different markets
with near-identical names — one Saturday, one Wednesday — and an earlier version
of this rule wrongly collapsed them. Three duplicates were found: Powerhouse,
Churchill Island and Kyogle.

**178 listings → 175 distinct markets.**

### Geocode quality

Two checks:

1. **Coordinates against the stated state's bounding box.** No failures.
2. **Roving listings.** One market — Limestone Coast Farmers' Markets — has
   `address = "Various Locations"`, no postcode, and a coordinate in the South
   Australian outback roughly 300 km from the region it names. It is flagged
   `geocode_ok = 0` and excluded from all spatial analysis, leaving **174
   markets** on the maps.

A third check reports, without excluding: markets whose coordinates fall within
100 m of a *different* market. Two pairs do (Slow Food Spotswood shares a
coordinate with Abbotsford Convent; Rainbow Region shares one with Lismore),
which indicates a copy-pasted geocode. The error is a few kilometres at most and
does not change any regional aggregate, so those markets are kept and the issue
is recorded.

Every issue found is written to `data/data_quality.csv`.

---

## 3. The spatial work (`scripts/prep_spatial.py`)

### Boundaries

ABS Australian Statistical Geography Standard Edition 3, as simplified TopoJSON:
state (STE 2021), Greater Capital City Statistical Area (GCCSA 2021) and local
government area (LGA 2023). CC BY 4.0. Originals in `data/boundaries/`; the
trimmed versions the page actually loads keep only the code, name and state
properties.

TopoJSON is decoded in pure Python — the format is quantised delta-encoded arcs
plus an index, so a decoder is about forty lines and saves a geopandas
dependency. Both scripts use only the standard library.

### Assigning markets to regions

Point-in-polygon (ray casting) with a bounding-box prefilter. Seven of the 174
markets fall just outside every GCCSA polygon, which is an artefact of boundary
simplification on the coast; each is snapped to the nearest region centre rather
than dropped.

One consequence worth knowing: a market's **listed** state and its **actual
location** can differ. Albury-Wodonga is listed under NSW but sits in Victoria,
and one market listed in NSW falls inside the ACT polygon. The by-state chart
uses the listed state; the maps use the location. The totals therefore differ by
one or two between those two views, and both are correct for what they measure.

### Population

ABS estimated resident population at 30 June 2025, used for every rate on the
page:

- Greater Capital City populations from **Regional population, 2024-25**.
- State and territory totals from **National, state and territory population,
  Jun 2025**.
- Rest-of-state = state total − capital city. Both figures are at the same
  reference date, so the subtraction is clean.

### Distance to the nearest market

For each of 544 LGAs, the great-circle (haversine) distance from the LGA's centre
to the nearest of the 174 geocoded markets.

**Three limitations, stated plainly:**

1. **Straight-line, not road distance.** Real travel is longer, so every figure
   here is a best case.
2. **Area centroid, not population-weighted centre.** A large remote LGA whose
   residents all live in one coastal town reads as further from a market than
   they actually are. This overstates isolation in the sparsest parts of the
   country and is accurate in the dense parts, which is where the argument sits.
3. **Centroids are nudged inside concave shapes.** Where the area centroid falls
   outside its own polygon, the nearest boundary vertex of the largest ring is
   used instead.

The 22 LGAs in Other Territories (Christmas Island, Cocos, Jervis Bay) are
excluded — they are thousands of kilometres offshore and would dominate the
colour scale without saying anything about mainland access. That leaves 544 of
the 566 LGAs.

### The coverage curve

Cumulative share of LGAs, and of Australia's land area, within N km of a market —
a straight cumulative sum over the distance calculation above. It is deliberately
*not* a population coverage curve: that would need ERP by LGA, which is a
separate ABS download not used here.

---

## 4. The other datasets

| Source | Used for | Vintage | Note |
|---|---|---|---|
| RIRDC Pub. 14/040 | travel distance, stall fees, product mix, sales channels | 2014 | n = 286 stallholders. The richest Australian dataset on stallholders that exists, and twelve years old. |
| Our World in Data / Poore & Nemecek | emissions by supply-chain stage | 2018 | CC BY 4.0. Global averages, not Australian. |
| DCCEEW National Food Waste Baseline | food waste by sector | 2016-17 | The published baseline names only the three largest sectors; the residual is labelled as such. |
| ACCC Supermarkets Inquiry final report | grocery market share | Feb 2025 | Executive summary figures. |
| ABS ASGS Edition 3 | all boundaries | 2021 / LGA 2023 | CC BY 4.0. |
| ABS ERP | all population rates | 30 Jun 2025 | CC BY 4.0. |

### Two charts that were planned and could not honestly be built

- **ACCC average product margins, 2019-20 to 2023-24 (Figure 1.3).** The report
  presents these as a chart image. The underlying percentages appear nowhere in
  the text, and the text says only that the margins "increased". Building a slope
  chart would have meant reading values off a picture and presenting them as
  data. Replaced by the food waste baseline.
- **Horticulture gross value vs market density.** ABS does not publish gross
  horticulture value by state in a retrievable form for the current reference
  year; the 2021-22 Value of Agricultural Commodities release is a reduced set
  after a poor survey response, and the 2024-25 horticulture release gives
  national totals with only scattered state figures for individual crops.
  Replaced by the Melbourne / Sydney comparison.

Both substitutions are noted in the README as well, because a marker reading only
the chart list should not have to guess why the plan changed.

---

## 5. Reproducing it

```bash
python3 scripts/prep_markets.py    # 178 listings -> markets.csv + aggregates
python3 scripts/prep_spatial.py    # spatial joins, distances, trimmed basemaps
python3 -m http.server 8000        # then open http://localhost:8000
```

Optionally, to confirm every chart still compiles and renders after a change:

```bash
npm install vega vega-lite canvas
node scripts/check_charts.mjs
```

That script compiles each spec, runs it against the real data files, reports the
row count that reached each mark (so a lookup that silently joins nothing is
visible), surfaces the sort and scale warnings Vega-Lite otherwise swallows, and
writes a PNG of every chart to `/tmp/afm-charts`.
