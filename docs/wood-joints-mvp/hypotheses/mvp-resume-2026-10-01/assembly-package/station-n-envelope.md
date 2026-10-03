# Proposed local station ordinary-N envelope

This packet proposes a reproducible local measurement convention for the
108-stack working proposal. The canonical rearward direction
`N = (0, -sin(50°), cos(50°))` and the ordinary 139.7 mm upper coordinate are
unchanged. Station origins come from saved joint interfaces and finite host
exterior faces, rather than whole-member origins. The convention is proposed
for parent disposition; it is not an adopted coordinate rule or exception.
Parent completed `attempt01` successfully. All 126 proposed local datums
have finite results, with no unsupported group or body. The completed
result remains `proposed_local_datums_not_adopted`; numerical completion
does not adopt the convention, exceptions or formal N17 acceptance.

The frozen working manifest reports **225.19791414318078 kg** for the
108-stack proposal. The [order reconciliation](knee-bridge-order.md) keeps
the separate 25 kg equipment allowance and planning-weight assumptions
explicit. This envelope calculation uses no forces or gravity scaling.
The formally reviewed scene still has **104 stacks**; the four added knee
stacks and their working mass do not change that reviewed authority or
establish complete-joint acceptance.

## Original applicability and retained arrangements

The frozen [`ordinary_n_envelope` criterion](../../../criteria.json) asks for
connector and installed-hardware projection from a named datum, with any
exception dimensioned. The [original plan](../../../plan.md#frozen-scope)
requires every station report to name its datum and report the connector,
complete installed hardware and separate tool workspace. The
[decision log](../../../decision-log.md#2026-09-23--establish-separate-wood-joint-mvp-lane)
states that rear-face placement creates no automatic exception.

These documents do not provide a retained-frame-bolt exemption. The twelve
starting arrangements remain part of the revised frame and require their
own current checks. This packet therefore includes all twelve, grouped by
their six recorded receiver pairs, alongside the 92 candidate stacks and
four proposed internal knee stacks. A retained arrangement is identified as
retained; that label does not approve an excessive projection. No permanent
exception found in an older WJ layout is transferred to this proposal.

The 66 Hillman panel/kicker screw cylinders remain a separate inventory.
Their receiver-local projections are reference diagnostics, not a new screw
policy or a substitute for connector-station disposition. Temporary tools,
withdrawal, counterhold and nut-exit paths retain their separate operation
scope and are excluded from this installed comparison.

## Proposed convention

For each current connector and adjacent nonconnector host, group the saved
bolt/interface memberships by their actual connector–host relationship.
Retain source station IDs where recorded; otherwise name the connector and
host explicitly. The local reference anchor is the arithmetic mean of that
group's saved current receiver-bearing midpoint positions. Corrected top
stacks use their corrected geometry and grips. The anchor is derived before
examining envelope results and is shared by the group, rather than selected
independently for whichever bolt gives the most favorable projection.

Trace the canonical-N line through this local anchor toward the front
(`-N`) to the host's named, finite exterior front face. The datum is that
intersection. The line preserves board-local X and T, so an upper joint on
an upright or sloped leg is referenced near that joint, rather than at the
leg's foot. Finite face trims are required: an intersection with an infinite
supporting plane outside the actual face is not an exterior-face datum.
The report retains exact face IDs, anchors, datum XYZ and their sources.
Finite oriented crossings in both N directions check the local anchor and
front exit. Recesses and shoulders keep their actual finite surfaces; the
calculation does not assume that every receiver is convex.

Existing trim holes remain holes. If a specifically identified own bore
needs filling to define the reference timber face, that operation is named
as a datum-only convention, including a matching blind cap where present;
it is not material, bearing or contact evidence.
Unsupported, missing or ambiguous finite intersections are reported for the
specific group. The producer does not move an origin to produce a pass or
silently substitute a remote member minimum or an unbounded face plane.

Compare the complete connector and all its associated installed stack
components against each associated host datum. A connector joining multiple
hosts keeps all those named comparisons. The four proposed knee-spine
internal bolts inherit the spine's existing post and side station datums;
they do not create new origins at their own bolt centers or connector front.
Retained bolt groups use their receiver-local references without a new wood
connector. The fixed N direction and 139.7 mm reference are used throughout.
Screw reference anchors use saved matched finite receiver intervals where
available, with specifically identified finite-crossing results or nulls
for unmatched axes; they do not use a convex-box clipping substitute.

For any global component extremum `n_global`, its station coordinate is
`n_local = n_global - N · datum`. A rearward excess is
`max(n_local_max - 139.7, 0)` and is recorded with the station, host, component
and controlling geometry. Frontward minima are reported too; the original
criterion supplies no separately adopted frontward limit.

## Saved geometry and hardware basis

The completed [ordinary planning packet](ordinary-n-envelope.md) supplies
the frozen installed 108-stack/66-screw inventory and analytical hardware
projections. Its result SHA-256 is
`278407d84e0061ab845ff73fb31dfc5551300a3afb9aa20327a5cca9e6b86ffc`.
This packet reuses those global projections; it changes their reference
coordinates, not the source hardware or geometry. Catalog assumptions,
retained modeled-head proxies and incomplete Hillman head/profile facts
remain explicit. Delivered parts have not been observed.

The [finished feature register](../../current-finished-feature-register-2026-10-01/surfaces.json)
provides finite planar trims and exterior geometry. Its SHA-256 is
`33fff67eee4bc4e96ccef5703f6eebd0d4e004541c6114a4b1da4a5332b2f6eb`.
The matching [axis-feature register](../../current-finished-feature-register-2026-10-01/axis-features.json)
binds the receiver and bore stations. Its SHA-256 is
`bebb4274cdecfb6ad0b0f26850d85a16570c245ea9f7d478c0b05c12b4513e19`.
Saved exterior LINE endpoints support unchanged connector projections;
display meshes and world-axis boxes are not promoted to exact finished
timber projection evidence.

The [top correction](../top-corner-correction/proposal.json), SHA-256
`5932768c7a7d91535f69a90787b32222eb4d165ac6353d3e2ed4daf9e248e2b2`,
binds the corrected cleats and side hosts. Corrected cleat extrema use the
recorded oriented stock box: X 88.9 mm, T 139.7 mm and N 119.7 mm, at the
saved corrected center. Old cleat trims and old descriptor dimensions are
not used as corrected shape evidence. The changed side-host bores leave the
named exterior front face unchanged; the source-derived reuse is identified
explicitly rather than treating all old finished geometry as current.
An N trace that could intersect a replaced old or new bore is specifically
unresolved; unchanged exterior geometry does not authenticate an old full
material trace through a changed hole.

The [knee geometry packet](../upper-corner-screw-layout/knee-bridge-geometry.md)
records the four added bores and unchanged stock bounds. Its saved manifest
SHA-256 is `254dd58d2f311553b32637b01b85b8bacbc0b474acfee667597333c501afe147`.
The knee exterior projection uses those unchanged outer dimensions. Added
holes do not supply a new host datum or establish joint acceptance.

## Completed local comparisons

The run contains **1,518 comparisons**, covering 108 complete stacks / 540
hardware components, 24 connector bodies and all 66 separate screw cylinders.
It resolves 48 connector–host datums, twelve retained-host datums across six
two-bolt receiver pairs, and 66 screw-receiver datums. All comparisons are
numeric; the unsupported pair/body list is empty.

| Category | Finite proposed datums | Comparison rows | Complete station/screw rows with a strictly positive excess | Of those, above 0.00001 mm |
| --- | ---: | ---: | ---: | ---: |
| Candidate connector–host groups | 48 | 1,296 | 36 | 14 |
| Retained frame-bolt pair/host groups | 12 | 156 | 8 | 8 |
| Separate Hillman screw-receiver diagnostics | 66 | 66 | 0 | 0 |

The frozen result preserves **44 strictly positive complete-station excess
rows**. Twenty-two are 0.0000000000616–0.0000001413504 mm residuals at the
nominal 139.7 mm boundary, including all four corrected top-corner host
comparisons. They are below the producer's 0.00001 mm geometric coordinate
tolerance. This note identifies that numerical scale without changing the
raw result or adopting an acceptance allowance. The other 22 rows are the
fourteen candidate and eight retained comparisons dimensioned below.

Each left/right row below represents both named mirrored comparisons; the
retained rear-rail row also applies to both of its named host datums. These
are permanent connector/hardware projections under the proposed convention,
not structural stress or resistance results.

| Connector or retained arrangement | Host datum | N maximum (mm) | Excess over 139.7 mm | Controlling component |
| --- | --- | ---: | ---: | --- |
| `center_post_cleat_left/right` | `base_post_center_left/right` | 215.411919 | 75.711919 | Same-side `center_post_header_*_1/head` |
| `center_principal_cleat_left/right` | `base_header` | 180.709365 | 41.009365 | Connector exterior geometry |
| `center_principal_cleat_left/right` | `base_principal_center_left/right` | 189.388700 | 49.688700 | Connector exterior geometry |
| `knee_outer_left/right_inner_frame_block` | `base_header` | 182.305134 | 42.605134 | Connector exterior geometry |
| `knee_outer_left/right_inner_frame_block` | `base_side_left/right` | 192.152686 | 52.452686 | Connector exterior geometry |
| `knee_outer_left/right_spine` | `base_post_outer_left/right` | **310.359157** | **170.659157** | Spine exterior geometry |
| `knee_outer_left/right_spine` | `base_side_left/right` | 197.017069 | 57.317069 | Spine exterior geometry |
| `rail_front_bolt_left/right_1` pair envelope | `base_floor_left/right` | 145.697039 | 5.997039 | Bolt 1 head and nut washers |
| `rail_rear_bolt_left/right_2` pair envelope | Both `base_floor_left/right` and `lumber_leg_left/right` | 164.777488 | 25.077488 | Bolt 2 head and nut washers |
| `lumber_leg_bolt_left/right_2` pair envelope | `lumber_leg_left/right` | 145.883014 | 6.183014 | Bolt 2 head and nut washers |

Complete candidate station extrema range from -99.514563 to 310.359157 mm
across their different named origins. Retained station extrema range from
25.873172 to 164.777488 mm. Screw-cylinder extrema range from -18.256250 to
48.190757 mm; the maximum is `kicker_header_left_1` against `base_header`.
No screw-cylinder diagnostic exceeds 139.7 mm. This establishes no complete
purchased screw-head/profile bound or panel-load-path acceptance.

For concrete origin examples, the controlling knee-post datums are
`(-1200.150000, -36.000000, 107.222477)` mm on
`base_post_outer_left/facet007` and
`(1196.975000, -36.000000, 107.222477)` mm on its right counterpart. The
corrected top side-host datums are
`(-1174.750000, 1466.195585, 2073.798449)` mm on
`base_side_left/facet018` and
`(1171.575000, 1466.195585, 2073.798449)` mm on its right counterpart.
Their complete top-corner N maxima are 139.70000000140442 mm. All exact
anchors, origins, face IDs and traces remain in the result. The four new
knee bolts inherit both post and side references as specified above.

The remaining disposition is concrete: parent must decide whether to adopt
this source-derived local convention and how to disposition the named
permanent excesses. The computation no longer has a missing-intersection
gap. It does not authorize exceptions, impose a redesign, or close catalog,
delivered-part, complete-joint or formal criterion requirements.

## Parent execution and disposition

[The producer](station-n-envelope.py) exposes `build(output)` and an explicit
`--output` CLI. Import is inert; the finite calculation uses saved data and
standard-library geometry arithmetic. Output must be a fresh immediate
child of `rawlocal/station-n-envelope/`. Parent owns the one execution and
publication; this task includes no CAD, heavy/frame/native solve, test,
review, staging or commit run.
The recorded command below has completed; no rerun is required.

```sh
.venv/bin/python -B \
  docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/assembly-package/station-n-envelope.py \
  --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/assembly-package/rawlocal/station-n-envelope/attempt01
```

Completed output:
[`rawlocal/station-n-envelope/attempt01/`](rawlocal/station-n-envelope/attempt01/).
The receipt records 71 authenticated direct/STEP inputs with identical
before/after hashes and binds all four output artifacts. The Markdown note
was not an input pin, so result annotation does not alter a consumed source.

| Artifact | SHA-256 |
| --- | --- |
| [Producer](station-n-envelope.py) and saved snapshot | `38e7934b05b12723711703c3198f953f11655f2f7553a2ea71f2125546e45fbc` |
| [Envelope result](rawlocal/station-n-envelope/attempt01/envelope.json) | `83d86a37ebc458d825c7cb675f438dccbe756b78f8074562254b6b0089e18714` |
| [Comparison CSV](rawlocal/station-n-envelope/attempt01/comparisons.csv) | `e10007945ee11a3dedaf07cbd03dc76982fdeaf7d3f30b3f2ac065691993f15a` |
| [Receipt](rawlocal/station-n-envelope/attempt01/receipt.json) | `6569ad27eefc706f6b709dc5b9d8e5784ed460d4b9c4ce20ad4ad82b50eb0a89` |

A numerical projection within 139.7 mm is not a delivered-part observation
or complete-joint acceptance. The ordinary packet and formally reviewed
104-stack authority remain preserved. Convention/exception adoption, N17
status, candidate selection and release flags remain unchanged by this run.
