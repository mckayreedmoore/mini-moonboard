# Solid 4×6 pivot and triangular side-frame comparison

**The centered ⅝-inch pivot in solid 4×6 legs and rims is the leading development
candidate. It is not a released construction detail.** Its two completed assembled
cases meet the listed bolt, directional placement and sampled member comparisons.
The actual rotational behavior of the installed joint remains the principal limit.
The selected `no-shoes-development` frame is unchanged.

This study follows the owner's instruction to try two specific alternatives
quickly: thicker members with a simpler upper connection, and a connected
triangular side frame. It does not add a general historical, panel or floor-test
campaign to the [agreed DIY scope](current-diy-completion-record.md).

## Solid-member candidate

The geometry uses actual 88.9 × 139.7 mm single-stock legs and outer inclined
rims. The 139.7 mm side-profile depth stays the same as the original 2×6; added
thickness grows outward to preserve existing rail ends, panel attachment axes
and commercial-angle locations. Each leg moves outward 50.8 mm, and the single
header extends 50.8 mm at each end to support the full rim width. The header is
therefore 2540 mm long, with short outboard extensions beyond the existing posts.

Each upper leg joint has one centered ⅝-inch bolt axis rather than a separated
four- or nine-bolt group. The CAD includes a provisional 9-inch Grade 5 bolt
envelope, two round washers and a nut. These dimensions and material assumptions
are inputs to the calculations, not a completed purchasing specification.

The first ¾-inch pivot trial had a favorable lateral ratio but failed directional
leg-edge clearance when its solved transverse force changed sign. It was rejected.
The smaller centered pivot provides at least 3.35 mm margin over the chosen 4D
edge screen in either depth direction, after a 1 mm drilling allowance and 2 mm
inward cut allowance. End distances also meet the conservative 7D screen.
These are assessment allowances, not released shop tolerances.

## Completed assembled calculations

All cases use A12 and twice the downward force of a 250 lb climber, with a separate
25 kg equipment allowance. Rearward means +300 N global Y; sideward means −300 N
global X. The no-slip floor premise, compression/uplift contact, independent panels
and retained material assumptions remain explicit.

| Candidate / horizontal force | Numerical gates | Worst bolt lateral ratio | Minimum adjusted edge/end margin | Decision |
| --- | --- | ---: | ---: | --- |
| Offset ¾-inch pivot / rearward | Accepted | 0.689 | −21.35 mm | Reject placement. |
| Centered ⅝-inch pivot / rearward | Accepted | 0.872 | +3.35 mm | Listed conditional comparisons met. |
| Centered ⅝-inch pivot / sideward | Accepted | 0.808 | +3.35 mm | Listed conditional comparisons met. |

For comparison, the preserved 2×6 four-bolt frame was approximately 3.10–3.12 in
the demanding rearward scenario; the nine-bolt 2×10 full-sole trial was 1.535.
These are different assembled configurations, not changes to one isolated
resistance denominator. See the [previous study](current-leg-mvp-study.md).

The centered rearward case has a maximum sampled net-member ratio of 0.616 in the
left rim and a header gross-section ratio of 0.724. Corresponding sideward maxima
are 0.570 and 0.331. The reported parallel-grain, supplemental splitting, direct
steel-stress and provisional washer comparisons are also below one. The header's
native actions include the new outboard load transfer; a gross-section comparison
does not qualify every local header connection or bearing condition.

Actual CAD checks find complete pivot bearing intervals, contained drilling,
supported washers and full rim/header face overlap. These checks do not constitute
a complete assembly collision or free-rotation/access audit.

## Necessary refinement of the opening calculation

An initial conservative net-section calculation reported 1.589 at a rim panel
screw. It treated a 4.1402 mm-wide, 33.5438 mm-deep opening as a 33.5438 mm cut
across the entire 88.9 mm member width. That was unsuitable for deciding whether
the thicker member required enlargement.

The refined calculation uses actual three-dimensional CAD cut bounds. At each
sampled section it removes the union of intersecting bounded rectangles, retaining
partial-width material, both centroid offsets and product of inertia. The resulting
corner bounds are conservative for linear axial/bending stress in the modeled
rectangle-subtracted section; they do not turn a small screw opening into a
full-width notch. Both native section-axis orientations are
handled explicitly. This changes the governing sampled rim comparison to 0.616.

The bores are completely inventoried, but not every opening center is a sampled
native section. Local opening stress concentrations, torsion and unsampled
stations remain outside this comparison. No local failure is claimed from the
superseded 1.589 bound, and the refinement does not qualify omitted effects.

## Practical tradeoffs and decisive limitation

The centered candidate's modeled assembly mass is 209.03 kg, versus the documented
171.04 kg baseline: approximately **38 kg / 84 lb additional weight**, before the
unchanged equipment allowance. Its timber envelope grows approximately 203 mm /
8 inches across the two outer leg faces. The narrow side profile is preserved,
but thickness and weight are material tradeoffs.

Maximum calculated panel/timber displacement is 32.75/27.04 mm in the rearward
case and 21.78/11.88 mm in the sideward case. These are model observations, not a
newly established acceptable serviceability limit.

**The response represents each pivot as finite translational springs with no
relative rotational restraint.** It releases all three relative rotations, not
only rotation about the bolt axis. Distributed shank bearing, mating-face contact
and clamp-induced moment are absent. A tightened wood lap joint is not thereby
established as a physical hinge, and omitting those effects is not guaranteed
conservative for demand. Scaling translational bolt stiffness cannot investigate
missing rotational restraint. The sideward case adds useful coverage but does
not resolve that distinction.

Consequently this is a promising development result, not a reason to drill the
frame immediately. The next focused gate is the actual single-axis connection
and its rotational/contact behavior, together with final hardware dimensions.
No load rating, final construction selection or friction measurement is claimed.

## Triangular side-frame alternative

The [bounded side-rail investigation](triangle-leg-concept-screen.md) evaluated
an actual placement and connection concept. Its fixed-resultant estimate requires
about 4.10 kN transfer through a floor-level rail, compared with 1.69 kN through
a raised rail. These values are force scales, not assembled predictions.

The proposed ML24 front detail fails receiver geometry. A straight LSTA12 strap
envelope fits the coplanar post/rail faces, but its verified screw-connected
published rating applies at C_D = 1.6 and explicitly excludes other durations.
The current C_D = 1.0 connection basis is unresolved. No assembled triangle was
simulated, and no unmodeled rigid tie was used to manufacture a favorable result.

Prefer resolving the thicker-member pivot first. The rail adds members and two
new connection regions without a demonstrated reduction in assembled demand.
It remains a secondary, unselected concept rather than a rejected universal idea.

## Evidence and reproduction

[Evidence manifest](../fea/results/thick-leg-study/manifest.json) links the three
compressed native reports, authenticated producer source archives, original and
centered geometry, and recomputable checks. Large native solver files remain at
the local paths recorded there; their hashes are retained in the reports. The
original offset candidate's source and failed placement evidence are preserved.

```sh
uv run python -m scripts.thick_leg_results
uv run python -m fea.triangle_concept_screen
```

A fresh centered native case uses a frozen source snapshot and an unused output:

```sh
uv run python -m scripts.thick_leg_study --output fea/generated/new-thick-centered
```

The published comparisons cover only the cases listed above. They do not imply
an unrun load envelope or qualification of the actual installed connection.

Validation: **369 default tests passed, 15 deselected, in 25.37 seconds**.
Repository lint and whitespace checks passed. Historical models were not rerun.
