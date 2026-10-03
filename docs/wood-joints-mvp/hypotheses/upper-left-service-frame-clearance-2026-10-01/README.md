# Upper-left service joint: frame clearance decision worksheet

**The next compatibility check is complete as a conditional comparison.
Keep the reviewed cleat geometry for the next development iteration.
The complete joint and physical release remain HOLD. The full 47-criterion
authority is unchanged.**

Scope: `left_service_outer_upper_cleat`, duty
`clip_horizontal_upper_left_1`, connecting `base_rail_service_upper_left`
and `base_side_left`. The 88.9 × 88.9 × 119.7 mm cleat, four quarter-inch
bolt axes and 33 mm pitches are unchanged. This follows the
[motion worksheet](../upper-left-service-motion-sensitivity-2026-10-01/README.md).

## Practical result

With the surrounding frame included, the four outer bolts can move within
their clearance while the panel and other connections carry more of the
transfer. The large rotation from the previous independent-interface inverse
calculation is not the returned response of this coupled frame hypothesis.
This comparison changes the joint forces rather than holding the old interface
wrenches fixed.

For the frozen source lateral stiffness, peaks over the same 21 saved states
are below. Peaks in a row can occur at different states. Loads are **2× the
recorded proportional gravity-plus-climber loads**; this is a study scaling,
not a new adopted load combination or a load-cycle simulation.

| Relative bolt clearance | Outer bolt shear / tension | Local rail-to-side movement | Local rail-to-side rotation | Largest spring-component change outside the joint |
| --- | ---: | ---: | ---: | ---: |
| 0 mm | 68 / 114 N | 0.094 mm | 0.057° | 0 N |
| 0.50 mm | 13 / 11 N | 0.556 mm | 0.089° | about 99 N |
| 1.15 mm | 9 / 13 N | 0.558 mm | 0.105° | about 99 N |

The 1.15 mm value is the modeled 7.5 mm bore minus 6.35 mm bolt, combining
the two receiver clearances. Actual fit is unobserved. Zero and 0.50 mm are
hypotheses; none of these values is a drilling instruction.

**Provisional decision targets:** 1 mm relative movement and 0.5° relative
rotation at this joint. These are explicitly hypothetical development targets,
not adopted authority limits or whole-frame serviceability criteria. A 0.5°
rotation produces approximately 1 mm differential motion over the 119.7 mm
cleat length, making the two targets comparable for a practical geometry
decision. The local movement and rotation estimates in all 252 study states
fall below those targets. This supports retaining the geometry while the
dependent load path is checked; it does not support fabrication or climbing.

## Sensitivity and motion interpretation

There are **12 scenarios × 21 states = 252 calculations**: clearances
0, 0.50 and 1.15 mm, crossed with four lateral stiffness choices. The frozen
source value is approximately 3,087 N/mm. The other three values are the
previous hypothetical beam-on-foundation law at effective timber moduli
150, 300 and 600 MPa: approximately 958, 1,611 and 2,709 N/mm.
Only the target bolts' lateral laws change. Timber solid stiffness, axial
ties, washer-seat surrogates, face-contact laws, panel screw laws and all
other bolt laws retain their frozen source values. This is not a repeat of
the previous combined timber/seat sensitivity.

At 1.15 mm clearance, across all four lateral stiffness choices:

- Local movement peaks: **0.557–0.558 mm**; rotation peaks: **0.105–0.106°**.
- Outer bolt peaks: approximately **9 N shear and 13 N tension**.
- Bolt-point slip peaks: **1.153–1.160 mm**. Slip at a bolt includes cleat
  motion within its bore; it is a different quantity from host-to-host motion.

The local motion estimate fits six relative-motion coordinates to all ten
returned projections at each interface: four lateral components, four
face-contact components and two outer-seat axial components. The projections
include solid elastic deformation through `q = D*a + e - H*f`. Both interface
fits use the same cleat datum, and rail relative to side is
`(cleat relative to side) - (cleat relative to rail)` there. Maximum residual
of this local rigid-interface approximation is **0.0033 mm** over the whole
grid and **0.0018 mm** at 1.15 mm clearance. It is an approximation supported
by those small projection residuals, not an exact reconstructed displacement
at an arbitrary point inside the timber.

The report also retains each body's global fitted rigid component. Those
coordinates omit elastic deformation and should not be substituted for the
local estimate. At 1.15 mm clearance, their common-datum host difference peaks
at approximately 1.016 mm / 0.099°. Maximum change from the source rigid
component is approximately 0.440 mm / 0.083°. Neither measure is total panel
deflection or an adopted serviceability check.

## What changes the next decision

