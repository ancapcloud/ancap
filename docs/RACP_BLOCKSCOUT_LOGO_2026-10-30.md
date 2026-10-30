# Blockscout logo compatibility — 2026-10-30

Blockscout reported `Unable to load image` for the public rACP SVG. The
production proxy served token artwork with `Cross-Origin-Resource-Policy:
same-site`, preventing embedding on an external explorer.

- Re-rendered the existing SVG as a 48×48 PNG at `/racp-logo.png`.
- Added a narrow nginx location for `/racp-logo.png` and `/racp-logo.svg` with
  `Cross-Origin-Resource-Policy: cross-origin` and public, credential-free CORS.
- Deployed the asset and proxy configuration without rebuilding unrelated work.
  Updated the remote source asset as well as the running frontend container.
- `nginx -t` passed before graceful reload. Public HTTPS GET returned 200,
  `image/png`, 1515 bytes, and the intended cross-origin headers. Downloaded
  image is exactly 48×48 and byte-identical to the source PNG.

Form URL: https://ancap.cloud/racp-logo.png

The authenticated Blockscout form has not been submitted or directly retested.
Token profile review/approval remains pending; other distribution status is in
[the distribution record](RACP_PUBLIC_DISTRIBUTION_2026-10-30.md).
