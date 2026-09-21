# PB02 rear-clear six-case development decision

## Decision

**ADVANCE PB02 to the unresolved component and complete-joint checks.**

This is a development decision, not structural acceptance. It does not release
purchasing for construction, drilling, fabrication, or construction. The
current whole-frame model still retains 22 legacy angle/SDS stations outside
the converted center, so it is not the final all-bolted candidate.

The decision is source-bound to commit `10333d2` and the active geometry
fingerprint
`4ef3ff0376b4c49142c8a1bc347270da024852e4554cfc4e549b6cafab63dccb`.
The rear cleat spans Z=5…460 mm and has no modeled floor bearing. This is the
geometry shown by the current V4 viewer and current BOM.

## Authenticated evidence

The [compact evidence package](../../fea/results/diagnostics/pb02-rear-clear-10333d2-v1/README.md)
retains six accepted reports, their final solver files, one common 278-file
source closure, and the A12-forward grid/density study. The
[`six-case authenticator`](../../scripts/simple_center_pb02_six_case_evidence.py)
pins every report hash, exact load, model identity, deterministic scope,
contact partition, source snapshot, and final-cycle artifact.

All cases use the corrected physical contact convention and the 8x8 exact-face
partition. The selected reference inputs are 1,000 N/mm bolt axial stiffness,
3,086.746 N/mm bolt lateral stiffness, 1,000 N/mm mean canonical-interface
contact stiffness, and 10,000 N/mm floor-contact stiffness. The floor value is
a conditional developmental input, not a measured or qualified property.

The
[bounded floor-stiffness evaluator](../../scripts/simple_center_pb02_floor_stiffness_sensitivity.py)
authenticates complete six-case suites before comparing governing identities,
ratios, and 432 signed action components. The
[compact evidence manifest](../../fea/results/diagnostics/pb02-floor-stiffness-5k-10k-15k-v1/manifest.json)
retains source-comparable 5,000, 10,000, and 15,000 N/mm suites. All three share
the same 278-file source map and producer map. Its self-authentication and
comparison report **material numerical change detected**: the governing identity,
one or more governing ratios, and one or more signed actions change under the
evaluator's 5% screening rule. That rule is a numerical triage threshold, not a
physical limit or acceptance criterion.

| Floor trial, N/mm | Combined bolt, N | Interface moment, N-mm | Direct-shaft ratio | End-grain ratio | Individual-wood ratio |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 5,000 | 203.132 | 5,339.455 | 0.20284 | 0.11413 | 0.20261 |
| 10,000 | 196.391 | 5,147.700 | 0.17441 | 0.09813 | 0.19984 |
| 15,000 | 192.170 | 5,045.844 | 0.16719 | 0.09407 | 0.19807 |

The largest governing-ratio change is 16.30%: the block/header end-grain ratio
changes from 0.09813 at 10,000 N/mm to 0.11413 at 5,000 N/mm. At 15,000 N/mm,
the governing complete-interface moment moves from
`header_principal_block`/A12 rear to `rear_block_post`/K12 right, while the
direct-shaft and block/header end-grain governors move from bolt 1/A12 forward
to bolt 2/K12 right. Eleven small signed components reverse sign; the largest
relative change is a 48.31 N-mm change in a near-zero-baseline interface moment.
These changes prevent a claim of numerical insensitivity, but every listed
conditional ratio remains below 0.203 and the **ADVANCE for development only**
decision is unchanged.

A separate 20,000 N/mm attempt accepted A12 forward but did not converge for
A12 rear under either bounded all-at-once or seeded one-at-a-time contact
updates. It is recorded as a failed trial; its reports, forces, and solver
artifacts are excluded from the comparison. The 5,000–15,000 N/mm trial values
are numerical inputs, not measured floor properties or asserted physical bounds.