**Robust within this frozen-frame study:** all 252 solutions satisfy the
declared connector laws, body equilibrium and the strict bearing/open signs
of their recorded floor branches. Contact release and engagement are included;
at most seven normal-branch solves were needed for a state. Removing touching,
zero-force normal rows and unloaded gap pairs leaves rigid-coordinate rank
300 in every state, so these returned motions do not rely on a zero-force
contact to remove a rigid mechanism. Outer lateral stiffness variation has
little influence once substantial clearance is available.

**Assumption dependent:** much of the outer joint's previous transfer moves
into panel connections. At full A12-rear, source row 322 for
`round_panel_upper_left_service_2/panel-wood-interface` reverses one signed
lateral component from approximately **−57 N to +42 N**, a **99 N change**.
That change is not a 99 N increase in screw shear magnitude. Other panel
contact and screw components also change. Source panel lateral stiffness
and parametric withdrawal springs are unqualified Hillman assumptions;
the frame response cannot establish their strength or stiffness.
All other bolted joints retain zero clearance, another optimistic load-sharing
assumption. The recorded no-slip floor masks remain conditional and do not
establish actual floor restraint or a uniquely selected floor history.

**Recommended single next check: bound the panel connections' contribution
to this redistributed load path.** Recompute this same comparison with zero
credit for the unsupported parametric Hillman withdrawal restraint and a
clearly stated panel lateral-stiffness range. Check whether the local movement
targets and the load transfer still hold. This is more likely to change the
geometry decision than increasing the outer bolts' strength from the small
forces returned here. It is a finite analytical check, not a screw substitution,
socket redesign or native mechanics program.

## Method and boundaries

The producer reuses the pinned full-frame compliance operator from
[attempt04](../mvp-acceleration-2026-09-28/current-frame-connector-compliance-attempt04/README.md).
It authenticates physical coordinates, body/element ownership, solid
connectivity, geometry and material binding for A1-rear, A12-rear and K12-rear
against that operator's source model. Its 1,840 connector coordinates include
all 50 bodies. Raw `H` is retained in the compatibility equations; no native
solver, new solid factorization or CAD change is performed.

Each normal branch is solved by general LU. An eight-coordinate reduction
then applies a circular clearance law to rows 112–119. A constrained
quadratic provides only a numerical starting point; the final projection
solve and all residual checks use the raw response. The law permits zero
force inside a clearance disk. Nonfloor normal branches can change;
the source floor tangent masks remain fixed and their strict normal signs
are checked afterward.

An explicit study assumption extends **zero force at open contacts** beyond
the source table's −10 mm endpoint; maximum separation coordinate is
approximately 14.2 mm at 2× load. Positive-force branches remain within their
source range. This extension, small-motion kinematics, centered initial gaps,
zero preload/friction credit, uncalibrated source stiffness and recorded
conditional floor support all limit the result. Missing A12-forward,
A12-left and K12-right cases remain missing. Finished timber, splitting,
bolt bending, washer stress, full contact transfer and turning/counterhold
checks are not closed by this comparison.

The zero-clearance calculation matches the 21 scaled source responses within
**0.001 N** and **0.000010 mm**, against separately declared practical
comparison tolerances of 0.002 N and 0.0001 mm. These tolerances apply to this
comparison only. The older failed exact DAT force-interval checks remain
unchanged and are not represented as passes.

## Evidence and reproduction

- [Final comparison](comparison-final.json): every state, both simultaneous
  signed interface wrenches, clearance motion, local fits and demand changes.
- [Full response vectors](response-vectors-final.npz): all `f`, `q` and `a`.
- [Independent saved-vector audit](parent-validation.json): laws, raw
  compatibility, equilibrium, force-bearing rank, floor consistency and
  world-port moment rejoin for all 252 states. All 47 authority records and
  eight release flags are unchanged.

The circular-gap known answer includes two force-bearing pairs and two free
pairs. Ruff passes. Full response vectors reproduce byte-identically; report
differences are confined to last-bit condition estimates (at most `1.4e-23`
absolute). The [completion receipt](completion-receipt.json) records this
comparison and the preserved source packet. Reproduce into fresh output paths:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python \
  docs/wood-joints-mvp/hypotheses/upper-left-service-frame-clearance-2026-10-01/study.py \
  --output /tmp/service-frame-clearance-replay.json \
  --vectors /tmp/service-frame-clearance-replay.npz
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python \
  docs/wood-joints-mvp/hypotheses/upper-left-service-frame-clearance-2026-10-01/audit.py --verify
```

Existing output paths are refused. Initial `comparison.json` and
`response-vectors.npz` are preserved; their producer snapshot is retained at
`/tmp/upper-left-service-frame-clearance-initial-0ph7j9ef`. Final vectors are
byte-identical to the initial calculation; the final worksheet adds local
motion fits and identifies demand changes outside all three joint bodies.
No authority file, reviewed geometry, historical source packet, native
readiness flag, commit or push was changed for this deliverable.
