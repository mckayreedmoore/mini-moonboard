# Leg-bolt resistance checkpoint

Status: conditional calculation, not an allowable joint rating or construction
approval. Retain geometry for review; do not reduce bolt count or raise the
climber limit based on this calculation.

## Actual stack

The machining inventory places each of the eight 95.25 mm (3¾ in) leg bolts
through a 38.1 mm rim followed by two adjacent 19.05 mm leg plies. Both plies
are on the same side of the rim. This is not the conventional double-shear
arrangement with the loaded main member between two opposing side members.

| Member | Raw interval from hardware origin | Nominal threaded bearing |
| --- | ---: | ---: |
| Rim | 2.032–40.132 mm | 0 mm |
| Inner leg ply | 40.132–59.182 mm | 0 mm |
| Outer leg ply | 59.182–78.232 mm | 8.382 mm (44% of ply thickness) |

These intervals are checked for all eight bolts against the source-bound
machining inventory. Thread length is the nominal 25.4 mm reference, not a
measurement of purchased hardware or a tolerance allowance. The outer ply
does not meet the nominal quarter-bearing-length condition. The calculation
therefore retains the 0.298 in root diameter throughout; no favorable diameter
exception is claimed by merging the plies.

NDS 2024 §12.3.8 addresses four-or-more-member connections with adjacent
members resisting opposing forces. That shortcut does not resolve this
three-member same-side stack. See the official
[NDS Chapter 12](https://awc.org/wp-content/uploads/2026/08/AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-%E2%80%93-Dowel-type-fasteners.pdf),
including §12.3.7 for threaded-fastener diameter and §12.3.9 for axial components.

## Conditional bonded-laminate calculation

For comparison with the FE model's perfectly bonded leg plies, treat the
combined 38.1 mm leg as one side member against the 38.1 mm rim. This requires
justification of laminate behavior; it is not established merely by specifying
glue. Reuse the [TR12 kernel and documented material assumptions](two-member-bolt-yield.md):
root diameter 0.298 in, assumed fastener bending yield 45,000 psi, timber bearing
3,650 psi, plywood bearing 5,600 psi, zero gap and the same conservative
directional reduction terms. Purchased fastener and material properties remain
unverified. No group, service-condition, axial, splitting or adhesive resistance
is established here.

The resulting reference is **797.62 N (179.31 lbf) per bolt**, governed by mode
IIIm. This is a supplied-input single-fastener lateral reference, not an adjusted
allowable. The [coupled leg release](coupled-leg-release.md) reaches 903.13 N
lateral demand in its stiffest assumed spring trial, approximately 1.13 times
this reference. This comparison flags the connection for further assessment;
it is not a safety factor, proof of failure, or a calibrated demand/capacity
ratio. The trial's separate 100.52 N axial maximum must not be combined with
that lateral maximum as though they occurred simultaneously. Signed case
vectors remain in the native archive for combined-action assessment.

## Next decision

### Distinguish the requested maximum from the sensitivity mass

The owner specified one climber, 250 lb maximum; 300 lb remains a comparison
case, not a changed requirement or a certified limit. The archived trials give
the following **peak lateral** forces, distinct from resultant-force maxima:

| Climber mass | At 100 N/mm | At 1,000 N/mm | At 10,000 N/mm | Signed axial force simultaneous with the 10,000 N/mm lateral peak |
| --- | ---: | ---: | ---: | ---: |
| 150 lb | 202.91 N | 385.95 N | 506.43 N | −14.08 N |
| 200 lb | 256.89 N | 489.07 N | 638.66 N | −17.77 N |
| 250 lb requested maximum | 310.87 N | 592.19 N | 770.90 N | −21.47 N |
| 300 lb sensitivity | 364.84 N | 695.31 N | 903.13 N | −25.16 N |

All these lateral peaks occur at A12 with twice the listed weight downward and
300 N in world +Y. At 100/1,000 N/mm the governing bolt is
`analysis_leg_wall_bolt_left_4`; at 10,000 N/mm it is
`analysis_leg_wall_bolt_left_1`. Axial signs above refer to force **on the leg
in world X**, not an automatic tension/compression classification of the washer
stack. Other cases/bolts can govern axial or combined action.

The stiffest 250 lb lateral case is numerically about 0.967 times the conditional
797.62 N reference. This is too incomplete to establish adequacy: it omits the
reference's unresolved applicability/adjustments, simultaneous axial resistance,
other failure modes and real connection/floor behavior. Do not describe the
300 lb result as a demonstrated failure of the 250 lb design, or the 250 lb
comparison as a pass.

`fea.leg_demand_checkpoint` authenticates the native archive and returns all
12 maxima with their actual case, bolt, signed vector and conditional numerical
reference ratio. It does not combine independently maximized components.

```sh
uv run python -m fea.leg_demand_checkpoint
uv run pytest -q tests/test_leg_demand_checkpoint.py
```

Published yield theory does not itself establish joint slip, and the cited
load-slip study evaluates a two-member connection, not this three-member stack.
See [Heine and Dolan, Wood and Fiber Science, 2001](https://wfs.swst.org/index.php/wfs/article/view/1368).
Neither dividing a yield value by a guessed displacement nor transferring the
study without checking applicability supplies the missing spring calibration.

Checkpoint verification: 20 focused tests passed, including replay of the full
coupled-leg native archive. Ruff and whitespace checks passed. Three independent
reviewers found no substantial correctness, testing or package issues and
independently verified the reported maxima. This is numerical/package review,
not structural approval.

### Steel-grade-only change does not close this comparison

Source check, 2026-09-08: the manufacturer's
[A307 mechanical-property summary](https://www.portlandbolt.com/technical/specifications/astm-a307/)
lists a 60 ksi minimum tensile strength for Grade A but no minimum yield
strength. The selected grade designation alone therefore does not verify the
45 ksi bending-yield input. A tensile ultimate value is not a substitute.
The [J429 summary](https://www.portlandbolt.com/technical/faqs/j429-strength-requirements/)
does specify yield minima for other grades, but these do not automatically
establish the project's NDS bending basis or compatible purchased hardware.

Holding all current lengths, bearing properties, root diameter and reduction
terms fixed, the mode-II reference is **840.79 N** and is independent of the
steel bending-yield input. Raising the assumed input from 45 ksi to either
90 or 120 ksi makes mode II govern at that value, only about 5.4% above the
current 797.62 N reference and still below the trial's 903.13 N lateral maximum.
Those two inputs are arithmetic sensitivities, not assignments to catalog
bolt grades. The mode-II ceiling applies to this calculation only, not all
possible joints or adjusted design values. No higher-grade bolt substitution
is selected as a solution.

The [material procurement basis](remaining-material-hardware-closure.md) takes
no adhesive/composite credit. The bonded-laminate calculation and bonded-ply FE
body are conditional departures used for diagnosis, not changes to that design
basis. To qualify the intended no-credit approach, resolve individual-ply bolt
bearing and stitch transfer; alternatively, explicitly qualify laminate action.
Do not silently carry the bonded reference into the procurement/build plans.

The [individual-ply load-path audit](leg-ply-load-path.md) confirms the existing
mesh can support that separation and maps the actual stitch bolts. It does not
yet assign individual-ply forces or qualify a three-member bolt model.

Do not declare this joint adequate. Establish the purchased bolt properties,
laminate/load-sharing basis and directional slip, then check the same-case
lateral/axial forces, washer bearing, spacing, group action and plywood failure
modes. Compare a revised attachment only if that basis shows a shortfall;
simply adding bolts or enlarging them is not yet an evidence-backed solution.
The remaining ideal bonds and fixed floor in the FE model also prevent treating
its trial demand as the physical demand bound.

Reproduce the eight stack inventories and references without a new FE solve:

```sh
uv run python -m fea.leg_bolt_reference
uv run pytest -q tests/test_leg_bolt_reference.py tests/test_dowel_yield.py
```

Verification: 25 focused thread-bearing, yield-kernel, bolt-reference and
gusset-envelope regression tests passed. Ruff and whitespace checks passed.
Independent correctness, testing and architecture/package reviews reported no
substantial findings. These implementation reviews are not structural approval.

The subsequent steel-strength-only sensitivity increases that regression to
26 passing tests. A fresh three-scope independent review found no substantial
issues in the sensitivity or design-basis clarification; Ruff and whitespace
checks remained clean.
