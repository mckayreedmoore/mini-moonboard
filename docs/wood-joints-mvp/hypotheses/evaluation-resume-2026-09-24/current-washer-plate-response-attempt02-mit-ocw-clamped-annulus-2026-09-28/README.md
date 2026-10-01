# Washer plate-response source attempt 02: provisional MIT OCW annular benchmark

**Reviewed:** 2026-09-28. **Candidate context:** `led-clearance-2x6-runner-seated-blocks-v1`.
**Criterion:** `washer_bending` remains pending. **Benchmark status:** provisional pending coordinator review of the primary-source transcription and calculation.

## Result

MIT OpenCourseWare provides a directly accessible, first-party teaching source with an axisymmetric elastic annular-plate example: uniform transverse pressure; both inner and outer edges clamped; radii `a = 1`, `b = 10`; classical thin-plate flexural rigidity; and an explicit deflection solution and four clamped-edge equations. The PDF publishes the solution coefficients rounded to one decimal place. I independently solved the four boundary equations without using those rounded coefficients and evaluated the response at `r/a = 5`.

For the dimensionless response `W = D w / (P a^4)`, the independently solved coefficients are approximately `[-10.7602000748, 7.17724045448, -3.65678083414, -7.19286545448]`; at `r/a = 5`, `W = 17.5518541636`. The source’s one-decimal coefficient vector is a coarse check only and does not reproduce that interior response closely enough for a precision test by direct substitution. The exact equation and boundary conditions do define a reproducible numeric answer, but the packet remains provisional until a second reviewer confirms the transcription and independent calculation.

This is a useful candidate for a generic annular-plate response test. It is not the attempted concentric ring-load case and does not match the candidate washer’s finite head/nut footprint or potentially partial/compliant timber-seat support. It does not establish a washer product, candidate demand, response, material strength, capacity, D/C, criterion disposition, design acceptance, or fabrication instruction. Do not transfer its boundary conditions to the WJ24 washer roles.

## Source

- Tomasz Wierzbicki, MIT OpenCourseWare, 2.080J Structural Mechanics, Fall 2013, “Recitation 5: Summary of Plate Bending,” official resource page and direct MIT-hosted PDF are pinned in [`source-observations.json`](source-observations.json).
- The example appears on PDF page 2 (printed page `5-2`) and the rounded illustrative coefficient solution on PDF page 3 (printed page `5-3`). The official PDF is returned by the read-only web source route as a nine-page PDF. The repository does not contain a source-file copy; the direct source URL is the stable citation route and remote bytes were not locally hashed.

## Benchmark definition and calculation

See [`benchmark-calculation.md`](benchmark-calculation.md) for the stated plate equation and solution, dimensionless boundary-value system, input/response normalization, numeric expected values, and applicability limits. No maintained helper, test, CAD, solver input, or candidate mechanics file was changed.

## Verification

From the repository root, run:

```sh
python3 docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-washer-plate-response-attempt02-mit-ocw-clamped-annulus-2026-09-28/verify_packet.py
```

The verifier checks packet checksums, the JSON structure, and hashes of the pinned attempt01 predecessor files. It does not fetch or certify mutable remote pages, and it does not compute a washer or assembly result.
