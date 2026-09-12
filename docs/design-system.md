# Design system

Light theme only. One palette, two typefaces. The tokens live in
`css/style.css` and are handed to Vega-Lite as a shared config in
`js/main.js`, so the page and the charts are styled from one source and
no spec carries fonts or chrome colours of its own.

---

## Typography

| Role | Face | Weight | Used for |
|---|---|---|---|
| Large titles | Georgia (serif) | **700** | `h1`, stat-tile values |
| Graph titles | Georgia (serif) | 400 | `figcaption .title`, Vega chart titles |
| Section titles | Helvetica Neue | **700** | `h2`, `h3`, eyebrows, axis and legend titles |
| Body | Helvetica Neue | 400 | prose, axis labels, legends, tooltips, captions |

```css
--font-serif: Georgia, "Iowan Old Style", "Times New Roman", Times, serif;
--font-sans:  "Helvetica Neue", Helvetica, Arial, "Liberation Sans", sans-serif;
```

No colour on any title. The eyebrows and act numbers are olive
`#6E6733` — the seed olive `#8B824D` deepened to clear 4.5:1 on the page
ground. Everything else is ink.

---

## The nature palette

Built out from the five seed colours: `#D4B48C` sand, `#8AB46F` wattle
green, `#D3E5C1` pale wattle, `#8B824D` olive, `#C3BFC4` grey, extended
across the nature range — pale blues, greens, browns, golds and rusts.

The seeds are *tints*. Run through the palette validator they fail on
three counts — three of the five sit outside the lightness band, four
read as grey against the chroma floor, and wattle-green against sand
measures ΔE 4.2 under simulated protanopia, which is indistinguishable.
So the seeds do the job they are good at — surfaces, landmass fill,
chrome — and the series colours are deeper steps from the same hue
families.

### Surfaces and chrome

| Token | Hex | Role | Contrast on page |
|---|---|---|---|
| `--page` | `#FAF7F0` | warm paper | — |
| `--surface` | `#FDFCF9` | chart surface | — |
| `--tint` | `#EEF3E3` | takeaway panels (from `#D3E5C1`) | — |
| `--ink` | `#1F2417` | primary ink | 14.8:1 |
| `--ink-2` | `#4A4F3E` | secondary ink | 7.9:1 |
| `--ink-muted` | `#7C7F6E` | axis labels, captions | 3.8:1 |
| `--ink-olive` | `#6E6733` | eyebrows, links | 5.4:1 |
| `--grid` | `#E3E0D4` | hairline gridlines | — |
| `--axis` | `#C3BFC4` | baselines (seed grey) | — |
| `--neutral` | `#8A877F` | residual "everyone else" categories | 3.5:1 on surface |
| `--land` | `#E8DCC8` | map landmass (from `#D4B48C`) | — |
| `--land-stroke` | `#C9C2B0` | map borders | — |

### Series — four slots, and four is the ceiling

| Slot | Name | Hex | Family |
|---|---|---|---|
| 1 | eucalypt | `#457B45` | green |
| 2 | bark | `#7A4208` | brown |
| 3 | waterhole | `#4199C9` | pale blue |
| 4 | dry gold | `#B68611` | gold / yellow |

All-pairs validated against the `#FDFCF9` surface: lightness band, chroma
floor and contrast all pass; worst pair under simulated CVD **ΔE 9.2**
(protan, dry gold ↔ eucalypt) against a target of 8, and **ΔE 16.4**
unsimulated (bark ↔ eucalypt) against a floor of 15.

Opening the palette to golds and oranges is what made a fourth slot
possible. Green and brown differ mainly along the red-green axis, which
is exactly the axis colour-vision deficiency removes; gold is separated
on the *blue-yellow* axis, which CVD preserves.

**Four is where it stops.** Searching the full nature hue range for a
fifth, teal and rust both fail against this set, and the only colours
that pass are a second blue — which is no use as a distinct identity.
Past four categories the charts fold the residual to `--neutral` or use
the ordinal ramp below.

