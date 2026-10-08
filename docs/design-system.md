# Design system

Light theme only. One rule governs the whole page:

> **A colour encodes exactly one variable.** A saturated hue always means a
> state and nothing else. Quantities use a reserved ramp. One highlight marks
> the single category a chart is arguing about. Nothing is reused for a second
> meaning anywhere on the page.

The tokens live in `css/style.css` and are handed to Vega-Lite as a shared
config in `js/main.js`, so the page and the charts are styled from one source
and no spec carries fonts or chrome colours of its own. Every categorical scale
in every spec names its own `domain` and `range`; the shared config deliberately
has **no default categorical range**, so a colour cannot pick up a second
meaning by falling through to a shared default.

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

No colour on any title — every heading is ink. Eyebrows and act numbers are
`--ink-strong` `#3D434A`, a darker grey rather than a hue, because a hue there
would be a colour that encodes nothing.

---

## Surfaces and chrome — no meaning

These carry no data. They are neutral so that the only chromatic thing on the
page is an encoding.

| Token | Hex | Role | Contrast on page |
|---|---|---|---|
| `--page` | `#F7F7F5` | page ground | — |
| `--surface` | `#FDFDFC` | chart surface | — |
| `--tint` | `#F0F1EE` | takeaway panels | — |
| `--ink` | `#1C1F23` | primary ink | 14.9:1 |
| `--ink-2` | `#474D54` | secondary ink, lede | 7.9:1 |
| `--ink-muted` | `#767C83` | axis labels, captions | 4.0:1 |
| `--ink-strong` | `#3D434A` | eyebrows, act numbers, links | 10.1:1 |
| `--grid` | `#E6E6E3` | hairline gridlines | — |
| `--axis` | `#C6C6C2` | baselines | — |
| `--land` | `#E9EAEC` | map landmass | — |
| `--land-stroke` | `#CDCED1` | map borders | — |

The landmass is grey on purpose. On the two choropleths the polygons carry a
`--land-stroke` hairline, so a region at the pale end of a ramp is still
readable as a shape rather than disappearing into the surface.

---

## 1. State identity

A state keeps the same colour everywhere it appears on the page. Victoria is
`#C56C00` in the ranked list, in the metro comparison and in the operator
chart, and orange means Victoria and nothing else in any of the sixteen charts.

| State | Token | Hex | Hue |
|---|---|---|---|
| NSW | `--st-nsw` | `#0063A0` | blue |
| VIC | `--st-vic` | `#C56C00` | orange |
| QLD | `--st-qld` | `#039B8C` | teal |
| WA | `--st-wa` | `#A17CDA` | violet |
| SA | `--st-sa` | `#8C4062` | plum |
| TAS | `--st-tas` | `#2D6101` | green |
| ACT | `--st-act` | `#767676` | neutral — 2 markets |
| NT | `--st-nt` | `#A6A6A6` | neutral — 0 markets |

All six hues validated all-pairs against the `#FDFDFC` chart surface: lightness
band, chroma floor and 3:1 contrast all pass; worst pair under simulated CVD
**ΔE 9.7** (deutan, TAS ↔ SA) against a target of 8, and **ΔE 18.3**
unsimulated (QLD ↔ NSW) against a floor of 15.

**Why two of the eight are grey.** Eight distinguishable hues is not achievable
at this surface and lightness band. The best eight-way set found reaches only
ΔE 12.4 unsimulated — under the 15 floor — and the best seven-way set reaches
7.7 / 14.0, which also fails. Rather than ship two colours that cannot be told
apart, the two jurisdictions with two markets and none take neutral greys, which
is honest about how little there is to distinguish. This is a measured ceiling,
not a style preference; re-run the search before adding a seventh hue.

**There is no red in this set**, which is what guarantees no red/green pairing
can occur. The highlight below is red, and it is confined to charts that carry
no state colour at all.

State colour appears in exactly two specs: `02b-gccsa-ranked` and
`08-operators`.

---

## 2. Magnitude — any ordered or continuous quantity

One muted slate-blue ramp, used for every quantity that is not
distance-to-a-market. The legend names the quantity; the colour only ever means
*more of it*.

| step | hex | | step | hex |
|---|---|---|---|---|
| 100 | `#EAF3FC` | | 600 | `#6587A7` |
| 200 | `#D0E0F0` | | 700 | `#4D6E8D` |
| 300 | `#B5CCE2` | | 800 | `#375470` |
| 400 | `#9AB6D2` | | 900 | `#243B51` |
| 500 | `#7F9FBE` | | 950 | `#132434` |

Single hue (OKLCH H 248, spread 1°), monotone in lightness, even steps. Step 950
exists only for the one scale that needs a ninth dark step — the emissions bar,
which has eight stages.

**Why a muted blue rather than a saturated one, and how it stays distinct from
NSW's blue.** Six state hues already span the colour wheel at 47–77° apart, so
there is no free hue left for a ramp to occupy: every candidate lands next to a
state. A steel blue at H 214 sits ΔE 2.9 from Queensland's teal under simulated
CVD; a true blue sits next to New South Wales.

