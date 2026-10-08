/* ------------------------------------------------------------------
   Line-length check.

   The page is held to a maximum of ten words per rendered line. That
   is a property of the rendered line box, not of the source text, so
   it cannot be checked by reading the HTML — this script counts the
   words in every line box of every text block at three viewport
   widths and reports anything over the limit.

   Run a local server first, then:  node scripts/check_lines.mjs

   The limits themselves are the max-width values in css/style.css.
   ------------------------------------------------------------------ */

import { chromium } from 'playwright';
const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
const PORT = process.env.PORT || 8814;
let failed = 0;
for (const width of [1180, 768, 400]) {
const page = await b.newPage({ viewport: { width, height: 1000 } });
await page.goto(`http://localhost:${PORT}/index.html`, { waitUntil: 'networkidle' });
const rows = await page.evaluate(() => {
  const SEL = 'p, li, h1, h2, h3, figcaption .title, .stat .k, .stat .v, blockquote';
  const out = [];
  for (const el of document.querySelectorAll(SEL)) {
    if (el.closest('.vega-embed')) continue;
    if (!el.textContent.trim()) continue;
    if (el.querySelector(SEL)) continue;            // containers only
    const html = el.innerHTML;
    // wrap every word so we can group by line box
    const walk = (node) => {
      if (node.nodeType === 3) {
        const frag = document.createDocumentFragment();
        for (const tok of node.data.split(/(\s+)/)) {
          if (!tok) continue;
          if (/^\s+$/.test(tok)) { frag.appendChild(document.createTextNode(tok)); }
          else { const s = document.createElement('span'); s.className='__w'; s.textContent = tok; frag.appendChild(s); }
        }
        node.parentNode.replaceChild(frag, node);
      } else if (node.nodeType === 1) {
        [...node.childNodes].forEach(walk);
      }
    };
    [...el.childNodes].forEach(walk);
    const lines = new Map();
    for (const w of el.querySelectorAll('span.__w')) {
      const t = Math.round(w.getBoundingClientRect().top);
      if (!lines.has(t)) lines.set(t, []);
      lines.get(t).push(w.textContent);
    }
    el.innerHTML = html;
    const counts = [...lines.values()].map(a => a.length);
    const worst = [...lines.values()].sort((a,b)=>b.length-a.length)[0] || [];
    out.push({
      tag: el.tagName.toLowerCase() + (el.className ? '.'+String(el.className).split(' ')[0] : ''),
      max: Math.max(0, ...counts),
      lines: counts.length,
      sample: worst.join(' ').slice(0, 90),
    });
  }
  return out;
});
const bad = rows.filter(r => r.max > 10).sort((a,b)=>b.max-a.max);
const worst = Math.max(...rows.map(r => r.max));
console.log(`${String(width).padStart(4)}px: ${rows.length} text blocks, longest line ${worst} words, over the limit: ${bad.length}`);
for (const r of bad.slice(0, 40)) console.log(`        ${String(r.max).padStart(2)}  ${r.tag.padEnd(22)} ${r.sample}`);
failed += bad.length;
await page.close();
}
await b.close();
process.exit(failed ? 1 : 0);
