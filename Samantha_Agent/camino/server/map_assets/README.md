# Vendored map runtime

Leaflet **1.9.4** (BSD-2-Clause, see LICENSE.txt), downloaded 2026-09-28.
No npm/build step or third-party runtime script request.

Official release and integrity reference: https://leafletjs.com/download.html
Source: https://unpkg.com/leaflet@1.9.4/dist/leaflet.js and leaflet.css;
license: https://raw.githubusercontent.com/Leaflet/Leaflet/v1.9.4/LICENSE.

Upstream bytes checked against the published SHA-256 (base64):

- JS: `20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=`
- CSS: `p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=`

Local text is identical after CRLF→LF and trailing EOF whitespace normalization.
Local SHA-256:

- leaflet.js: `4f1ac3296897403e0a84881c974dbdf36d9a8488f0ef4b5626a952b1b6190d80`
- leaflet.css: `337bfca5cabd03b39815b2700febe2b3b7edf55921c59cd49f88ecb328212303`

Only circle markers are used; unused default marker/layer-control images and
the developer source map are not bundled or served. No plugin dependencies.
map.js and map.css are Camino code, not upstream Leaflet.

Tiles use https://tile.openstreetmap.org/{z}/{x}/{y}.png only after consent.
Keep visible attribution, native HTTP cache, origin Referer and no credential
forwarding. No downloads/prefetch/offline cache service worker. Provider policy:
https://operations.osmfoundation.org/policies/tiles/ (checked 2026-09-28).
Changing provider requires an explicit code/CSP/privacy review, not a user URL.
