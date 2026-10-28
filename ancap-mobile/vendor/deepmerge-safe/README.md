# ANCAP deepmerge security fork

Vendored from the MIT-licensed npm deepmerge 4.3.1 `dist/cjs.js`, with its original
license and TypeScript definitions. This is a private ANCAP fork, not an upstream
fixed release. Original bundled-source SHA-256: `2e5160f84a1141bd927264afe4d15766f1e6cf07daef182b37ff53fea121de7d`.

Fixes GHSA-gcqx-w48m-w2h4 / CVE-2026-93753: reject __proto__, constructor and
prototype in both target and source copy paths; define own data properties;
abort on proxy failures instead of treating a failed membership check as safe.
Normal recursive merging, enumerable symbols, arrays, custom merge callbacks,
clone=false and merge.all remain available. Dangerous key names are deliberately
excluded. Regression tests run against the installed override during postinstall.

Source: https://github.com/TehShrike/deepmerge/tree/v4.3.1
Advisory: https://github.com/advisories/GHSA-gcqx-w48m-w2h4
Remove the local override only after an upstream fix passes these regressions.
