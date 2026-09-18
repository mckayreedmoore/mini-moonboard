# Selected compact frame with independent knee splices

2026-09-13. Candidate: `compact-spliced-knee-development`.

This is the selected DIY development arrangement, without independent
professional engineering review. The assessment concerns the current support
legs, their attachments, the added knees and the retained base details. The
owner accepts the panel construction and excludes floor-friction qualification;
the calculations use explicit no-slip support assumptions. Neither the model
nor this study establishes an unconditional climber weight rating.

**All six archived baseline load cases meet all 21 listed conditional criteria.** The
largest adopted bolt comparison is 0.67414, the largest sampled net-member
comparison is 0.44477, and every sampled member passes the implemented
stability gate. The finite analytical task is complete under the stated
assumptions; this decision does not depend on another speculative design
iteration. Component conformity and the documented assembly checks remain
part of using the selected detail. The current installation adds outward bolt
ends and exterior timber trims. The end-detail assessment below reuses these
baseline forces with an explicit unloaded-tail response approximation; the
six native archives are not newly solved trimmed assemblies.

## Physical arrangement and analytical load path

Each side retains one solid 4x6 leg and one solid 4x6 inclined outer rim, joined
by two half-inch bolts. The knee comprises **two separate, unnotched standard
2x6 pieces**, each 38.1 × 139.7 mm, overlapping by 269.511 mm. Four 3/8-inch
through-bolts connect that overlap. Two further 3/8-inch bolts connect each
knee end to its rim or leg. The complete arrangement has four upper half-inch
bolts, eight knee endpoint bolts and eight splice bolts: **20 bolts total**.
The compact 2x6 base and the small existing inclined-member end trims remain.

The two knee pieces occupy their actual neighboring X positions. Native
baseline analysis represents separate rectangular timber members, individual finite
bolt springs and compression-only contact over the overlap. It credits no
glue, tensile wood tie, interface friction or composite action between the
pieces. This removes the earlier notched 4x6 brace's unresolved shoulder
fracture mechanism; no strength acceptance transfers from that old detail.
Each piece's six bores enter its net section. Its two endpoint bolts and four
splice bolts are checked as separate physical connection groups.

## Finite load cases and result gates

All six specified cases apply 2224.111 N downward, corresponding to twice the
250 lb target's static weight, plus the indicated 300 N horizontal component.
The applied load is 100 mm in front of the face; self-weight and the 25 kg
equipment allowance remain included. The adopted
resistance duration factor is **Cd = 1**; doubling applied load supplies no
automatic duration credit. Archive parameters retain the exact load point,
hold eccentricity, materials and spring assumptions.

The following are demand/reference ratios; at most 1.0 meets the respective
comparison. Every row has status `LISTED_CONDITIONAL_SPLICE_CRITERIA_MET`.

| Archive / load | Bolt, actual Ktheta | Local parallel | Supplemental splitting | Sampled net member | Header stability | Listed criteria |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `a12-rear`, A12, +Y | 0.67414 | 0.15815 | 0.45370 | 0.44477 | 0.32084 | 21/21 met |
| `a12-forward`, A12, −Y | 0.56158 | 0.14684 | 0.37474 | 0.38887 | 0.12826 | 21/21 met |
| `a12-left`, A12, −X | 0.63333 | 0.16799 | 0.42305 | 0.41645 | 0.16548 | 21/21 met |
| `k12-right`, K12, +X | 0.62479 | 0.16568 | 0.41746 | 0.40874 | 0.17360 | 21/21 met |
| `k12-rear`, K12, +Y | 0.66593 | 0.15687 | 0.44827 | 0.43744 | 0.32299 | 21/21 met |
| `a1-rear`, A1, +Y | 0.08958 | 0.03511 | 0.06131 | 0.11613 | 0.21158 | 21/21 met |

Each case must pass native global/member equilibrium, multipoint constraint,
unilateral-contact convergence and closed-bearing checks before resistance is
interpreted. The final result must report every listed conditional criterion
as true. These include actual-angle bolt resistance, an additional conservative
group-action sensitivity, group spacing and directional edge screens, direct
steel and washer resistance, local parallel-to-grain checks, separately labeled
supplemental EC5 splitting, sampled net sections, header/base checks, actual
receiver fit and complete machining inventory.

