# Source and route audit

## Findings

1. **The primary source and case context are real.** UNT's indexed scan page
   12 identifies the report title and describes an outer simply supported,
   inner free annular plate with uniform load on a concentric circle; it labels
   the page `CASE III`. The searchable OSTI report text identifies the general
   annular cases and says response constants are tabulated. This is enough to
   show that Heap ANL-6905 is relevant to an idealized concentric ring-load
   plate case, not enough to validate a helper.
2. **The case's OCR does not expose a reliable equation/sign transcription.**
   The UNT page returns equation OCR such as broken subscripts, exponents,
   fractions, and detached symbols across the moments, slope, and deflection
   sections. It also corrupts the continuity conditions. I could not use that
   text to independently recover the governing expressions or sign convention.
3. **A matching table answer is not established.** The accessible OSTI index
   says Table II reports maximum-deflection and maximum-moment constants for
   selected Poisson ratio, radius ratios, and load positions. The text
   available through search does not expose a legible table row and column
   alignment that binds a specific coefficient to Case III, its exact
   geometry/load location, and the relevant response quantity. No number was
   selected or reconstructed in this review.
4. **The route failures are accurately described as attempt/tool limits, with
   one useful caveat.** OSTI's PURL timed out in the web reader. The UNT
   page-image click returned an internal error in this review, and direct
   high-resolution and medium-resolution image URLs were not accessible
   through the reader. The producer recorded a `Cache miss` for its image-click
   attempt; I could not reproduce that exact error string, but reproduced the
   failure to retrieve image bytes. Direct local `urllib` requests to the OSTI
   PURL, UNT scan, high-res image, medium-res image, and UNT record all failed
   at DNS resolution. These outcomes do not show that either institution's
   host is globally unavailable.
5. **UNT advertises a downloadable report PDF.** The UNT bibliographic search
   result for ARK `metadc868796` confirms Heap, ANL-6905, 41 pages, and says
   “PDF Version Also Available for Download.” The record page itself returned
   a cache miss in this review; the PDF bytes were not obtained. The producer
   packet correctly does not claim that the report is absent, but a resumed
   attempt should try that advertised download or another primary copy before
   treating the source obstacle as persistent.
6. **Failing closed before code is appropriate.** A response helper with a
   “known-answer” test would be unverified if the expected answer, equation
   symbols, and signs were guessed from damaged OCR. The packet does not
   invent a formula or numeric answer. The source gap therefore justifies
   deferring the helper and tests while leaving the method gate open.
7. **No candidate result was generated.** The packet makes no WJ24 washer
   response, strength, capacity, demand, D/C ratio, or `washer_bending`
   disposition claim. At review time,
   `mini_moonboard/washer_plate_response.py` and
   `tests/test_washer_plate_response.py` were absent. No CAD or native solver
   activity was part of this review.

## Reproduced route observations

| Route | Independent observation on 2026-09-28 | What this supports |
|---|---|---|
| [OSTI PURL for report 4005214](https://www.osti.gov/servlets/purl/4005214) | Web open failed with `(400) Timeout fetching`. Local Python `urllib` failed with `Temporary failure in name resolution`. OSTI search results returned report OCR, including design text about Table II, but no rendered page. | The exact PDF/page layout was not obtained by these routes. This is not a claim of source absence. |
| [UNT printed page 12 / scan 14](https://digital.library.unt.edu/ark:/67531/metadc11594/m1/14/) | Web open returned HTML/OCR. Lines 24–36 identify the page and loading/support description; lines 42–53 contain boundary/continuity OCR; lines 58–83 and 94–120 contain visibly damaged formula OCR; lines 124–126 identify `CASE III`. | Case context is readable, while exact equations/signs are not reliably transcribable from this OCR. |
| UNT high-res and medium-res page-image routes | Direct web opens said the URLs were not accessible through the reader. Clicking the page image produced an internal error in this review. Local Python requests failed at DNS. | No source image bytes were inspected. Producer's distinct `Cache miss` wording was not reproduced, but the image retrieval failure was. |
| [UNT bibliographic record](https://digital.library.unt.edu/ark:/67531/metadc868796/) | Search result confirms the report metadata, 41-page length, and advertises a PDF download. Web open returned `Cache miss`; local Python request failed at DNS. | A PDF is advertised and merits a targeted retrieval attempt. Its bytes and legibility were not confirmed here. |

The UNT OCR page and catalog record, along with the OSTI report index, are
primary-source or archival records for this report. Search-result OCR is used
only to establish context and observed indexing; it is not substituted for an
equation or numeric benchmark. The browser's inaccessible-image errors varied
between attempts, so this audit records the outcomes observed here rather than
claiming a stable server-side outage.

## Local integrity checks

The producer's verifier completed with:

```text
OK: packet checksums and prior T06 context pins match
```

It checked four packet payload files against the producer's `SHA256SUMS`, then
checked four pinned files from the prior T06 washer-method packet against
`source-pins.json`. This verifies local packet integrity, not remote content.

No formula, expected numeric response, candidate demand, or pass/fail
criterion value is asserted in this review.
