/* ------------------------------------------------------------------
   Chart loader and shared Vega-Lite theme.

   Every spec in specs/ is written without colours or fonts of its own.
   The theme below is read from the CSS custom properties on :root, so
   the charts follow the page's light/dark tokens rather than duplicating
   them. Re-rendering on a theme change keeps the two in step.
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
  const series = ['--s1', '--s2', '--s3', '--s4', '--s5', '--s6', '--s7', '--s8'].map(token);
  const font = 'system-ui, -apple-system, "Segoe UI", sans-serif';

  return {
    background: null,
    font,
    padding: 0,
    autosize: { type: 'fit', contains: 'padding', resize: true },
    title: {
      color: ink, fontSize: 13, fontWeight: 600, anchor: 'start',
      subtitleColor: muted, subtitleFontSize: 11.5, offset: 8, dy: -2,
    },
    axis: {
      labelColor: muted, labelFontSize: 11.5, labelFont: font,
      titleColor: ink2, titleFontSize: 11.5, titleFontWeight: 600, titlePadding: 8,
      gridColor: grid, gridWidth: 1, domainColor: axis, tickColor: axis,
      tickSize: 4, labelPadding: 4,
    },
    axisX: { grid: false, labelAngle: 0 },
    axisY: { domain: false, ticks: false, gridDash: [] },
    legend: {
      labelColor: ink2, labelFontSize: 11.5, titleColor: ink2,
      titleFontSize: 11.5, titleFontWeight: 600, symbolStrokeWidth: 0,
      symbolSize: 90, offset: 10, padding: 0,
    },
    view: { stroke: null, continuousWidth: 620, continuousHeight: 300 },
    range: {
      category: series,
      // sequential blue, steps 100 -> 700 from the palette
      heatmap: ['#cde2fb', '#9ec5f4', '#6da7ec', '#3987e5', '#256abf', '#184f95', '#0d366b'],
      ramp: ['#cde2fb', '#9ec5f4', '#6da7ec', '#3987e5', '#256abf', '#184f95', '#0d366b'],
    },
    mark: { tooltip: true },
    bar: { cornerRadiusEnd: 4 },
    rect: { stroke: surface, strokeWidth: 2 },
    arc: { stroke: surface, strokeWidth: 2 },
    line: { strokeWidth: 2 },
    point: { size: 70, filled: true },
    circle: { size: 70 },
    rule: { color: axis },
    text: { color: ink2, font, fontSize: 11.5 },
    geoshape: { stroke: surface, strokeWidth: 0.5 },
    concat: { spacing: 26 },
    facet: { spacing: 22 },
  };
}

const embedOptions = () => ({
  actions: { export: true, source: false, compiled: false, editor: false },
  renderer: 'canvas',
  config: theme(),
  tooltip: { theme: document.documentElement.dataset.resolvedTheme || 'light' },
});

/* ------------------------------------------------------------ render */

const mounted = new Map(); // element -> spec url

async function renderOne(el) {
  const url = el.dataset.spec;
  el.innerHTML = '<p class="loading">Loading chart…</p>';
  try {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
    const spec = await res.json();
    el.innerHTML = '';
    await vegaEmbed(el, spec, embedOptions());
    mounted.set(el, url);
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

/* --------------------------------------------------------- theming */

function resolvedTheme() {
  const set = document.documentElement.dataset.theme;
  if (set) return set;
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

function syncToggleLabel() {
  const btn = document.getElementById('theme-toggle');
  if (!btn) return;
  const next = resolvedTheme() === 'dark' ? 'light' : 'dark';
  btn.textContent = next === 'dark' ? 'Dark' : 'Light';
  btn.setAttribute('aria-label', `Switch to ${next} theme`);
  document.documentElement.dataset.resolvedTheme = resolvedTheme();
}

let rerenderTimer;
function rerenderAll() {
  clearTimeout(rerenderTimer);
  rerenderTimer = setTimeout(() => {
    for (const el of mounted.keys()) renderOne(el);
  }, 60);
}

function initTheme() {
  let stored = null;
  try { stored = localStorage.getItem('afm-theme'); } catch { /* private mode */ }
  if (stored === 'light' || stored === 'dark') document.documentElement.dataset.theme = stored;
  syncToggleLabel();

  document.getElementById('theme-toggle')?.addEventListener('click', () => {
    const next = resolvedTheme() === 'dark' ? 'light' : 'dark';
    document.documentElement.dataset.theme = next;
    try { localStorage.setItem('afm-theme', next); } catch { /* ignore */ }
    syncToggleLabel();
    rerenderAll();
  });

  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
    if (!document.documentElement.dataset.theme) {
      syncToggleLabel();
      rerenderAll();
    }
  });
}

/* ------------------------------------------------------------- go */

document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  observe();
});
