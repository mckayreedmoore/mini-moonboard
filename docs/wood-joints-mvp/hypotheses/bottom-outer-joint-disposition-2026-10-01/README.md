# Bottom outer left joint: simultaneous source actions and contact context

October 1, 2026. This additive packet joins the four bolts, three modeled
contact pairs and complete cleat free body of the reviewed
`led-clearance-2x6-runner-seated-blocks-v1` wood-joints candidate. It preserves
the existing A1/A12/K12 rear responses and every reviewed geometry and
hardware count. It adds no native solve or adopted resistance.

The source join passes in all 21 existing load states. It resolves an outdated
geometry dependency: the current exact contact graph and face atlas already
contain the finished mating areas that the older WJ24 diagnostic left null.
The flagged `side_1` bolt still has a conditional unadjusted ratio of
`1.0945088665197509`; this packet does not resolve that strength disposition or
accept a complete joint.

## Scope and source identities

The cleat is `bottom_outer_left_cleat`; its hosts are `base_side_left` and
`base_rail_bottom_left`. The four axes are
`bottom_outer/clip_horizontal_bottom_left_1/{rail,side}_{1,2}`. The existing
52-bolt report supplies their individual two-receiver lateral reference rows
and separate same-state outer ties. The raw report remains unchanged at
SHA-256 `6551861db1112c91b87c5705bbceb3bb26f55f0d7e70029a74d828519425145e`.

The pinned [three-case freeze](../upper-frame-joint-review-2026-09-30/freeze.json)
binds each native model, response and all-body audit. Each case has load
factors `0.1, 0.2, 0.3, 0.45, 0.675, 0.925, 1.0`. The producer verifies all
source hashes before calculating. It reuses the reviewed signed-plane and
outer-tie checkers, then explicitly compares their native force and rounding
radius evidence with the old report and physical action records.

The graph verifier authenticates 142 source pins, including the 50 finished
STEP solids and current geometry sources. The atlas supplies the exact
opposed faces and hole-trimmed intersection regions; its areas must agree
with the graph and with the sum of the four native contact-cell areas.
The [method review](method-review.md) records exact face IDs, normals,
extents, STEP hashes and NDS applicability limits.

| Contact pair | Current finished shared area, mm² | Source cells | Grain-direction context |
| --- | ---: | --- | --- |
| Rail / cleat | 10,552.972706618 | `contact_58_0..3` | Both receivers perpendicular to proposed grain |
| Side / cleat | 10,552.972706618 | `contact_88_0..3` | Both receivers perpendicular to proposed grain |
| Rail / side, direct host path | 5,322.57 | `contact_56_0..3` | Rail parallel to proposed grain; side perpendicular |

All three graph records have zero common solid volume and nominal opposed
planar touch. Exact nominal touch is geometry evidence; active contact comes
from the corresponding frozen source force/law, rather than from area alone.
This is not installed fit or a physical pressure/stiffness qualification.

## Calculated coverage and results

| Output | Count |
| --- | ---: |
| Simultaneous joint states | 21 |
| Preserved four-bolt reference rows | 84 |
| Native contact-cell states | 252 |
| Three-pair contact states | 63 |
| Complete cleat force/moment balance states | 21 |

The 252 contact states contain 112 resolved compressive cells and 140
resolved open cells, with no ambiguous rounded-boundary state. Each cell is
joined to its original SPRINGA identity, inventory row, physical receiver,
point, unit normal, area and compression-only law. Signed native RF,
action/reaction vectors and component radii agree. Native force and source
table-force intervals must intersect; numerical spring-ground RF stays
excluded from the physical free body.

The producer computes force divided by each modeled cell's source area.
This is a **modeled cell average**, not actual peak pressure, a finite contact
traction solution, or a calibrated wood-bearing law. The conditional
DF-L No. 2 reference is `Fc⊥=625 psi` (`4.309223308230226 MPa`). A comparison
is emitted only for a resolved compressive cell whose receiver normal is
perpendicular to its proposed grain. Across all 504 receiver contexts,
182 such comparisons apply, 238 open-cell comparisons are explicitly null,
and 84 parallel-rail contexts exclude this perpendicular-grain method.
Material/orientation facts remain visible for open cells without assigning
them a zero bearing ratio.

All cell-average peaks below occur at A1 full load. No comparison is fully
adjusted or an accepted bearing utilization.

| Contact pair | Peak modeled cell average, MPa | Corresponding unadjusted perpendicular-grain quotient | Peak pair compression force, N |
| --- | ---: | ---: | ---: |
| Rail / cleat | 0.0469222553 | 0.0108887964, either receiver | 187.0846418 |
| Side / cleat | 0.2345212926 | 0.0544231004, either receiver | 621.70177 |
| Rail / side | 0.3118800129 | 0.0723749944, side only; rail excluded | 425.54263 |

