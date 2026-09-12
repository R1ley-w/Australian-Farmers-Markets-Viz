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

## The bush palette

Built out from the five seed colours: `#D4B48C` sand, `#8AB46F` wattle
green, `#D3E5C1` pale wattle, `#8B824D` olive, `#C3BFC4` grey.

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
| `--land` | `#E8DCC8` | map landmass (from `#D4B48C`) | — |
| `--land-stroke` | `#C9C2B0` | map borders | — |

### Series — three slots, and three is the ceiling

| Slot | Name | Hex |
|---|---|---|
| 1 | eucalypt | `#3E5D1B` |
| 2 | dry grass | `#AF8340` |
| 3 | sky | `#3175A4` |

All-pairs validated against the `#FDFCF9` surface: lightness band, chroma
floor and contrast all pass; worst pair under simulated CVD **ΔE 16.3**
(protan, dry grass ↔ eucalypt) against a target of 8, and **ΔE 19.4**
unsimulated against a floor of 15.

**Three is a real ceiling, not a stylistic choice.** A search over ~4,000
candidate colours in bush hue families at muted chroma found no fourth
colour that clears the gates: the best bush-hue fourth slot manages CVD
ΔE 14.3 only by being a bright periwinkle, and no fifth slot clears the
floor at all. The reason is structural — greens and browns differ mainly
along the red-green axis, which is exactly the axis colour-vision
deficiency removes. Past three categories the charts use the ordinal
ramp below, with direct value labels doing the identity work.

### Accent

`--accent: #A8442A` red earth. For highlighting one mark in a field of
one other colour — the modal stall-fee band, the cumulative line, the
market itself among sales channels.

It pairs safely with sky (ΔE 18.3 CVD) and with dry grass (ΔE 12.0), but
it **collides with eucalypt** under CVD (ΔE 1.8). So on anything built
from the green ramp the highlight is sky blue, not red earth — which is
why Transport is picked out in blue on the emissions chart.

### Eucalypt sequential ramp

Choropleths, heatmaps, and any ordered category past three.

| step | hex | | step | hex |
|---|---|---|---|---|
| 100 | `#E7F5E2` | | 600 | `#568C43` |
| 200 | `#CFE8C7` | | 700 | `#3E722A` |
| 300 | `#B6D8AA` | | 800 | `#2D5A1B` |
| 400 | `#96C387` | | 900 | `#1F4212` |
| 500 | `#75A963` | | | |

The **4-step ordinal** used for trading frequency is
`#1F4212 · #3E722A · #6BA257 · #8ABD79`, run dark-first so darker reads
as "trades more often". Validated as an ordinal ramp: monotone lightness,
every adjacent gap ≥ 0.06 ΔL, single hue, and the light end clears the
2:1 floor at 2.12:1. (The plain 400 step does not — it measures 1.96:1 —
which is why the light end is `#8ABD79` rather than `#96C387`.)

### Dry-grass ramp

The second sequential context, for distance to the nearest market:
`#FEEDDB · #F7DABB · #ECC49A · #DDA971 · #C68A45 · #AA6C18 · #8E5400`.

Distance gets grass rather than green on purpose — the country browns off
as you move away from a market, so the metaphor and the "darker = more"
convention point the same way, and it keeps the distance map visually
distinct from the density map.

Both sequential maps use a `sqrt` scale. Most of the continent is past any
sensible distance cap and one heatmap cell holds 70 of 175 markets, so a
linear ramp floods the first and washes out the second.

---

## Reproducing the validation

The palette checks come from the data-viz skill's validator, which
computes OKLCH lightness and chroma, OKLab ΔE under the
Machado–Oliveira–Fernandes CVD simulation, and WCAG contrast:

```bash
# the three series slots, all pairs
validate_palette "#3E5D1B,#AF8340,#3175A4" --mode light --surface "#FDFCF9" --pairs all

# the 4-step frequency ordinal
validate_palette "#8ABD79,#6BA257,#3E722A,#1F4212" --mode light --surface "#FDFCF9" --ordinal

# the accent, against each colour it actually sits beside
validate_palette "#3175A4,#A8442A" --mode light --surface "#FDFCF9" --pairs all
validate_palette "#AF8340,#A8442A" --mode light --surface "#FDFCF9" --pairs all
```
