/* ------------------------------------------------------------------
   Chart loader and shared Vega-Lite theme.

   The specs carry no fonts and no chrome colours of their own; they
   come from here, read off the CSS custom properties in css/style.css,
   so the page and the charts are styled from one source. Light theme
   only — there is no theme switching.

   Type roles follow the page: graph titles are serif, everything
   functional (axes, legends, labels, tooltips) is Helvetica.
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
  const series = ['--s1', '--s2', '--s3'].map(token);
  const euc = ['--euc-100', '--euc-200', '--euc-300', '--euc-400', '--euc-500',
    '--euc-600', '--euc-700', '--euc-800', '--euc-900'].map(token);

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
      // Three categorical slots is the documented ceiling for this palette.
      category: series,
      heatmap: euc.slice(0, 7),
      ramp: euc.slice(0, 7),
      ordinal: [euc[3], euc[4], euc[6], euc[8]],
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
  actions: { export: true, source: false, compiled: false, editor: false },
  renderer: 'canvas',
  config: theme(),
  tooltip: { theme: 'light' },
});

/* ------------------------------------------------------------ render */

async function renderOne(el) {
  const url = el.dataset.spec;
  el.innerHTML = '<p class="loading">Loading chart…</p>';
  try {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
    const spec = await res.json();
    el.innerHTML = '';
    await vegaEmbed(el, spec, embedOptions());
  } catch (err) {
    el.innerHTML =
      `<p class="chart-error">Could not load this chart (${err.message}).<br>` +
      `<span class="muted small">The page must be served over http — see the README.</span></p>`;
    console.error(url, err);
  }
}

/* Charts render when they first scroll into view, so the page is usable
   immediately rather than after sixteen specs have all compiled. */
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
