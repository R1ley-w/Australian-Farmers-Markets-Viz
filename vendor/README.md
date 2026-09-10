# Vendored Vega libraries

The page loads Vega from here rather than from a CDN, so the visualisation
works offline, is not exposed to a CDN outage or a version bump, and the
exact library versions live in the repo alongside the specs that depend on
them.

| File | Package | Version |
|---|---|---|
| `vega.min.js` | [vega](https://www.npmjs.com/package/vega) | 5.30.0 |
| `vega-lite.min.js` | [vega-lite](https://www.npmjs.com/package/vega-lite) | 5.21.0 |
| `vega-embed.min.js` | [vega-embed](https://www.npmjs.com/package/vega-embed) | 6.26.0 |

All three are BSD-3-Clause, © University of Washington Interactive Data Lab.
Unmodified minified builds, taken straight from the published npm packages.

## Updating them

```bash
npm install vega@5.30.0 vega-lite@5.21.0 vega-embed@6.26.0
cp node_modules/vega/build/vega.min.js              vendor/
cp node_modules/vega-lite/build/vega-lite.min.js    vendor/
cp node_modules/vega-embed/build/vega-embed.min.js  vendor/
```

The specs declare `https://vega.github.io/schema/vega-lite/v5.json` as their
`$schema`. That is an identifier, not a fetch — nothing on the page requests
it at runtime — but keep the vendored vega-lite on major version 5 so the two
stay in step.

After changing a version, re-run `node scripts/check_charts.mjs` to confirm
every spec still compiles and renders.
