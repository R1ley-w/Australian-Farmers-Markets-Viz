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
scripts/prep_markets.py    cleans the scraped AFMA directory
scripts/prep_spatial.py    the spatial joins behind the four maps
docs/                      data provenance and methodology notes
```

To regenerate everything derived from the raw sources:

```bash
python3 scripts/prep_markets.py
python3 scripts/prep_spatial.py
```

Both scripts use only the Python standard library.

## The idioms

**Maps (4)**

1. Every farmers' market in Australia — symbol map, coloured by trading
   frequency, sized by trading hours
2. Markets per 100,000 people — choropleth by Greater Capital City Statistical
   Area and rest-of-state
3. How far is the nearest market? — choropleth of distance from each LGA's
   centre to its nearest market
4. Who runs the markets? — the multi-market operator networks, mapped

**Non-map (9, plus one bonus)**

5. Where food emissions actually come from — emissions by supply-chain stage
6. How far stallholders travel to market
7. Trading frequency by state
8. What stallholders sell — national product mix
9. What a stall costs — stall fee distribution
10. What markets are up against — supermarket concentration
11. Where food is wasted — Australia's food waste baseline by sector
12. Markets are one channel among several — stallholder sales channels
13. The operators, by market count
14. *(bonus)* When can you actually shop? — trading day × opening hour

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
