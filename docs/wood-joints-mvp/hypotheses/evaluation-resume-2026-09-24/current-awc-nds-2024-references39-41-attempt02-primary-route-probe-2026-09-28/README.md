# T06: AWC NDS-2024 References 39–41 primary-route probe, attempt02

**Search date:** 2026-09-28. **Recorded:** 12:21 UTC.

This append-only, source-only packet tests new AWC-hosted discovery routes after
attempt01's independent review. The new routes were AWC's WordPress REST API
and public sitemap endpoints. The goal was to discover an official AWC reader
target or an edition-bound AWC publication asset containing References 39–41.

## Result

The available web tool could not retrieve the AWC WordPress page API, media
API, sitemap index, page sitemap, or `robots.txt`. It returned “not accessible
via this tool” for each URL, without HTTP status, response headers, redirect
target, or body. No AWC reference page, publication file, viewer target, or
edition-bound primary-publisher source was discovered. The browser result
identifiers and exact URLs are captured in `source-observations.json`.

This is an access-tool boundary only. It does **not** establish that the AWC
endpoints, reader, publication assets, or References 39–41 are absent. The
attempt01 mirror transcription remains unauthenticated, and no assignment of
references 39–41 is promoted. No timber through-bolt combined axial tension +
shear + bending (`N+V+M`) method, capacity, criterion result, or candidate
disposition is established.

## Scope and audit note

The previously attempted AWC landing-page/button, LinkedIn/shortlink, AWC
search-index, Chapter 11, press-release, Accuris preview, and non-AWC mirror
routes were not re-tested as part of this search. One redundant landing-page
open was accidentally included in the same browser batch as the new routes;
it returned 403. That request adds no new evidence and is explicitly excluded
from the result.

The queue snapshot and immutable attempt01/review source records inspected
before the search are listed in `source-pins.json`. The mutable queue digest is
recorded for context and intentionally is not enforced by the verifier.

## Reproduction and integrity

From this directory run:

```sh
python3 verify_source_packet.py
sha256sum -c SHA256SUMS
```

The verifier checks this packet's file checksums and the pinned immutable
attempt01 and review files. It does not fetch URLs, certify browser-tool logs,
or turn inaccessible endpoints into evidence about their contents.
