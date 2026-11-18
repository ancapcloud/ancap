# ANCAP local picomatch security fork

Source: picomatch 4.0.7 (MIT; original LICENSE retained).
Advisory: https://github.com/advisories/GHSA-fc5q-39xc-vjpf
At 18 November 2026 the registry has no patched release.

Only lib/parse.js changes: repeated extglobs with one wildcard-containing branch
use the existing safe literal fallback, unless the existing analyzer can flatten
a star-extglob sequence into a character class. This prevents nested unbounded
quantifiers from +(*) and +(*a), including prefixed/suffixed patterns and the
maxExtglobRecursion=false option. These risky globs intentionally match their
literal spelling rather than expanding; ordinary file globs, literal alternations,
optional/negated extglobs and supported character-class rewrites stay available.

The private package is named @ancap/picomatch-safe and retains version 4.0.7 for
peer compatibility. ancapPatch identifies the local patch; it is not an upstream
release. The root picomatch file dependency/override makes all consumers resolve
this reviewed source. npm audit does not assess local forks: a clean audit alone
is not proof of this mitigation. Child-process regression tests demonstrate the
attack no longer stalls and verify normal matching and installed resolution.
Both project copies must remain identical until replaced by a verified upstream
fix; do not suppress the advisory or silently substitute an older release.
