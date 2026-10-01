# Service-level upper-block review, September 30, 2026

This packet supplies current actions for the four service-level upper cleats,
including the shortened upper-right G7, while the main worker continues the
corner assembly and floor-support work. Together with the
[uppermost-block packet](../upper-frame-joint-review-2026-09-30/README.md), it
covers eight cleats and 32 existing bolts in three authenticated response
histories. It establishes extraction and conditional component comparisons,
not complete-joint resistance or a six-case envelope.

The candidate is `compact-floor-flush-wood-joints-development`, revision
`led-clearance-2x6-runner-seated-blocks-v1`. No reviewed geometry, screw axis,
panel outline or starting leg/runner bolt arrangement changed. No native
solve ran. Earlier geometry studies remain history; their passes are not
transferred. The selected screw-and-bracket candidate is separate.

The [code/summary publication policy](../../code-summary-checkpoint-2026-09-30.md)
keeps these scripts and Markdown summaries in Git. Detailed JSON/CSV packets
and their native source evidence remain at their original local paths;
a checkout of this branch alone is not a complete replay bundle.

## Service-block actions

The sources are A12-rear, A1-rear and K12-rear, each at seven printed
increments. These maxima can occur on different bolts; they must not be
combined into an invented simultaneous load. Each resistance comparison uses
the corresponding individual-bolt force and member grain angles.
The recorded loads, unverified no-slip floor assumption, hypothetical
spring/contact laws and gross-member wood stiffness remain the source basis;
the response model does not resolve local bore and cut stresses.

| Current cleat | Largest sampled lateral force | Bolt and case | Largest sampled axial tension | Largest nominal-bearing/root-yield comparison |
| --- | ---: | --- | ---: | ---: |
| Left service outer upper | 33.81 N | `upper_side_1`, A1-rear | 57.21 N | 0.0461 |
| Right service outer upper, WJ-06 | 38.46 N | `upper_side_1`, A1-rear | 54.23 N | 0.0528 |
| Left service inner upper | 36.86 N | `upper_principal_1`, A1-rear | 25.94 N | 0.0508 |
| Right service inner upper, shortened G7 | 30.42 N | `upper_principal_1`, A1-rear | 24.27 N | 0.0416 |

The comparison column uses the explicitly unadopted typical-thread-root
scenario in the earlier upper packet. Ratios below one do not establish
complete-joint acceptance. These service-level demands are much smaller than
the sampled 1,074.79 N and 1,264.69 N uppermost outer-bolt demands, making the
uppermost outer bolts the first upper resistance priority under these sources.
Other support cases and model sensitivities can change that ordering.

The three common service cleats have 88.9 × 88.9 × 119.7 mm outer envelopes.
G7 is 88.9 × 88.9 × **86.9 mm**, with proposed grain along its source `N`
axis. Its two finite cleat contact patches total 7,637.05 mm², compared with
10,552.97 mm² for the common geometry. Those modeled areas are not contact
strengths or proof that the whole face remains engaged.

## G7 detailing and corrected end interpretation

The G7 cleat's `upper_rail_1` station has a 26.95 mm short grain end and a
59.95 mm opposite end; `upper_rail_2` reverses those distances. Both principal
stations have 43.45 mm to either grain end. The upper rail host has a
26.95 mm short cross-grain edge at `upper_rail_2`. In these source histories,
that edge is loaded; it exceeds the pure perpendicular 4D = 25.4 mm screen
by only 1.55 mm. The separate cleat cross-grain minimum is 27.9 mm.
Outer-box comparisons omit internal bores, shoulders, splitting and cut
effects; they provide no fabrication tolerance allowance or oblique-edge rule.

The [method correction and calculations](method-correction.md) distinguish
angle to grain from angle to the bolt axis. They supersede the earlier upper
README's generic suggestion that these lateral grain-oblique forces require
the NDS §12.5.1.2(b) shear-area method. The earlier numerical evidence remains
unchanged. Actual oblique-edge applicability and axial transfer stay open.