| Case | Applied force XYZ, N | Cycles | Max panel displacement, mm |
| --- | ---: | ---: | ---: |
| A12 forward | `[0, -300, -2224.111]` | 12 | 13.6140 |
| A12 rear | `[0, 300, -2224.111]` | 14 | 17.0472 |
| A12 left | `[-300, 0, -2224.111]` | 14 | 14.7127 |
| K12 right | `[300, 0, -2224.111]` | 14 | 13.8285 |
| K12 rear | `[0, 300, -2224.111]` | 14 | 16.4463 |
| A1 rear | `[0, 300, -2224.111]` | 10 | 8.59576 |

Every report passes its recorded contact and tension-only active-set gates,
member/global equilibrium, MPC check, and numerical acceptance gates. These
are numerical statements, not resistance qualification.

## Signed load path and governing actions

The connected center has three physical routes:

- base header to shifted post through direct timber bearing and the
  `block_header`/`post_block` path;
- base header to principal through `header_principal_block` and
  `principal_block_principal`; and
- principal to upright to rear cleat to shifted post through the return path.

The [six-case component envelope](../../scripts/simple_center_pb02_six_case_component_envelope.py)
preserves each bolt's simultaneous axial and lateral forces from one solve. It
also combines every canonical interface's contact resultant with all bolts on
that interface to obtain a complete interface wrench about the net-face
centroid. It does not add capacities across serial interfaces.

| Quantity | Governing location and case | Demand |
| --- | --- | ---: |
| Combined bolt force | `principal_block_principal/bolt_1`, A12 rear | 196.391 N |
| Bolt tension | `header_principal_block/bolt_1`, A12 rear | 75.576 N |
| Bolt lateral force | `principal_block_principal/bolt_1`, A12 rear | 181.849 N |
| Complete interface force | `principal_block_principal`, A12 rear | 195.771 N |
| Complete interface moment | `header_principal_block`, A12 rear | 5,147.700 N-mm |
| Peak cell-average pressure | `header_principal_block`, A12 left | 0.01765 N/mm² |

The A12-rear governing bolt carries 74.165 N tension and 181.849 N lateral
force simultaneously. This is materially below the earlier local replacement-
duty trial's kilonewton bolt reactions. The difference is physically
explainable: the whole-frame model retains direct post/header and
principal/header compression paths plus the surrounding frame, instead of
routing an imported interface wrench through the isolated seven-body loop.

## Conditional resistance comparisons

The envelope reuses the existing 2024 NDS DF-L yield helpers and the existing
conditional A307/washer arithmetic. It evaluates all six reference-density
cases without converting any single mode into a complete-joint verdict.

| Conditional family | Governing bolt and case | Ratio |
| --- | --- | ---: |
| Individual wood yield | `principal_upright_block/bolt_1`, K12 rear, 0.180-in root | **0.19984** |
| A307 direct-shaft comparator | `block_header/bolt_1`, A12 forward | 0.17441 |
| Block/header end-grain yield | `block_header/bolt_1`, A12 forward, 0.180-in root | 0.09813 |
| Ideal 20-mm washer wood bearing | `header_principal_block/bolt_1`, A12 rear | 0.06441 |

All currently supported conditional ratios are below 1.0. The separate
A12-forward density-2x sensitivity governs the existing direct-shaft screen at
0.22815, also below 1.0. Neither value qualifies the long-grip method, a
delivered bolt, or the joint.

The 4x4-to-8x8 study changes maximum interface force 3.0081%, moment 5.6164%,
governing bolt force 0.8192%, and panel displacement 0.000285%. Active area and
peak cell-average pressure change 8.5557% and 22.8987%, so local pressure is
not qualified. Across the A12-forward 0.5x/1x/2x contact-density range, maximum
interface-force and moment ratios are 2.17094 and 2.39203; the governing bolt-
force ratio is 1.13920. The six-case envelope is reference density only.

## Six-case bore-member envelope

The [bore-member envelope](../../scripts/simple_center_pb02_six_case_member_envelope.py)
checks both sides of four current 7.3 mm diagnostic bore cuts in every accepted
case. It reuses the signed section actions and 2024 NDS member helper. Dimension
lumber uses the DF-L No. 2 base values without a size-factor increase; the 4x4
side cleat uses the separately classified DF-L No. 2 post-and-timber values.

