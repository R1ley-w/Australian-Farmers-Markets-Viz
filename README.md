# Australian Farmers' Markets — a data visualisation

An interactive Vega-Lite narrative about where Australia's farmers' markets are,
who can reach them, what they do for producers, and how the sustainability case
for them actually stacks up.

Built for Monash FIT3179 Data Visualisation 2.

## Running it

The page is plain static HTML — no build step. Any static server will do:

```bash
python3 -m http.server 8000
# then open http://localhost:8000
```

Opening `index.html` directly from the filesystem will not work: the charts
fetch their data with `fetch()`, which browsers block on `file://` origins.

## Layout

```
index.html                 the narrative page
css/style.css              layout, typography, light/dark tokens
js/main.js                 chart loader, theme handling, tooltips
specs/*.vg.json            one Vega-Lite spec per idiom
data/                      source data and the files derived from it
vendor/                    Vega, Vega-Lite and Vega-Embed, pinned
scripts/prep_markets.py    cleans the scraped AFMA directory
scripts/prep_spatial.py    the spatial joins behind the four maps
docs/                      data provenance and methodology notes
```

Vega is vendored rather than pulled from a CDN, so the page renders offline and
the exact library versions are pinned in the repo — see `vendor/README.md`.
There is still nothing to build or install.

To regenerate everything derived from the raw sources:

```bash
python3 scripts/prep_markets.py
python3 scripts/prep_spatial.py
```

Both scripts use only the Python standard library.

## The idioms

Sixteen idioms, four of them maps.

**Maps**

| # | Idiom | Spec |
|---|---|---|
| 1 | Symbol map — every market, coloured by frequency, sized by trading hours | `01-market-map` |
| 2 | Choropleth + proportional symbols — markets per 100k by GCCSA | `02-gccsa-density` |
| 3 | Choropleth — distance from each LGA centre to its nearest market | `03-lga-distance` |
| 4 | Small-multiple maps — Greater Melbourne vs Greater Sydney at one scale | `04-metro-comparison` |

**Non-map**

| # | Idiom | Spec |
|---|---|---|
| 5 | Ranked bar — every region by market density | `02b-gccsa-ranked` |
| 6 | Cumulative line — population and land area within N km | `05-coverage-curve` |
| 7 | Heatmap — trading day × opening hour | `06-day-hour-heatmap` |
| 8 | Normalised stacked bar — trading frequency by state | `07-frequency-by-state` |
| 9 | Labelled bar — multi-market operators | `08-operators` |
| 10 | Bar + cumulative line — stallholder travel distance | `09-travel-distance` |
| 11 | Histogram — stall fee distribution | `10-stall-fees` |
| 12 | Grouped bar — national product mix | `11-product-mix` |
| 13 | Lollipop — stallholder sales channels | `12-sales-channels` |
| 14 | Stacked bar — food emissions by supply-chain stage | `13-emissions-by-stage` |
| 15 | Single stacked bar — food waste by sector | `14-food-waste` |
| 16 | Donut — supermarket concentration | `15-supermarket-share` |

### Two deviations from the original plan

- The **ACCC product-margin slope chart** (Figure 1.3) was dropped. The ACCC
  publishes those margins only as a chart image; the underlying percentages are
  not stated numerically anywhere in the report, so the chart could not have been
  built without inventing numbers. The **food waste baseline** replaces it, and
  makes a stronger sustainability argument on published Commonwealth data.
- The **horticulture-value vs market-density bivariate map** was dropped. ABS
  does not publish gross horticulture value by state in a retrievable form for
  the current reference year. The **Melbourne / Sydney comparison** replaces it.

## A note on the data

There is no official government dataset of Australian farmers' markets. No ABS
series, no data.gov.au entry. The AFMA "Find a Market" directory is the de facto
census, and it is self-registration, so it under-counts small and non-member
markets.

The directory holds **178 listings**, which resolve to **175 distinct markets**
after de-duplication, of which **174** have coordinates usable for spatial
analysis. That is materially fewer than the "300+" often quoted. Every cleaning
decision is recorded in `data/data_quality.csv` and explained in
`docs/methodology.md`.

Sources, licences and vintages are set out in `docs/data-sources.md`. Every
chart carries its own source line and reference year.