The stability gate checks **every sampled member section**, not merely the
section with the largest reported net ratio: each section's
`conditional_checked_failure` must be false. The header's full-length
unbraced comparison is also retained. Every bolt-center section must have a
native recovery sample. Contact pressure uses actual compression force divided
by its tributary area and the assumed 625 psi wood-bearing reference. Opening
contacts carry no tensile reaction.

Across all six baseline cases, the other governing quantities are:

| Comparison or geometric reserve | Governing value |
| --- | ---: |
| Original fixed-maximum-Ktheta nominal bolt ratio | 0.70647 |
| Additional conservative group-reduction ratio | 0.67414 |
| Direct combined steel ratio | 0.13608 |
| Washer wood-bearing ratio, catalog dimensional bounds | 0.07626 |
| Washer bending ratio, catalog dimensional bounds | 0.17917 |
| Knee overlap contact wood-bearing ratio | 0.00114 |
| Average header-bearing ratio | 0.03154 |
| Quarter-area header-bearing sensitivity | 0.06383 |
| Conservative retained base end-notch shear ratio | 0.24737 |
| Minimum directional edge/end reserve after modeled allowances | 2.325 mm |
| Minimum component group-spacing reserve | 1.900 mm |

The spacing reserve is reported by its own geometric screen; it must not be
read as an additional unallocated drilling tolerance. All six cases also pass
baseline receiver fit, machining completeness and the existing base end-cut
geometry gate. The new exterior-trim distances are reported separately below.

The force-directed 4D loaded-edge rule is a conservative interpretation for
oblique loading; it is not presented as an explicit universal NDS oblique
minimum. Supplemental EC5 splitting is an additional check, not an NDS
perpendicular-tension allowable. The selected finite case set is not an
exhaustive proof of all possible climbing actions.

## Current outward-bolt and exterior-trim revision

`mini_moonboard/compact_spliced_installation.py` reverses the sixteen bolt
stacks that formerly pointed inward; four leg-end stacks already pointed
outward. All twenty now have heads inward and nuts/threaded ends outward.
The [bolt installation evidence](compact-spliced-construction/bolt-installation-check.json)
checks the unchanged wood, axes, interfaces and hardware envelopes for that
orientation-only revision. The rim-end nominal-diameter shank requirement
increases to **120.1166 mm** because its threads now enter the thinner knee
piece; the hardware and build schedules give all four applicable thresholds.

`mini_moonboard/compact_spliced_trimmed.py` then cuts the six exterior timber
tails. Both rear-leg tops retain **18 mm normal projection** beyond the rim
rear face to preserve the upper-bolt end-distance reference. Rim-end knee
tips finish at the rim rear face; leg-end tips finish at the leg outer depth
face. Existing shorter portions remain unchanged. These are plain end cuts,
not shoulder notches or reduced-width tabs. Nominal angles from square are
36.16°, 4.27° and 49.57°, respectively.

The [current end-detail evidence](compact-spliced-construction/end-trim-check.json)
records all forty actual bolt receivers, revised directional edge/end geometry,
washer seating, the six retained force cases, local connection and hardware
comparisons, and removed timber volume/mass. The rim-end cut leaves only
**0.361 mm** beyond the adopted 7D end-distance reference after the existing
3 mm geometric allowance. The build instructions preserve that allowance;
it is not additional shop tolerance.

Every cut lies beyond the outermost bolt bore stations across the full member
section. The smallest longitudinal separation is approximately **1.138 mm**
at the leg-end knee tip; upper-leg and rim-end separations are approximately
25.650 mm and 57.411 mm. The bolted overlap and the full-section span between
connections remain intact. This geometric observation supports the bounded
**unloaded-tail stiffness approximation**; it does not establish identical
member stiffness. The current detail assessment retains the original native
stiffness, gravity placement, connected-section and stability results while
rechecking end distances, local connections and hardware against all six saved
force cases. Removed timber mass is reported explicitly. No new native solve
or measured behavior is claimed for the trimmed geometry.