So the ramp is not separated from the state hues by *hue* — it is separated by
**chroma**. The ramp peaks at C 0.062; the state hues run C 0.110–0.147, two to
two and a half times higher. A quantity reads as a tinted neutral and an
identity reads as a colour. That distinction is what the one-variable rule rests
on here, and it is the reason the ramp must stay muted: saturating it would make
it compete with the state hues for the same perceptual role.

The ramp and the state hues also never share a chart (`§1` lists where each
appears), so the remaining closeness is cross-chart only. The tightest case is
step 800 `#375470` against South Australia's plum, ΔE 2.3 under simulated
protanopia and 14.5 unsimulated — they sit in different charts and SA is always
directly labelled.

Its pale end is close to the surface by design — in a continuous choropleth or
heatmap that end means *near zero*, and the polygon strokes keep the shape
legible.

The **4-step discrete ordinal** used for trading frequency takes four steps from
the same ramp, run dark-first so darker reads as "trades more often":

`#243B51 · #4D6E8D · #7F9FBE · #9AB6D2`

Validated as an ordinal ramp: monotone lightness, every adjacent gap ≥ 0.06 ΔL,
single hue (1° spread), and the light end clears the 2:1 floor at 2.06:1 — which
is why the light end is step 400 and not step 300, which measures 1.62:1.

Trading frequency is a variable in its own right, so it keeps this exact
four-step scale everywhere it is encoded — the national map (`01`), the state
breakdown (`07`) and the Melbourne/Sydney panels (`04`). Weekly is always the
darkest step.

Neither sequential map is linear, for good reason. The day/hour heatmap has one
cell holding 70 of 175 markets, which washed every other cell to near-white, so
it uses **pow 0.4**.

---

## 3. Distance from a market — its own ramp

Distance gets a separate warm ramp so that the distance map is never mistaken
for the density map, and so "how far" never shares a colour with "how many".

`#FEEFDE · #F7DCBC · #EDC698 · #DDAC6E · #C58D41 · #A96F10 · #8C5600 · #6E4000 · #4F2C00`

Monotone in lightness at a single hue (spread 7°). Used in one spec only:
`03-lga-distance`.

Distance to a market spans 0.1 km to 2,228 km, so this choropleth is **log**
scaled — a capped linear ramp put 38% of LGAs, and most of the land area, on a
single step.

---

## 4. Highlight

`--highlight: #B83025`. The one category a chart is arguing about: the modal
stall-fee band, the cumulative travel line, the market itself among sales
channels, primary production in the food-waste bar, Transport in the emissions
bar.

It sits against the magnitude ramp, never against a state hue. Measured against
every ramp step it can neighbour, the closest is step 800 `#375470` at **CVD ΔE
11.6** (protan) and **ΔE 23.8** unsimulated; the mid-ramp steps sit further
still, at ΔE 15.8–21.5 under CVD. The blue ramp separates from the red highlight
more cleanly than the grey one did. The validator marks the grey as failing
the chroma floor, which is correct and intended: the grey is not a series
colour, it is the "everything else" ground the highlight is picked out against.

The highlight appears in `05`, `09`, `10`, `12`, `13`, `14` — none of which
carry a state colour, so red and green never meet.

---

## Where each colour appears

| Encoding | Specs |
|---|---|
| State identity hues | `02b`, `08` |
| Magnitude ramp | `01`, `02`, `04`, `06`, `07`, `11`, `13`, `14`, `15` |
| Distance ramp | `03` |
| Highlight | `05`, `09`, `10`, `12`, `13`, `14` |

The only pairing that occurs is highlight against the magnitude ramp, which is
the highlight doing exactly its one job — picking one category out of a neutral
field. State identity and the distance ramp each appear alone. No spec mixes
state hues with the highlight, and none mixes the two ramps.

---

## Reproducing the validation

The checks come from the data-viz skill's validator, which computes OKLCH
lightness and chroma, OKLab ΔE under the Machado–Oliveira–Fernandes CVD
simulation, and WCAG contrast:

```bash
# the six state hues, all pairs
validate_palette "#0063a0,#c56c00,#039b8c,#a17cda,#8c4062,#2d6101" \
  --mode light --surface "#fdfdfc" --pairs all

# the magnitude ramp, as a sequential scale
validate_palette "#eaf3fc,#d0e0f0,#b5cce2,#9ab6d2,#7f9fbe,#6587a7,#4d6e8d,#375470,#243b51" \
  --mode light --surface "#fdfdfc" --ordinal

# the 4-step frequency ordinal
validate_palette "#9ab6d2,#7f9fbe,#4d6e8d,#243b51" \
  --mode light --surface "#fdfdfc" --ordinal

# the highlight against the ramp step it neighbours
validate_palette "#375470,#b83025" \
  --mode light --surface "#fdfdfc" --pairs all
```

The two 9-step ramps are continuous scales, not discrete ordinals, so they are
checked for lightness monotonicity and single hue rather than against the
discrete-step gap and light-end contrast floors, which assume each step has to
stand alone as a mark.