Among the three cuts with exact paired report rows, the governing necessary
fully-braced normal interaction is **0.04335** at the rear-cleat link bore,
station-loads-included side, in K12 rear. Its same-cut average net-shear ratio is
**0.00134**. The governing exact-cut result therefore remains **ADVANCE for
development only**.

That result is deliberately narrow. The principal-upright bore actions are
extrapolated from the first valid full-section plane and are excluded from the
disposition. The screen records torsional demands but evaluates no torsional
resistance or torsion/shear interaction. It also does not qualify stability,
local splitting, crossed- or nearby-hole interaction, or near-hole stress
concentration. The largest recorded torsional demand at these four cuts is
3,082.31 N-mm at the extrapolated principal cut in K12 rear; it is a demand to
resolve, not a capacity result.

## Crossed-bore local wood envelope

The
[local wood envelope](../../scripts/simple_center_pb02_six_case_local_wood_envelope.py)
evaluates four bolt/member incidences around the 18.7 and 20.2 mm nominal
crossed-bore ligaments in all six accepted cases. Each of the 24 records uses
one bolt force without neighbor-force cancellation. An incidence-specific
orthonormal frame preserves the signed three-dimensional action and the loaded
edge. The perpendicular neighbor bore is represented as a separate orthogonal
strip at its actual grain station, rather than as a false same-orientation
helper opening.

The governing conditional 2024 NDS Appendix E ratio is **0.02373** for
parallel row tear-out at `upright_side_cleat/cleat_link` in K12 rear. The
separate supplemental EC5 splitting comparison governs at **0.01071** at
`shifted_right_post/post_high` in K12 right. Both use `CD = 1` and the lower
Table 4D DF-L No. 2 values as a conservative conditional input without a size
factor benefit; the finished stock classification remains a receiving item.

This mechanism therefore remains **ADVANCE for development only**. The result
does not qualify three-dimensional orthogonal-hole stress concentration,
near-hole interaction, fabrication tolerance, or the complete joint.

## Hardware, access, and retained geometry

The center uses ten ordinary through-bolts, ten nuts, and twenty washers: three
5-inch, three 6-inch, and four 8-inch bolts. The illustrative allocated hardware
cost remains $11.88, or $13.69 at first checkout, excluding lumber. All modeled
bolts have insertion routes; seven are one-ended access installations. Nominal
washer seats and compact socket envelopes clear. Delivered dimensions, grade,
thread location, washer metal, and actual tool access remain receiving checks.

The panel/kicker screw layout remains unchanged at 66 axes. Both inner kicker
panel edges remain supported. Only one center support was shifted outward, and
the kerf-right narrower kicker remains the active width option.

## Why the decision is only ADVANCE

The present evidence supports continuing this architecture because the
source-bound demands are modest relative to every resistance comparison that
is actually available. It does not support acceptance because the resistance
coverage is incomplete. The next engineering work is bounded to:

- crossed-bore splitting and nearby-hole interaction at the 18.7 and 20.2 mm
  nominal ligaments;
- the inclined principal's clipped local section and 0.490 mm unloaded-edge
  nominal reserve before tolerance;
- three-dimensional crossed-/nearby-hole stress concentration, principal-cut
  qualification, torsion/shear interaction, stability, group, perpendicular-tension, washer-
  metal, preload, prying, nut/thread, and delivered-hardware checks;
- a defensible physical floor-contact stiffness basis or receiving criterion,
  because the numerical 5,000–15,000 N/mm range is decision-stable but not a
  measured material range; and
- conversion and checking of the 22 remaining legacy connector stations on
  one coherent factory-connector-only frame.

No lap joint, custom steel, half-lap, manufacturer contact, or panel-screw
layout change is authorized. Until the open mechanisms and final all-bolted
frame are checked and reviewed, PB02 remains **developmental only**: no
purchase for construction, drilling, fabrication, or construction is released.
