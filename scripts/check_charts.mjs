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
const S = ['#457b45', '#7a4208', '#4199c9', '#b68611']; // eucalypt, bark, waterhole, gold
const EUC = ['#e5f5e5', '#cce9cb', '#b1d9b0', '#90c48f',
             '#6eaa6d', '#4d8d4d', '#357336', '#245b26', '#19421a'];
const SERIF = 'Georgia, serif';
const SANS = 'Helvetica, Arial, sans-serif';
const config = {
  background: '#fdfcf9',
  font: SANS,
  title: { font: SERIF, fontWeight: 400, fontSize: 15, color: '#1f2417',
           anchor: 'start', subtitleFont: SANS, subtitleColor: '#7c7f6e' },
  axis: {
    labelFont: SANS, labelColor: '#7c7f6e', labelFontSize: 11.5,
    titleFont: SANS, titleColor: '#4a4f3e', titleFontSize: 11.5,
    titleFontWeight: 700, gridColor: '#e3e0d4', domainColor: '#c3bfc4', tickColor: '#c3bfc4',
  },
  axisX: { grid: false, labelAngle: 0 },
  axisY: { domain: false, ticks: false },
  legend: {
    labelFont: SANS, labelColor: '#4a4f3e', labelFontSize: 11.5,
    titleFont: SANS, titleColor: '#4a4f3e',
    titleFontSize: 11.5, titleFontWeight: 700, symbolStrokeWidth: 0, symbolSize: 90,
  },
  view: { stroke: null, continuousWidth: 620, continuousHeight: 300 },
  range: { category: S, heatmap: EUC.slice(0, 7), ramp: EUC.slice(0, 7),
           ordinal: [EUC[3], EUC[4], EUC[6], EUC[8]] },
  bar: { cornerRadiusEnd: 3 },
  rect: { stroke: '#fdfcf9', strokeWidth: 2 },
  arc: { stroke: '#fdfcf9', strokeWidth: 2 },
  line: { strokeWidth: 2 },
  point: { size: 70, filled: true },
  circle: { size: 70 },
  text: { font: SANS, color: '#4a4f3e', fontSize: 11.5 },
  geoshape: { stroke: '#fdfcf9', strokeWidth: 0.5 },
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
