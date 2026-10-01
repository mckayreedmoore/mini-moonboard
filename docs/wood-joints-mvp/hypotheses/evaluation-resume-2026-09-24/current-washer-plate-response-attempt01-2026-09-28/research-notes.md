# Heap ANL-6905 route and OCR observations

This note records why the benchmark gate failed closed. URLs below identify the primary report and its archival scan; the repository does not contain a downloaded report image or PDF.

## What the primary indexed text establishes

The report metadata identifies J. C. Heap, ANL-6905, Argonne National Laboratory, April 1964, OSTI ID 4005214 and DOI 10.2172/4005214. UNT’s indexed printed page 7 says the generalized cases are annular plates with a concentric load between the inner and outer edges and lists four inner/outer edge-condition families. Printed page 8 distinguishes the four generalized cases and six simplified cases; it identifies the last two simplified cases as solid plates. Printed page 12 is an annular case page: its extracted description says outer simply supported, inner free, and a uniform load on a concentric circle; the extracted case label is III.

OSTI’s searchable report text also describes Table II as containing maximum-deflection and maximum-moment constants for selected Poisson’s ratio and radius ratios. The indexed row data include candidate ratios and numbers, but the OCR extraction does not preserve reliable column boundaries or unambiguously align each coefficient with its case, deflection/moment heading, and load position.

## Exact route observations on 2026-09-28

- UNT page route: `https://digital.library.unt.edu/ark:/67531/metadc11594/m1/14/` returned HTML/OCR for printed page 12. That output showed the case description, partial boundary-condition text, and damaged formulas. OCR strings around the continuity conditions and equations are not a dependable transcription of mathematical symbols.
- Clicking the UNT page image led to `https://digital.library.unt.edu/ark%3A/67531/metadc11594/m1/14/high_res/` and returned `Cache miss`.
- Direct opens of the page’s `high_res` and `med_res_d` image routes were rejected as inaccessible by the web reader. No image bytes were obtained for inspection.
- Primary PDF route: `https://www.osti.gov/servlets/purl/4005214`. The web reader’s direct open failed with `(400) Timeout fetching`. Its search index did return source OCR, including abstract/design text and some of Table II, but not a readable rendered page. A screenshot attempt reported that the retrieved content was not available as `application/pdf` to the screenshot tool.
- A direct local `urllib` fetch attempt failed at DNS resolution in the execution environment. This records the observed environment limitation; it is not a claim that the source host is offline.
- UNT’s alternate bibliographic record `https://digital.library.unt.edu/ark:/67531/metadc868796/` confirms the report identity and that UNT holds a 41-page item. The opened route is a record page, not an independently legible second mathematical copy.

## Why no benchmark was frozen

The page OCR lets a reader infer parts of the case, but inference is insufficient for the requested independent symbol/sign verification. The printed page 12 equations are too damaged to distinguish all powers, ratios, subscripts, and signs reliably. Table II has numeric OCR, but its case headings and column alignment are not intact enough to bind one entry to a known geometry/load location and to either the deflection or moment coefficient. A value must not be selected by guessing its column.

Thus the exact case equation and exact published answer cannot be reproduced from the accessible evidence. The helper implementation and test suite were intentionally not started. The next attempt needs a legible source image/PDF or another primary copy with the same case and numeric benchmark; until then, no behavior or test vector is asserted.
