/**
 * check_charts.mjs — compile and render every spec headlessly.
 *
 * Catches the failure modes that are invisible until you open the page: specs
 * that will not compile, lookups that silently join nothing, expressions that
 * throw at runtime, and sort properties Vega-Lite quietly drops in layered
 * specs. Also writes a PNG of each chart to /tmp/afm-charts so you can eyeball
 * them without a browser.
 *
 * Optional dev tool — the site itself has no build step and no dependencies.
 *
 *   npm install vega vega-lite canvas
 *   node scripts/check_charts.mjs
 */

import fs from 'fs';
import path from 'path';
import * as vl from 'vega-lite';
import * as vega from 'vega';

const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const SPECS = path.join(ROOT, 'specs');
const OUT = '/tmp/afm-charts';

// Mirrors the theme in js/main.js closely enough to spot layout problems.
const S = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#008300', '#4a3aa7', '#e34948'];
const BLUES = ['#cde2fb', '#9ec5f4', '#6da7ec', '#3987e5', '#256abf', '#184f95', '#0d366b'];
const config = {
  background: '#fcfcfb',
  font: 'sans-serif',
  title: { color: '#0b0b0b', fontSize: 13, fontWeight: 600, anchor: 'start', subtitleColor: '#898781' },
  axis: {
    labelColor: '#898781', labelFontSize: 11.5, titleColor: '#52514e', titleFontSize: 11.5,
    titleFontWeight: 600, gridColor: '#e1e0d9', domainColor: '#c3c2b7', tickColor: '#c3c2b7',
  },
  axisX: { grid: false, labelAngle: 0 },
  axisY: { domain: false, ticks: false },
  legend: {
    labelColor: '#52514e', labelFontSize: 11.5, titleColor: '#52514e',
    titleFontSize: 11.5, titleFontWeight: 600, symbolStrokeWidth: 0, symbolSize: 90,
  },
  view: { stroke: null, continuousWidth: 620, continuousHeight: 300 },
  range: { category: S, heatmap: BLUES, ramp: BLUES },
  bar: { cornerRadiusEnd: 4 },
  rect: { stroke: '#fcfcfb', strokeWidth: 2 },
  arc: { stroke: '#fcfcfb', strokeWidth: 2 },
  line: { strokeWidth: 2 },
  point: { size: 70, filled: true },
  circle: { size: 70 },
  text: { color: '#52514e', fontSize: 11.5 },
  geoshape: { stroke: '#fcfcfb', strokeWidth: 0.5 },
};

const loader = vega.loader({ baseURL: 'file://' + ROOT + '/', mode: 'file' });
fs.mkdirSync(OUT, { recursive: true });

let failed = 0;
const warnings = [];

for (const file of fs.readdirSync(SPECS).sort()) {
  if (!file.endsWith('.json')) continue;
  let spec;
  try {
    spec = JSON.parse(fs.readFileSync(path.join(SPECS, file), 'utf8'));
  } catch (e) {
    console.log(`JSON  ${file}: ${e.message}`);
    failed++;
    continue;
  }
  if (spec.width === 'container') spec.width = 760;

  try {
    // Vega-Lite logs dropped sort properties and conflicting scales through
    // console.warn; capture them rather than letting them scroll past.
    const realWarn = console.warn;
    console.warn = (...m) => warnings.push(`${file}: ${m.join(' ')}`);
    let compiled;
    try {
      compiled = vl.compile(spec, { config });
    } finally {
      console.warn = realWarn;
    }
    const view = new vega.View(vega.parse(compiled.spec), { renderer: 'none', loader });
    await view.runAsync();

    // A lookup that joins nothing still "works" — report row counts so an
    // empty join is visible rather than silent.
    const rows = Object.keys(view.getState({ data: vega.truthy }).data || {})
      .filter((k) => !k.startsWith('_'))
      .map((k) => { const d = view.data(k); return d && d.length ? `${k}:${d.length}` : null; })
      .filter(Boolean).slice(0, 6).join(' ');

    const canvas = await view.toCanvas(2);
    fs.writeFileSync(path.join(OUT, file.replace(/\.vg\.json$/, '.png')), canvas.toBuffer());
    console.log(`ok    ${file.padEnd(32)} ${rows}`);
  } catch (e) {
    console.log(`FAIL  ${file}: ${e.message}`);
    failed++;
  }
}

if (warnings.length) console.log('\nWarnings:\n  ' + warnings.join('\n  '));
console.log(failed ? `\n${failed} spec(s) failed` : `\nAll specs compile and render. PNGs in ${OUT}`);
process.exit(failed ? 1 : 0);
