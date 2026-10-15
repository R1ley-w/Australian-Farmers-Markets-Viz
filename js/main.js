/* ------------------------------------------------------------------
   Chart loader and shared Vega-Lite theme.

   The specs carry no fonts and no chrome colours of their own; they
   come from here, read off the CSS custom properties in css/style.css
   ------------------------------------------------------------------ */

const token = (name) =>
  getComputedStyle(document.documentElement).getPropertyValue(name).trim();

function theme() {
  const ink = token('--ink');
  const ink2 = token('--ink-2');
  const muted = token('--ink-muted');
  const grid = token('--grid');
  const axis = token('--axis');
  const surface = token('--surface');
  const serif = token('--font-serif');
  const sans = token('--font-sans');
  const mag = [1, 2, 3, 4, 5, 6, 7, 8, 9].map((i) => token(`--mag-${i}00`));
  const seqBrown = ['#f7dcbc', '#edc698', '#ddac6e', '#c58d41', '#a96f10', '#6e4000', '#4f2c00'];

  return {
    background: null,
    font: sans,
    padding: 0,
    autosize: { type: 'fit', contains: 'padding', resize: true },
    title: {
      font: serif, fontWeight: 400, fontSize: 15, color: ink, anchor: 'start',
      subtitleFont: sans, subtitleColor: muted, subtitleFontSize: 11.5,
      offset: 8, dy: -2,
    },
    axis: {
      labelFont: sans, labelColor: muted, labelFontSize: 11.5,
      titleFont: sans, titleColor: ink2, titleFontSize: 11.5,
      titleFontWeight: 700, titlePadding: 8,
      gridColor: grid, gridWidth: 1, domainColor: axis, tickColor: axis,
      tickSize: 4, labelPadding: 4,
    },
    axisX: { grid: false, labelAngle: 0 },
    axisY: { domain: false, ticks: false, gridDash: [] },
    legend: {
      labelFont: sans, labelColor: ink2, labelFontSize: 11.5,
      titleFont: sans, titleColor: ink2, titleFontSize: 11.5,
      titleFontWeight: 700, symbolStrokeWidth: 0, symbolSize: 90,
      offset: 10, padding: 0,
    },
    view: { stroke: null, continuousWidth: 620, continuousHeight: 300 },
    range: {
      // No default categorical range. Every categorical scale in this
      // project names its own domain and range, so a colour cannot pick up
      // a second meaning by falling through to a shared default.
      // Sequential (quantitative) scales are one brown, light to dark. Hue is kept for
      // categories only, so a colour never means both a category and an amount.
      heatmap: seqBrown,
      ramp: seqBrown,
      ordinal: [mag[8], mag[6], mag[4], mag[3]],
    },
    mark: { tooltip: true },
    bar: { cornerRadiusEnd: 3 },
    rect: { stroke: surface, strokeWidth: 2 },
    arc: { stroke: surface, strokeWidth: 2 },
    line: { strokeWidth: 2 },
    point: { size: 70, filled: true },
    circle: { size: 70 },
    rule: { color: axis },
    text: { font: sans, color: ink2, fontSize: 11.5 },
    geoshape: { stroke: surface, strokeWidth: 0.5 },
    concat: { spacing: 26 },
    facet: { spacing: 22 },
  };
}

const embedOptions = () => ({
  actions: { export: true, source: true, compiled: false, editor: true },
  renderer: 'canvas',
  config: theme(),
  tooltip: { theme: 'light' },
});

/* ------------------------------------------------------------- links

   Charts that share a selection declare it in their spec:
     "usermeta": {"link": {"group": "commodity", "signal": "commodity"}}
   A change to that signal in one chart is pushed to every other chart in
   the same group. Charts render lazily, so the group remembers its latest
   value and a chart that renders later starts from it. */

const linkGroups = {};

function joinLink(view, link) {
  const g = (linkGroups[link.group] ??= { value: undefined, members: [] });
  const member = { view, signal: link.signal };
  g.members.push(member);
  if (g.value !== undefined && view.signal(link.signal) !== g.value) {
    view.signal(link.signal, g.value).runAsync();
  }
  view.addSignalListener(link.signal, (_, value) => {
    if (value === g.value) return;
    g.value = value;
    for (const m of g.members) {
      if (m !== member && m.view.signal(m.signal) !== value) {
        m.view.signal(m.signal, value).runAsync();
      }
    }
  });
}

/* ------------------------------------------------------------ render */

async function renderOne(el) {
  const url = el.dataset.spec;
  el.innerHTML = '<p class="loading">Loading chart…</p>';
  try {
    // no-cache forces a conditional request, so an edited spec is picked up
    // on reload instead of being served from the browser's cache.
    const res = await fetch(url, { cache: 'no-cache' });
    if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
    const spec = absoluteUrls(await res.json());
    el.innerHTML = '';
    const result = await vegaEmbed(el, spec, embedOptions());
    const link = spec.usermeta && spec.usermeta.link;
    if (link) joinLink(result.view, link);
  } catch (err) {
    el.innerHTML =
      `<p class="chart-error">Could not load this chart (${err.message}).<br>` +
      `<span class="muted small">The page must be served over http — see the README.</span></p>`;
    console.error(url, err);
  }
}

/* Charts render when they first scroll into view, so the page is usable
   immediately rather than after fifteen specs have all compiled. */
function observe() {
  const els = [...document.querySelectorAll('.viz[data-spec]')];
  if (!('IntersectionObserver' in window)) {
    els.forEach(renderOne);
    return;
  }
  const io = new IntersectionObserver((entries) => {
    for (const e of entries) {
      if (e.isIntersecting) {
        io.unobserve(e.target);
        renderOne(e.target);
      }
    }
  }, { rootMargin: '300px 0px' });
  els.forEach((el) => io.observe(el));
}

document.addEventListener('DOMContentLoaded', observe);


/* I used relative paths when embedding vega charts, this function rewrites 
    each specs path to the full url */
function absoluteUrls(node) {
  if (Array.isArray(node)) {
    node.forEach(absoluteUrls);
  } else if (node && typeof node == 'object') {
    for (const[key, value] of Object.entries(node)) {
      if (key === 'url' && typeof value === 'string' && !/^[a-z]+:/i.test(value)) {
        node[key] = new URL(value, location.href).href;
      } else {
        absoluteUrls(value);
      }
    } 
  }
  return node;
}