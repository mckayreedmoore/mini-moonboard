# Independent correctness review — ordinary-joint actuation/map-binding attempt02

Date: 2026-09-28  
Result: **PASS WITHIN SCOPE; NO CLAIM-PROMOTION FINDING**

## Scope and integrity

Reviewed `ordinary-joint-actuation-map-binding-attempt02-ordered-freeze-2026-09-28/` for packet/source integrity, the static-time clarification, and promotion of unqualified maps or results. The packet checksum passed from its directory. The source manifest declares and contains 58 entries; all 58 passed when checked from the repository root. No target packet file was changed. This review does not accept mechanics.

## Findings

The clarification is accurate. The pinned attempt01 deck uses `*STATIC`, a unit endpoint in its static step-time ramp. The CalculiX 2.21 manual, §6.9.1, states that the time dimension is not involved in a static analysis and describes the finite static step length as an increment parameter. Thus “unit static step-time interval” correctly distinguishes the failed ramp from a physical second or transient duration. [CalculiX 2.21 User’s Manual](https://www.dhondt.de/ccx_2.21.pdf)

The successor does not promote any unqualified map or result:

- It remains `NOT_FREEZE_READY`, with native execution, mechanical acceptance, new-load selection, and geometry-change flags false.
- `active_map_set` is explicitly source-bound to attempt01’s N+ deck only. The deck’s A00–A03 maps stay in preflight; map equivalence or qualification is a separate unresolved gate. A01–A03 are explicitly still unqualified for that history.
- A00’s known-answer result remains limited to its small global-Y body-force fixture; the packet says it does not qualify A01–A03 or the external-port motion.
- The T02 and T03 coupons remain `NOT_RUN`, prerequisite flags remain false, and each coupon’s scope is limited to its method/topology. Neither is described as ordinary-joint acceptance.
- History/method, acceptance thresholds, map qualification, immutable joint freeze, and response audit remain unresolved or not ready. The packet describes no selected physical/service history and grants no response, demand, capacity, criterion, fabrication, or climbing disposition.

No substantive source-binding, factual, or result-scope mismatch was found in this bounded review.

## Exact packet hashes

- `README.md`: `7d401bccea625796fda3b8ad823b4a90a1951e21de1865e5b7fa08c46eec1daf`
- `decision-sequence.json`: `eb0e0d0c2756df5102c1dcc63bbbc3642c1e8123bc4ade04e1d4f824a3f95df4`
- `source-pins.json`: `ea01c3b3ddeb1bd8e5c1f7c21c906a746a8e8bef02ee9fe400874093164f3fa7`
- `SHA256SUMS`: `5e36729626eac815c14cfe7c6f0061ee7994ba79b6ea2b0d09d332077e5a0588`
- `SOURCE-SHA256SUMS`: `bebe192ec68236b2c775010a679fe20229b6a992f00f3f8bfe3b20b996d49290`
