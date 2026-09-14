# Selected compact frame with independent knee splices

2026-09-13. Candidate: `compact-spliced-knee-development`.

This is the selected DIY development arrangement, without independent
professional engineering review. The assessment concerns the current support
legs, their attachments, the added knees and the retained base details. The
owner accepts the panel construction and excludes floor-friction qualification;
the calculations use explicit no-slip support assumptions. Neither the model
nor this study establishes an unconditional climber weight rating.

**All six archived load cases meet all 21 listed conditional criteria.** The
largest adopted bolt comparison is 0.67414, the largest sampled net-member
comparison is 0.44477, and every sampled member passes the implemented
stability gate. The finite analytical task is complete under the stated
assumptions; this decision does not depend on another speculative design
iteration. Component conformity and the documented assembly checks remain
part of using the selected detail.

## Physical arrangement and analytical load path

Each side retains one solid 4x6 leg and one solid 4x6 inclined outer rim, joined
by two half-inch bolts. The knee comprises **two separate, unnotched standard
2x6 pieces**, each 38.1 × 139.7 mm, overlapping by 269.511 mm. Four 3/8-inch
through-bolts connect that overlap. Two further 3/8-inch bolts connect each
knee end to its rim or leg. The complete arrangement has four upper half-inch
bolts, eight knee endpoint bolts and eight splice bolts: **20 bolts total**.
The compact 2x6 base and the small existing inclined-member end trims remain.

The two knee pieces occupy their actual neighboring X positions. Native
analysis represents separate rectangular timber members, individual finite
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

Across all six cases, the other governing quantities are:

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
actual receiver fit, machining completeness and the existing base end-cut
geometry gate.

The force-directed 4D loaded-edge rule is a conservative interpretation for
oblique loading; it is not presented as an explicit universal NDS oblique
minimum. Supplemental EC5 splitting is an additional check, not an NDS
perpendicular-tension allowable. The selected finite case set is not an
exhaustive proof of all possible climbing actions.

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

The selected DIY decision is conditional on this exact geometry, the finite
load set and the documented material, hardware and installation basis. The
machine-readable `qualified_for_design` field remains false: meeting the
listed analytical criteria is not professional certification or an unrestricted
whole-board rating.
