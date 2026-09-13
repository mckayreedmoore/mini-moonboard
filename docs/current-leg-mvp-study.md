# Assembled leg MVP study

**Decision: no replacement is selected. The current leg connection remains unresolved.**
The fixed-resultant nine-bolt screen did not survive an assembled-frame calculation.
Neither larger-stock trial below supports releasing its drilling or purchasing its
replacement hardware. The preserved `no-shoes-development` baseline is unchanged.

This is the bounded follow-up to the [replacement screen](current-leg-revision-screen.md)
and the owner's [DIY completion scope](current-diy-completion-record.md). It does not
add external sign-off, physical floor testing or general panel qualification to that
scope. It also does not change a failed numerical comparison into a passing design.

## What was evaluated

All three completed cases use A12, a 250 lb climber with twice the downward force
(2,224.11 N), 300 N rearward force and 100 mm load eccentricity. They retain the
accepted panel configuration, no-slip floor premise, compression-only normal
contact and the existing material assumptions. These are project scenarios, not
an established impact spectrum or climber weight rating.

| Geometry and contact model | Numerical checks | Governing bolt demand/reference ratio | Decision |
| --- | --- | ---: | --- |
| Original single-2×6 legs/rims, four ⅜-inch bolts per leg; 3×3 tributary-area foot springs | Accepted | 3.122 | Finite-area contact does not remove the baseline concern. |
| Single-2×10 legs/rims, nine ½-inch bolts per leg; original corner foot springs | Accepted | 1.535 | Reject this candidate as the selected detail. |
| Same nine-bolt frame, actual 5 mm sole-end relief leaving a 75 × 38.1 mm land; 3×3 tributary-area foot springs | Accepted | 1.606 | Reject this candidate as the selected detail. |

The two revised candidates use a 3×3 bolt layout with 65 mm spacing along the leg
and 75 mm along the rim, shifted 50 mm along the leg from the previous group
center. The leg top extends 260 mm beyond that original center. Their complete
catalog stack is a ½-inch, 5-inch-long Grade 5 bolt, two BP½ plates, three specified
spacer washers and a Grade 5 nut. Dimensions and material properties remain the
explicit assumptions in the hardware module; this study does not release them.
The wider rims retain their actual partial header overlap; the 77.3 mm rear
overhang is not given fictitious header support.

Finite-area foot springs preserve the previous total normal stiffness of
400,000 N/mm per leg. Their spatial distribution changes rotational compliance.
Bolt stiffness uses the existing elastic analogy with the larger diameter and
plate seat area. Neither spring law is a measured installed property. All three
runs passed the implemented equilibrium, interpolation and contact convergence
gates. That validates their numerical solution under those assumptions, not the
assumptions themselves.

## Why the earlier result changed

The earlier 0.847 screen distributed the old frame's saved joint forces over a
larger bolt pattern. The assembled calculation changes both the force distribution
and the resultant joint moment. In the full-sole revision, left-leg moment about
global X rises to approximately 728 N·m. Moving the floor pressure resultant
rearward and changing the horizontal reaction both contribute.

The relieved sole moves that pressure resultant forward, but the assembled frame
redistributes again: left-leg horizontal joint force falls from 561 to 405 N,
vertical force magnitude rises from 2,853 to 3,006 N, and moment rises to 774 N·m.
The smaller counteracting horizontal contribution offsets the footprint benefit.
Peak individual bolt lateral force increases from 1,670 to approximately 1,749 N.
This is why footprint tuning did not solve the joint.

The relieved foot retains at least 3.834 mm calculated clearance beneath the
removed ends after a 1 mm cut tolerance. Its governing extrapolated corner
pressure is nevertheless 6.972 MPa, or 1.618 times the retained conservative
perpendicular-to-grain bearing reference. This coarse-grid pressure screen is
not a mesh-converged contact stress. The independent bolt exceedance already
prevents selecting the detail.

