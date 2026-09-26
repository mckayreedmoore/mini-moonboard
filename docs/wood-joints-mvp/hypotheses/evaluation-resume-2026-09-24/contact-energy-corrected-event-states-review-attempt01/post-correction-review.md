# Post-correction review: event-state energy report wording

Read-only follow-up completed September 26, 2026. It checked the corrected
README wording against the frozen producer and point-map parser; it did not run
tests, repeat the DAT scan, run mass integration, or perform a native solve.

## Pins and disposition

- Corrected README SHA-256: `e4d3ac90b06177f96df2cb2a67fd7e392e5d06c25136f9322d9c15741274d430`
- Unchanged result SHA-256: `658c16682e7553d53e555288574ec9d64b57d3dc5f6e0da08d369aa7359d4694`
- Unchanged producer SHA-256: `2a3ca9f4c316b53da284cce2a15bda58fceb0aae48f8f8948d6f70ca777351db`
- Unchanged point-map parser SHA-256: `78887f638b7d3bf8b200e12e03b3ad179f1d53226e285ed2a808b3de0cc3eb0f`

The producer uses `parser.point_key` for both CSV and DAT rows. The parser
defines the key as `(element_fortran_number, igauss, jfaces)`. DAT
`tie/slave/master` tags remain matched-record metadata, not key fields. The
corrected README now states this accurately. The selected states, counts,
energy totals, bounds, and all numerical results remain unchanged.

The earlier [independent review](independent-review.md) remains intact as the
review of the prior README snapshot and records the wording issue it found.
This follow-up closes that documentation correction for the current README.