**Treat these four as fixed values, not a starting point.** The feasible
region is very narrow: lightening the bark by one step drops the worst
CVD pair from 9.2 to 4.8, and warming the green by one step drops it to
7.7. Both fail. If you need to change one, re-run the search rather than
nudging by eye.

### Accent

`--accent: #A8442A` red earth. For highlighting one mark in a field of
one other colour — the modal stall-fee band, the cumulative travel line,
the market itself among sales channels, primary production in the food
waste bar.

Safe beside waterhole (CVD ΔE 21.7) and dry gold (ΔE 13.7). It
**collides with eucalypt** (ΔE 3.6) and **bark** (ΔE 5.2), so it must
never sit beside those two — which is why the travel-distance bars are
waterhole rather than green, and why the donut's ring order puts red
earth between waterhole and the neutral.

On anything built from the green ramp the highlight is **dry gold**, not
red earth — which is why Transport is gold on the emissions chart.

### Eucalypt sequential ramp

Choropleths, heatmaps, and any ordered category past four.

Regenerated at the series green's own hue (OKLCH H 144) so the ramp and
slot 1 read as one family.

| step | hex | | step | hex |
|---|---|---|---|---|
| 100 | `#E5F5E5` | | 600 | `#4D8D4D` |
| 200 | `#CCE9CB` | | 700 | `#357336` |
| 300 | `#B1D9B0` | | 800 | `#245B26` |
| 400 | `#90C48F` | | 900 | `#19421A` |
| 500 | `#6EAA6D` | | | |

The **4-step ordinal** used for trading frequency is
`#19421A · #357336 · #5B995A · #89BC87`, run dark-first so darker reads
as "trades more often". Validated as an ordinal ramp: monotone lightness,
every adjacent gap ≥ 0.06 ΔL, single hue, and the light end clears the
2:1 floor at 2.13:1. (The plain 400 step does not — it measures 1.95:1 —
which is why the light end is `#89BC87` rather than `#90C48F`.)

### Dry-grass ramp

The second sequential context, for distance to the nearest market:
`#FEEDDB · #F7DABB · #ECC49A · #DDA971 · #C68A45 · #AA6C18 · #8E5400`.

Distance gets grass rather than green on purpose — the country browns off
as you move away from a market, so the metaphor and the "darker = more"
convention point the same way, and it keeps the distance map visually
distinct from the density map.

Neither sequential map is linear, for good reason. Distance to a market
spans 0.1 km to 2,228 km, so the distance choropleth is **log** scaled —
a capped linear ramp put 38% of LGAs, and most of the land area, on one
step. The day/hour heatmap has one cell holding 70 of 175 markets, which
washed every other cell to near-white, so it uses **pow 0.4**.

---

## Reproducing the validation

The palette checks come from the data-viz skill's validator, which
computes OKLCH lightness and chroma, OKLab ΔE under the
Machado–Oliveira–Fernandes CVD simulation, and WCAG contrast:

```bash
# the four series slots, all pairs
validate_palette "#457B45,#7A4208,#4199C9,#B68611" --mode light --surface "#FDFCF9" --pairs all

# the 4-step frequency ordinal
validate_palette "#89BC87,#5B995A,#357336,#19421A" --mode light --surface "#FDFCF9" --ordinal

# the accent, against each colour it actually sits beside
validate_palette "#4199C9,#A8442A" --mode light --surface "#FDFCF9" --pairs all
validate_palette "#B68611,#A8442A" --mode light --surface "#FDFCF9" --pairs all

# and the pairs it must NOT sit beside, for the record
validate_palette "#457B45,#A8442A" --mode light --surface "#FDFCF9" --pairs all   # ΔE 3.6
validate_palette "#7A4208,#A8442A" --mode light --surface "#FDFCF9" --pairs all   # ΔE 5.2
```