A short-neck linear stress calculation also reports tension. A section only
5 mm above partial bearing does not establish a linear stress distribution, so
that diagnostic is not proof of splitting. Conversely, the generic beam and
hole-section calculations do not qualify this relieved neck.

## Local checks and their limits

Actual CAD inventory covers the revised bores, complete bolt stacks and placement.
The full-sole fit review found contained bores, supported plates and no reported
hardware collisions. The relieved candidate's upper connection is unchanged, but
its floor geometry is assessed separately. A sole model cannot silently call the
full-sole fit review.

For the relieved candidate, the conditional parallel-grain joint check is 0.400
and the separate supplemental splitting comparison is 0.744. Plate, washer and
direct steel-stress comparisons remain below one using the documented assumptions;
the additional combined lateral/axial screen is 1.612. These comparisons do not
resolve the failed wood-dowel lateral comparison or establish a local prying bound.

The independent worst-hole net-section envelope is 1.115. It combines worst area,
moduli and centroid offset from different stations with recovered actions at every
station. **This is a conservative envelope exceedance, not an established local
member failure.** Station-matched refinement would be needed before making that
claim. Raw end cuts and sole relief are outside this bore-envelope calculation.
No further member refinement was needed to reject the candidate because its
individual bolt comparison already exceeds the reference.

A cheaper single-pivot concept was screened before adding more CAD. At a leg-aligned
force of roughly 3.2 kN, the existing smooth-shank dowel-yield equations give about
1.986, 2.259 and 2.527 kN for single ¾-, ⅞- and 1-inch bolts respectively in two
38.1 mm members. Thus a 1-inch pivot has no demonstrated reserve even before
retention, fit and out-of-plane behavior. Two separated bolts remain a moment
connection; they must not be labeled a hinge to obtain a favorable calculation.
The [AWC connection resources](https://awc.org/resources/connection-calculator/)
identify the applicable single/double-shear connection design framework; these
screening values are repository calculations, not manufacturer load ratings.

## Deliverables and stopping decision

The study adds explicit candidate selection, independent leg-bolt stiffness
variation, actual header overlap and finite-area foot sampling to the response
runner. Its defaults preserve the current candidate. New geometry and local
checks remain separate development modules. The scripts list additional possible
study cases; only the three cases in the table were completed. No unrun sensitivity
or different load case is claimed as evidence.

[Saved evidence](../fea/results/leg-mvp-study/manifest.json) includes compressed
full response reports, their producer source snapshots, source/artifact hashes,
actual sole geometry and its local assessments. The large native cycle files
remain at the local paths in the manifest; the committed archives do not contain
those solver files. The saved reports retain their artifact hashes and numerical
validity records. Reproduction requires the recorded solver environment and
model configuration; it is not a substitute for an independent solver audit.

A senior design decision here is to stop these unproductive detail variations.
The next design study would need a materially different, explicitly connected
load path or a justified change in available bearing thickness, with its own
installation constraints. Merely adding bolts, narrowing feet or declaring a
multi-bolt joint pinned is not supported by this evidence. That next concept is
not selected by this report.

The MVP remains incomplete at the leg/connection decision. The provisional
construction package remains useful for the retained configuration, but no final
replacement leg drilling is issued. The completed investigation narrows the
problem without hiding its failure or transferring historical acceptance.

## Verification and reproduction

The current default suite passed **358 tests, with 15 deselected, in 23.54 seconds**;
repository lint and whitespace checks passed. Historical model tests were not rerun.
These software results do not change the failed structural comparisons above.

Recompute the saved response comparisons without CAD or a native solve:

```sh
uv run python -m scripts.leg_mvp_results
```

For a fresh native study, use a clean source snapshot and an unused output directory:

```sh
uv run python -m scripts.leg_mvp_study sole-foot3 --output fea/generated/new-sole-foot3
```

The archived producer sources authenticate the completed runs. Later source changes
include clearer review rejection and evidence labels; rebuilding current sources
creates new evidence and must not overwrite or impersonate an archived run.
