# Remaining 54 bolts: three-case signed outer-seat actions

October 1, 2026 UTC. The primary took over this source join after the worker
supplied a useful source trace but no reviewable implementation. It reuses
the three authenticated rear responses without changing geometry or solving
another response. The result is `PASS_THREE_CASE_SIGNED_TIE_JOIN_ONLY`:
**1,134 bolt-state records and 2,268 outer-seat records**, covering 54 bolts
at seven increments in each of A12 rear, A1 rear and K12 rear. This is source
and action coverage, not washer resistance, joint acceptance or six-case
completion.

## Result

There are 1,106 positive tensile actions and 28 display-zero actions, with
no negative tie forces. The largest recorded action in this cohort is
**231.1119 N**, on `bottom_outer/clip_horizontal_bottom_left_1/side_2` at A1
rear full load. This maximum is across the three accepted cases only.

The [finished-solid geometry screen](../remaining-candidate-washer-seats-2026-10-01/README.md)
has one partial-support exception: the `center_principal_right_2` nut washer
on `base_principal_center_right`, next to the retained F1–G1 service passage.
The join carries its failed geometry flag and inapplicable hole-only-area
flag into all 21 states. Its full-load tensile actions are:

| Accepted conditional case | Signed tie and inward seat action |
| --- | ---: |
| A1 rear | 3.736414 N |
| A12 rear | 41.45025 N |
| K12 rear | 64.40226 N |

The exception's force is not zero and its partial footprint remains a
resistance dependency. No average-pressure or washer bending calculation is
made. Neither the force magnitudes nor the source-join status waive the
geometry exception.

## Source and sign checks

The partition is the same pinned six-plus-32-plus-54 partition as the geometry
packet. It excludes the primary's six corner bolts, the parallel upper
owner's 32 candidate bolts and all twelve retained frame arrangements. The
raw all-body response contains 104 outer-seat ties; the 54 selected candidate
axes are joined once each in every increment. The narrower corner report
alone does not expose this cohort and is not used as its force inventory.

The pinned corner-register method authenticates the accepted response register
and case statuses, including the accepted direct-master K12 response and its
preserved rejected predecessor. The separate pinned upper-frame freeze
supplies the actual all-body model, response, audit, terminal assessment,
native DAT, deck and applicable serialization bindings. Every frozen case
file is hashed; response/model/deck/native and parent-audit joins must match.
The seven source increment gates and exact load-factor sequence are required.
The reviewed candidate and revision must agree across all three sources.

Each selected tie must have a unique `unilateral_springa_bindings` entry with
law `k * max(q, 0)`, its matching SPRINGA component and matching source
inventory row/element. It is not a bilateral spring or numerical floor anchor.
The source component must retain its native RF/law interval, action-reaction
and domain passes, and exclude numerical-ground RF from physical balance.
The recorded scalar must match that component's native endpoint internal
force. Native files are authenticated; this producer does **not** parse
their RF tokens again or revalidate the native response law.

The source first receiver is matched to the current head seat and second to
the nut seat. Both points and the installation axis are compared with the
geometry source. With head-to-nut normal `n` and signed scalar `T`, the
physical actions must be `T*n` on the head receiver and `-T*n` on the nut
receiver. Their inward directions are respectively `n` and `-n`, so both
signed inward actions are `T`. Source vectors, points, inventory rows and
rounding intervals remain in the local record. Meaningful negative values
reject the tension-only join; values within `1e-9 N` are labeled display zero,
without claiming physical reverse washer contact.

The primary's separate reconstruction agreed across all 1,134 states:
maximum vector difference `2.84e-14 N`, point difference `2.27e-13 mm`, and
axis-component difference `2.22e-16`. A separate direct DAT sample of the
exception's SPR1768 endpoints reproduced all 21 recorded forces and their
equal-and-opposite numerical endpoint actions. This sample does not extend
the producer's native-token parsing claim to every tie.

## Reproduction

Producer SHA-256:
`0c58a7dc6c82ccc2624ee9d3355e2840f738be01961ddaf3f64486700e89e6c9`.
The upper-frame freeze SHA-256 is
`d4ba1c78eb358d25e32819201e9c59e05d425a06d9e4e5cca3dc09d7139ffd73`.
The local reviewed geometry record supplied to `--support-report` must have
SHA-256 `64853898bccf71df62119f0977f29aa612b323d436790b370b5616f7b3cb9fe3`;
its input pins and all 26 finished STEP files are reauthenticated. This is a
frozen geometry record, not an arbitrary replacement JSON report.

```sh
.venv/bin/python docs/wood-joints-mvp/hypotheses/remaining-candidate-washer-demands-2026-10-01/produce.py --support-report /tmp/mini-moonboard-remaining-seats-parent-2026-10-01.json > /tmp/remaining-washer-demands.json
```

The command must exit zero with the counts and exception above. Required
authenticated local evidence includes the broader raw response sources and
the frozen geometry report. Raw JSON and native files remain local; only
code, summaries and review are published. Independent review is recorded
separately. This packet gives no pressure distribution, steel or timber
capacity, stiffness qualification, adopted criterion disposition, inspected
hardware, fabrication authority or climbing release.