The cleat free body uses its **exact 16-interface source inventory**: four
lateral planes, four separate outer-seat axial ties and eight cleat contact
cells. It includes all source physical nodal body loads scaled to the same
increment. The four direct host-to-host contact cells remain in the joint
contact register; they do not touch the cleat and are not inserted into its
free body. All 21 cleat balances reproduce the frozen all-body residuals
with the original `0.1 N / 2 Nmm` gates and RF-rounding intervals.
The largest absolute residual components are `8.5072e-5 N` and
`0.00354334 Nmm`, at A1 full load. Force transport about the stated descriptor
midpoint is bookkeeping, not an internal bolt bending result.

For the flagged A1 full-load `side_1` bolt, the preserved lateral resultant
is `661.948743401738 N`, its conditional unadjusted Mode IV reference is
`604.7906633288045 N`, and its separate tie is `197.1248 N`. The simultaneous
forces at the other three bolts and all contact cells remain available.
Contact compression does not cancel, reduce or replace that actual source
bolt demand; summing four force magnitudes does not establish group strength.

## Strength disposition still required

The lateral scenario uses smooth nominal quarter-inch diameter, SG 0.50,
zero gap and unadopted `Fyb=45,000 psi`. The official 2024 NDS Table 12A's
45-ksi entry starts at half-inch diameter; it does not qualify quarter-inch
`Fyb`. The 106-ksi Grade 5 empirical estimate is also not an adopted minimum.
The [original reference packet](../remaining-single-shear-reference-2026-10-01/README.md)
and method review preserve these boundaries.

Complete disposition requires a supported hardware/material basis and
applicable adjustment, spacing/end/edge and group terms, plus the simultaneous
local member/finished-section, splitting and combined axial/lateral/steel
checks. Parallel-grain compression at the direct rail receiver needs its own
applicable method. Physical contact-law applicability remains separate from
this source-cell arithmetic. This packet checks the whole cleat boundary;
it does not claim complete host-member boundaries or finished bored-ligament
tractions. No favorable adjustment, new bolt size, altered model, physical
inspection requirement or external sign-off is introduced here.

The [adjustment applicability note](adjustment-applicability.md) identifies
the exact quarter-inch threshold, actual 33 mm station spacing, receiver grain
directions and conditional end-distance inputs. The smaller-diameter unity
exceptions do not apply; an NDS row must still be defined from the applicable
load/group arrangement. A rail-cleat parallel-tension sensitivity is
`CΔ=43.350/44.450=0.975253`; it is not adopted or transferred to `side_1`.
The separate axial ties also require applicable angled-to-fastener loading
and axial bearing checks under NDS §12.3.9, with any applicable equivalent
shear-area geometry check under §12.5.1.2(b). A lateral-plane reference alone
does not settle those complete-joint requirements.

## Reproduction and validation

Run from the repository root, using the project's Python environment:

```sh
.venv/bin/python docs/wood-joints-mvp/hypotheses/bottom-outer-joint-disposition-2026-10-01/produce.py \
  --source-report /tmp/mini-moonboard-remaining-single-shear-reference-2026-10-01.json \
  > /tmp/mini-moonboard-bottom-outer-joint-2026-10-01.json
.venv/bin/python -m unittest discover \
  -s docs/wood-joints-mvp/hypotheses/bottom-outer-joint-disposition-2026-10-01 \
  -p 'test_source_guards.py' -v
```

The parent run and Ruff pass. Fifteen tests exercise corrupted receiver,
area, sign, radius, native source identity, nonfinite/tensile force, disjoint
native/table interval and numerical-ground records, plus exclusion of open,
ambiguous and parallel-grain comparisons. An independent source/code review
and independently reconstructed numerical oracle are recorded separately.
The [source/code review](source-code-review.md) has no unresolved material
finding. The [independent calculation review](independent-calculation-review.md)
reconstructs all 504 native scalar force components and every cleat balance
without the producer's balance helper. Its full producer replay is
byte-identical to the frozen raw result. Parent also ran the independent
verifier successfully; the force and moment interval excesses are zero.

```sh
.venv/bin/python docs/wood-joints-mvp/hypotheses/bottom-outer-joint-disposition-2026-10-01/parent_verify.py
```

- Producer SHA-256: `a941dceee5c002068e9920cfe41f62270e11ff399367fdf9494c445a06d8a86d`.
- Test SHA-256: `66a99f388c19c0df3bd99eaa2951a035a9b5496e8c9facc8a7b32859a0de71b2`.
- Independent verifier SHA-256: `e49fbefe980e009e40b352035988c27db5b0bab86865a4792b3d2aa5efd73486`.
- Local raw result SHA-256: `fcf393be26c433daf760a6afcf9fd6260d88f04f43a6234def960bbba4789029`.

Raw result data stays local. Publication contains code and summaries only.
`PASS_SOURCE_JOIN_AND_CONDITIONAL_REFERENCE_CONTEXT_ONLY` is a bounded
source-join status: joint acceptance, adopted capacity, physical pressure
qualification, geometry changes and formal criterion passes remain false.