Under the declared softwood tension-end interpolation, the full-load G7 rail
pair's minimum eligible square-end factor is 0.846 for A1-rear, 1.000 for
A12-rear and 0.882 for K12-rear. The principal pair's eligible cleat-end
comparison is 1.000; its host-side grain-negative directions point toward the
angled foot profile and are explicitly excluded from the square-end branch.
These are bounded end-branch sensitivities, not adopted connection factors.
The interpolation is supported by official historical Commentary; direct
verification of the corresponding 2024 Commentary remains open. The pinned
2024 specification confirms the separate bolt-axis rule, not the interpolation.
The [end-branch records](conditional-end-branches.json) retain all seven
increments and both members' force signs.

## Declared partially threaded bolt comparison

An explicit thread/runout interval lets the conditional full-body diameter
case be evaluated now. It does not require pretending that a product or
delivered bolt has been identified. The start coordinate `S` is measured from
under the head; all potentially bearing thread or runout at and after `S` is
counted as threaded. A 2.032 mm head washer is declared. For each wood layer
`[a,b]`, the thread overlap is `max(0, b - max(a,S))` and must not exceed one
quarter of that layer's bearing length for this diameter scenario.

| Wood layers from head to nut | Required earliest thread/runout start | Declared start | Worst threaded fraction |
| --- | ---: | ---: | ---: |
| 88.9 mm then 38.1 mm | 119.507 mm | 120.650 mm | 22.00% |
| 38.1 mm then 88.9 mm | 106.807 mm | 120.650 mm | 9.43% |
| 88.9 mm then 88.9 mm | 157.607 mm | 158.750 mm | 23.71% |

The 32 upper axes include 24 with 127 mm wood grip and eight with 177.8 mm
grip. The declarations clear the stricter threshold for each grip family by
1.143 mm. Published bolt `Lb`/`Lg` bounds do not prove these earliest runout
coordinates, nut engagement or a delivered smooth shank.

The full-D scenario uses nominal D = 0.250 in for both bearing and yield
equations, the same unadopted Fyb = 106 ksi Commentary estimate, and each
record's member lengths and grain angles. All six single-shear modes are
retained. No duration, moisture, geometry, group or other end-use adjustment
is applied. Contacting faces and zero gap remain hypothetical applicability
conditions. The NDS effective diameter does not alter the separate steel
tensile or shear areas.

| Upper cleat | Largest nominal-bearing/root-yield ratio | Largest conditional full-D ratio |
| --- | ---: | ---: |
| Uppermost outer left | 1.520 | 1.163 |
| Uppermost outer right | 1.786 | 1.367 |
| Uppermost center left | 0.217 | 0.166 |
| Uppermost center right | 0.225 | 0.172 |
| Service outer left | 0.0461 | 0.0353 |
| Service outer right | 0.0528 | 0.0404 |
| Service inner left | 0.0508 | 0.0422 |
| Service inner right, G7 | 0.0416 | 0.0345 |

The uppermost outer comparison remains above one under this additional
unadjusted, unadopted scenario. That is a concrete follow-up, not an adopted
failure or a reason to move axes without owner review. The
[672-record comparison](partial-thread-comparison.json) and
[CSV](partial-thread-comparison.csv) keep all histories and the separate
root-bearing sensitivity. No bolt capacities are added across a group.

## Evidence, replay and remaining work

[freeze.json](freeze.json) binds the same native decks, DAT files, accepted
responses and parent/all-body decisions as the earlier upper packet. The
wrapper [producer](produce.py) and [checker](check.py) reuse hash-pinned
extraction logic with explicit service-station inputs. They change no source
file or earlier report. All source gates and 92 new / 12 retained / 66 screw
inventory guards remain in force.

[upper-joints.json](upper-joints.json) contains 336 bolt records, 672 signed
member-direction records and 84 block balances. Each balance includes four
lateral planes, four axial outer-seat ties, eight finite contact cells and
the block's discrete source loads, including self-weight. Force and moment
are reconstructed at the named datum using each source's own endpoints.
The independent DAT-token check reproduced all lateral records and signed
directions. [Verification](verification.md) records the checks and limits.

The remaining three whole-frame cases, physical bolt distribution, contact
applicability, applicable member/cut/group resistance, washer/nut transfer
and axial/bending interactions remain required work. The main worker should
keep the corner and floor-support focus and reuse these upper inputs. For
the upper task, first settle the uppermost outer bolts' resistance basis,
then verify the end-method applicability alongside separate edge, spacing and
shared-member checks. Conditional calculations can proceed under declared
properties; none of this selects hardware or releases physical work.
