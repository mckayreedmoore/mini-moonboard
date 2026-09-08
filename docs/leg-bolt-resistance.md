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