For the bevel-ended members, the local parallel-to-grain comparison uses
end stations bounded across the complete bolt-group shear band: the outer
bolt rows plus half the clearance-hole diameter on each side, including the
space between rows. The cut plane is eroded by the retained 3 mm allowance
before obtaining the shortest end station across that band. This avoids
substituting a distant, unrelated bevel corner for every row's available
shear length. The interpretation follows the row shear-line geometry of
[NDS Appendix E, E.3](https://awc.org/wp-content/uploads/2021/10/AWC_NDS2018-withCommentary_20210113_AWCWebsite_Appendix.pdf).
The wood resistance inputs are unchanged; the refined geometric comparison
remains a conditional application to this beveled detail.

The generated profiles and build instructions apply to this current revision;
the archived six-case CAD/source snapshots remain unchanged as its analytical
baseline. This distinction is part of the conditional DIY basis.

## Material and installation basis

Timber resistance assumes dry, unincised Douglas Fir-Larch No. 2 and the
recorded material properties. Bolts are specified SAE J429 Grade 5 with a
conditional **90 ksi Fyb** through the documented NDS tensile-yield route.
The [half-inch hardware assessment](compact-half-inch-hardware.md) and
[splice hardware schedule](compact-splice-hardware.md) identify actual catalog
parts, dimensions, material assumptions and assembly checks. No delivered
hardware lot is represented as tested or inspected.

Washer checks use catalog tolerance bounds, rather than the thicker nominal
rendered washers:

| Washer family | Minimum OD | Maximum bore | Minimum thickness |
| --- | ---: | ---: | ---: |
| Half-inch upper bolts | 34.7472 mm | 14.6558 mm | 2.1844 mm |
| 3/8-inch knee and splice bolts | 25.2222 mm | 11.5062 mm | 1.6256 mm |

The washer plate-yield input remains an explicit 33 ksi material assumption;
the catalog's grade label does not independently establish that numerical
plate-yield value. The direct hardware checks include the recovered axial
increments. No arbitrary bolt preload or friction strength is credited.

The adopted bolt-strength comparisons use nominal diameter. Before assembly,
verify the actual shank and transition so threaded bearing occupies no more
than one quarter of the bearing length in **each** member. Count the transition
as threaded. The referenced hardware documents provide measurable thresholds
for the 177.8 mm upper grip, 127 mm endpoint grip and 76.2 mm splice grip.
Also check that each nut reaches its washer without bottoming on runout and
has full usable thread engagement. These are practical component and assembly
checks; no physical floor test or laboratory bolt test is introduced.

## Root-diameter sensitivity

The result files also recompute all six dowel yield modes with the entire
bearing length reduced to the supplied root diameter, using actual Ktheta and
Cd = 1. Nominal-D perpendicular bearing stress is retained conservatively;
the actual hole and spacing requirements remain based on nominal diameter.
This is a separate sensitivity, **not the adopted strength basis**.

| Case | Actual-Ktheta full-root reference ratio |
| --- | ---: |
| A12 rearward | 0.97659 |
| A12 forward | 0.81340 |
| A12 leftward | 0.91727 |
| K12 rightward | 0.90483 |
| K12 rearward | 0.96453 |
| A1 rearward | 0.12831 |

All these reference-root comparisons, including their additional conservative
group-reduction sensitivity, are below 1.0. The original fixed-maximum-Ktheta
root branch reaches 1.02343 and remains preserved. Neither branch changes the
selected nominal-diameter assembly acceptance requirement.

Its half-inch 0.4056-inch and 3/8-inch 0.298-inch root values are calculation
references, not established delivered minimum diameters. A passing sensitivity
therefore does not waive the nominal-diameter shank acceptance above. The
[Safety Socket thread-limit table](https://www.safetysocket.com/wp-content/uploads/2020/07/Thread_Limits.pdf)
identifies 0.4041 inch as the half-inch UNC class 2A **maximum** minor diameter;
a maximum must not be mistaken for a lower-bound resistance input.

## Evidence and reproducibility

Each directory under `fea/results/compact-splice-study/` contains the compressed
native report, exact geometry, archived source snapshot and manifest. The
resistance report is regenerated without another native solve using:

```sh
uv run --no-sync python -m scripts.compact_splice_results \
  --archive fea/results/compact-splice-study/a12-rear
```

Use the corresponding directory for each other case. The command checks
manifest hashes and report/geometry source identity before calculating the
listed criteria. Its output records the postprocessor and input hashes.
Historical failed upper joints, single-bolt knees and notched-knee results
remain separate evidence; they are not overwritten or relabeled as passing.

The selected DIY decision is conditional on the current installation/trim
geometry, the retained baseline load set and response approximation, and the
documented material, hardware and installation basis. The
machine-readable `qualified_for_design` field remains false: meeting the
listed analytical criteria is not professional certification or an unrestricted
whole-board rating.
