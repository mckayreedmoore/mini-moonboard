# Panel attachment: a practical decision worksheet

## Corrected added stations and left/right interpretation

**The first 20-screw proposal had unequal left/right gap choices.** Its
longest-gap rule selected the outer and middle horizontal gaps on the left,
but the inner and middle gaps on the right, because the right outer gap
was 3.175 mm shorter. Four right-side hypothetical additions were at
X=252.5375 rather than the comparable outer location X=1016.025 mm.
This is a placement error in the comparison, not evidence that wood frames
naturally have different left/right capacities. Preserve the original
helpers, inputs, response and [count-comparison.json](count-comparison.json)
as evidence for their particular asymmetric stations.

[count_mirrored_layout.py](count_mirrored_layout.py) corrects those four
additions, retaining all existing twelve stations and the proposed count
of twenty per main panel. [mirror_projection.py](mirror_projection.py)
reprojects only twelve changed scalar rows on six right-side bodies using
the existing delta-projection equations. The original twelve-screw operator
block remains byte-identical, and all new points map into the gross meshes.
No live CAD, hold-grid, purchased hardware policy or native solver changes.

The corrected frame completes all twelve states with the existing QP seed
option and unchanged physical equations/tolerances:

| Actual-grid case, modeled bolt clearances | Source 12-screw peak | Corrected 20-screw peak |
| --- | ---: | ---: |
| A12-rear, upper left | 1871.251 N | 1244.179 N |
| K12-rear, upper right | 1603.442 N | 1829.446 N |
| A1-rear, lower left | 987.395 N | 2171.094 N |

Correcting screw placement does not eliminate the side difference or close
the generic reference gap. A12 and K12 carry identical force vectors in
separate cases, but their X coordinates are -1019.2 and +980.8 mm. Relative
to the corrected nearest added screws, their offsets are -1.5875 and
-35.225 mm, so these are not mirrored load locations.

### Bounded right-side load-position probe

One diagnostic translates the saved eight-node K12-rear force patch by
36.8125 mm in X, bringing its relative screw offset to +1.5875 mm. The
nodal forces are interpolated onto the existing gross right-panel mesh.
Force and moment are conserved; a zero-translation oracle reproduces
the original nodal map to 1.14e-9 N. Only this right-side case is solved,
at zero and modeled bolt gaps. This is a different load position from real
K12, not a new hold or replacement design case. No remesh or physical
calibration is implied by the interpolation check.

| Rear case | Corrected left, actual A12 | Corrected right, actual K12 | Right with matched local hold offset |
| --- | ---: | ---: | ---: |
| Zero bolt gaps | 1202.172 N | 1513.495 N | 1276.755 N |
| Modeled bolt gaps | 1244.179 N | 1829.446 N | 1585.342 N |

The matched-offset zero-gap peaks differ by 6.2%; with modeled gaps they
differ by 27.4%. The gap increment is about 42 N on the left and 309 N
in the right position probe. This isolates load location as a contributor
and shows additional sensitivity to the coupled frame's clearance/seating
and contact response. It is not an exactly mirrored mesh/geometry test,
and does not establish that the physical build will have that residual
asymmetry or a unique force allocation. Bounded nonunique seating and
failed strict stiffness/stability flags remain explicit.

### What the screw peak means

All 98 proposed panel/kicker screws are solved in the same coupled frame,
along with frame bolts and compression contacts. Each screw has two lateral
components and one tension-only axial component. The climber force is
applied once per case; the force solution satisfies all screw laws, body
equilibrium and contact laws simultaneously. These are predictions, not
physical force measurements. Equality of screw forces is not imposed.

For the corrected lower-left A1-rear state, all twenty panel screws carry
4466.891 N total tension. The largest carries 2171.094 N, about 48.6%; the
other nineteen together carry 2295.797 N. The next two carry approximately
391 and 385 N. Local bending and backing compression concentrate load at
the new screw near the hold. The larger total than the external outward
load is balanced by contact reactions, as explained in the preserved
first-layout section below. These figures remain conditional on the
unmeasured screw and panel/contact laws.

[mirror-comparison.json](mirror-comparison.json) records all twelve
corrected states, both position-probe states, every loaded-panel screw
tension, source/output hashes and reconstruction commands. Raw packets
remain in ignored `results/count20-mirrored-*` and
`results/right-position-probe-*` paths, with exact launcher snapshots.
Two symmetry-placement tests and helper/projection lint pass; operator
reciprocity is 9.07e-11 relative and the original source hashes recheck.
The position projection used the project environment; its initial frame
import lacked OSQP and produced no frame result. The separate completed
two-state run used the pinned NumPy 2.2.6/SciPy 1.15.3/OSQP 1.0.4 environment.
No further solve or branch search remains active. Preserve the corrected
comparison, probe and original asymmetric packet as distinct evidence.

## Owner-requested 12-versus-20 screw and model check

This section preserves the first asymmetric 20-screw station proposal;
the corrected side-comparable proposal and position probe are above.

**The evaluated 20-screw layout does not close the conditional reference
gap.** It improves the upper-left high-hold case but shifts the governing
demand to an added screw on the lower-left panel. This applies to the
particular proposed stations, not every 20-screw arrangement or the physical
purchased screws. No live candidate or hardware change is adopted.

The comparison starts from the owner's four-upper-station relocation,
[`operators-attempt02`](../upper-corner-screw-layout/operators-attempt02/operator-assessment.json)
and its completed twelve-state 250 lb response. It preserves each panel's
twelve existing stations, including the lower-panel row offsets.
[count_layout.py](count_layout.py) adds two stations in each vertical column
and two in each horizontal rail row, using midpoints of the two longest
current gaps. Eight additions per main panel change 48 main plus 18 kicker
screws to 80 main plus 18 kicker screws: **98 hypothetical total screws**,
outside the existing 66 purchased-axis inventory.

[count_projection.py](count_projection.py) appends 96 scalar connector rows
using the saved native member operators. All 32 added points project into
both gross receiving meshes and pass coarse AABB checks. These do not
certify finished holes, edge distances, hold/LED conflicts, installation or
resistance. Original operator blocks, members, contacts, bolt layouts,
loads and conditional screw laws are retained; added screw mass is omitted.
No CAD rebuild or native solver is launched, and the live reviewed model
is unchanged.

[count_frame.py](count_frame.py) preserves the frozen frame producer. Its
only adaptations change the 66/132 screw inventory guard to 98/196 and pad
raw numerical seeds/reference differences with 96 zeros. No equilibrium
equation, law, tolerance or floor assumption changes. The first attempt
completed six zero-gap states, then stopped on a normal active-set cycle.
One bounded retry using the producer's existing QP seeding option completed
all twelve states; its exact launcher/function snapshots are retained.
No further branch search is active.

| Load case, modeled bolt clearances | 12 screws: peak axial demand | 20 screws: peak axial demand | Simultaneous shear at the 20-screw peak |
| --- | ---: | ---: | ---: |
| Upper-left A12-rear | 1871.251 N | 1243.913 N | 503.053 N |
| Upper-right K12-rear | 1603.442 N | 1550.561 N | 724.349 N |
| Lower-left A1-rear | 987.395 N | 2171.245 N | 173.278 N |

The 20-screw nominal envelope governs at added bottom-rail station
`hyp20_main_lower_left_edge_gap_1`, with 0.807251 mm modeled opening.
Its zero-gap envelope is 2071.947 N at the same station, versus the old
1923.816 N upper-left zero-gap envelope. Extra springs change local
compatibility and prying; dividing the old peak by the count ratio is
invalid. The 2171 N peak exceeds the retained 277–629 N unadjusted head
references and explicit 1006 N favorable duration-adjusted head scenario.
These are conditional ASD references, not measured Hillman breaking loads.

Read-only recovery of the saved responses explains part of the unexpected
lower-panel increase. The added governing screw is only 1.5875 mm from
A1's X coordinate and 36.75 mm upslope of its face patch. Its source live
force/moment gives approximately 90.1 N m about the screw's front-face point.
At that same new station, probing the old response with the appended
`D a + e - H f` row gives 2.997833 mm nominal-gap opening without the screw;
the new response gives 0.807251 mm with it. At zero bolt gaps the respective
values are 4.202036 and 0.770333 mm. These are conditional relative panel/
receiver motions, not physical measurements or new solves. The old 987 N
maximum is at a different station, so comparing peak forces alone hides
this local improvement in restraint.

For A1-rear at modeled gaps, the lower panel's total external outward
normal load, including its proportional dead load, is 1775.487 N in both
models. Its twelve-screw response balances 2622.318 N total screw tension
against 846.831 N net outward contact force. The twenty-screw response
balances 4469.319 N tension against 2693.832 N net outward contact force:
in each case, tension minus net contact equals the same external load.
The net contact term includes the kicker interface; it is not solely the
sum of unsigned backing pressures. Contact/tension couples can amplify
individual forces while preserving equilibrium. Recovered external load
work also decreases in both compared rear cases when the added springs
are present. These checks make the higher individual screw demand
mechanically coherent; they do not calibrate the contact or spring laws.

### Local bending benchmark and official backing comparison

[count_benchmark.py](count_benchmark.py) isolates upper-left panel-normal
translation/bending with fixed receivers, the same screw/contact stations
and normal load/moment. It compares rigid plywood with the saved elastic
plywood operator. Both omit frame motion, panel-seam constraints and
in-plane connector reactions. The elastic version retains the panel's
elastic response to the full load vector, while rigid balance is projected
onto three normal/bending coordinates. Neither replaces the full frame.

| Upper-left A12-rear, fixed receivers | 12 screws | 20 screws |
| --- | ---: | ---: |
| Rigid panel: largest axial force | 396.794 N | 229.870 N |
| Elastic panel: largest axial force | 2130.507 N | 1402.797 N |

Large concentration persists without frame movement or its bolt-clearance
iteration. This identifies local plywood bending, contact and screw
compliance as a useful fidelity question; it does not validate those
properties or justify adopting a rigid panel to claim a pass. The saved
panel material is a conditional APA Group 1 equivalent-layer fit with
unobserved face axes and out-of-plane proxies. Preserve the purchased
[Roseburg AC fir identification](../../../../purchased-materials.md);
remaining property questions concern that product/lot.

Moon's [Mini DIY guide, page 2](https://moonclimbing.com/media/moonboard-pdf/How-to-build-a-MoonBoard_v2.3.pdf)
specifies four uprights spaced **813 mm** apart. This candidate's main-panel
rim/center screw columns are approximately **1130 mm** apart. Its upper-left
panel has normal timber contacts only on the rim, center principal, top
rail and service rail, with no intervening upright contact. Moon also
requires [horizontal bracing across panel joints](https://us.moonclimbing.com/blogs/guides/how-to-build-your-moonboard)
and supplies [birch plywood panels](https://moonclimbing.com/mini-moonboard-diy-panels.html).
Therefore equal screw count does not establish equal support, panel bending
or connection demand. The quantitative effect of these differences has
not been evaluated here, and the video's count remains the owner's report.

### Measured climbing forces and design actions

The current 250 lb case applies **2.224 kN downward, or 2.0 bodyweights**,
plus 300 N horizontal, or 0.270 bodyweight, at one hold 100 mm outward from
the face datum. The 2x includes static weight; it is not added twice.

| Primary source | Finding | Limit |
| --- | --- | --- |
| [Fuss and Niegl, 2010](https://www.researchgate.net/publication/225113929_Biomechanics_of_the_two-handed_dyno_technique_for_sport_climbing) | Nine climbers, 45–60 kg; upper-hold vertical catch peaks 1.1–1.63 bodyweights after two-hand dynos. | Rescaling 1.63 to 250 lb gives 1.813 kN, about 23% below our case. This is an inference, not a measured 250 lb result or upper bound. |
| [Hugues et al., published 2025](https://mbj.episciences.org/en/articles/14571) | Seven experts; peak of averaged total vertical support profile 2.26 bodyweights. Separate hand/foot profiles peak at 0.84/1.57 at different times. | Short conference paper about four-contact takeoff, not single-hold catching or individual maximum-force bounds. |
| [CWA first edition, January 2009](https://www.cwapro.org/file/secure/cwadesignpecfinal2022.pdf) | Table 1 specifies 1.2 kN unroped-climber live load; current 2.224 kN is 1.85 times that action. | Specified design action, not measured maximum or failure resistance. Scope is stationary/fixed-in-place, not specifically portable. Filename/hosting does not make it a new edition. |
| [Official EN 12572-2:2017 preview](https://preview.sist.si/sist-preview/39968/eb82f102549541eba9b79bad025432c2/SIST-EN-12572-2-2017.pdf) | Structural integrity uses characteristic actions and Annexes A/B; panel deflection uses 0.8 kN. | Service deflection, strength and panel-insert qualification are separate checks. Preview omits full annex factors; no standard-based reduction is adopted. |

Hugues also reports opposed antero-posterior hand/foot profiles peaking at
0.66/0.55 bodyweight, with mean net force about 0.053 bodyweight. A modest
net horizontal force can coexist with larger local forces and a contact
couple. This does not calibrate our 300 N at one hold. Neither dynamic
paper establishes the 100 mm hold lever or matches our 40-degree/250 lb
conditions.

**Assessment:** 2x bodyweight is a plausible screening case, neither an
absurd magnitude nor a proven dynamic bound. Full single-hold concentration
is demanding relative to multi-contact movement. Reducing it solely to
obtain a screw pass is unsupported. The method is arithmetically consistent
and useful for sensitivities; local peaks remain conditional on the screw
laws, sheet properties and backing/contact fidelity. Reconcile those
assumptions before selecting an attachment correction.

### Receipts and finite closure

[count-comparison.json](count-comparison.json) retains all 24 frame-state
comparisons, simultaneous shear/opening, source/output hashes, commands and
runtime versions. Bulky raw operators/responses are in ignored
`results/count20-*` paths. The first stop is preserved; the completed packet
is [count20-frame-attempt02-qp](results/count20-frame-attempt02-qp/comparison.json).
Restore its `count-only-launcher.py.snapshot` to a temporary Python file
and use the recorded pinned command with fresh output directories.
Projection used Python 3.12.3/NumPy 2.5.2/SciPy 1.18.1; frame and benchmark
used NumPy 2.2.6/SciPy 1.15.3/OSQP 1.0.4.

Three layout tests and centered/eccentric four-tie known answers pass.
All 24 benchmark states meet their balance/law tolerances. Maximum
20-screw frame force, moment, finite-law and circular-gap residuals are
`1.46e-11 N`, `1.65e-8 N mm`, `1.35e-6 N` and `9.07e-9 N`.
Projection reciprocity is `9.09e-11` relative; old H/D/e blocks are unchanged.
An independent read-only review found no algebra/index/count-adaptation
error. Six lint advisories remain in already frozen helpers; no clean-lint
claim is made. The `reviewed_geometry_changed` flag denotes a hypothetical
model difference, not approval of added screws. No force-case or native
run remains active. Preserve this comparison and failed attempt as evidence;
physical fit, actual Hillman resistance and release remain unestablished.

**Preserved all-outer/soft-law results (attempt05–07):** none of those three
saved compatible frame allocations meets declared unadjusted head references.
Reducing assumed withdrawal stiffness from 2689.7 to 100 N/mm lowers their
modeled-gap withdrawal peak from 1812 to 916 N while increasing opening from
0.67 to 9.16 mm. Their stiffness sensitivity does not close panel attachment.
Panel-only statics permits about 294 N when face compression can redistribute,
but neither those compatible runs nor a Hillman rating establishes that
allocation. The current bounded all-two-receiver baseline and a separate
100 N/mm sensitivity are documented at the end. The latter lowers the
modeled-gap withdrawal peak to 907 N but still exceeds every declared head
reference; its favorable generic combined index reaches 3.0068.

## Preserved attempt05 all-outer baseline: inputs and demands

[attachment_screen.py](attachment_screen.py) reuses the parent's
[all-outer six-case frame packet](../all-outer-corner-frame-attempt01/comparison.json):
both top and bottom outer corners and both left outer service cleats have
modeled clearance. The saved packet contains six independent full static
cases, each at zero and modeled gaps. It retains the 25 kg proportional
accessory allowance and conditional 2689.679 N/mm screw scalar stiffness.
These are different loads from the service worker's twice-recorded rear cases.
All values in this section through the reproduction record below describe
attempt05 or its separately sourced 1000/100 N/mm sensitivities.

The current receiver packet supplies all 66 axes, including the four moved
center-kicker axes entering the center posts. Historical backer identities
in `source-inventory.json` are not used as current receivers. The calculation
joins **792 screw states**, three signed scalars per state, and 48 upper-panel
static allocation problems. It checks the saved screw laws, body equilibrium,
orthonormal force bases, receiver identities, and LP primal/dual residuals.
No frame solve, CAD regeneration or native run was performed by this worker.
The later sensitivity section reuses two additional parent frame responses.

| Saved state | Screw and receiver | Withdrawal | Simultaneous lateral force |
| --- | --- | ---: | ---: |
| A12-rear, modeled gaps | upper-left `edge_2`, into `base_rail_top` | 1811.6 N | 743.7 N |
| K12-rear, modeled gaps | upper-right `rim_4`, into `base_side_right` | 623.1 N | 1214.3 N |

The first row is the largest withdrawal; the second is the largest lateral
force. They are separate states and are not combined into one demand.
The largest zero-gap withdrawal is 1911.8 N at upper-left `edge_2`.
The complete signed records remain in
[screw-states.csv](results/attempt05-baseline/screw-states.csv).

## Withdrawal and combined loading

For a qualifying cut or rolled wood screw entering timber side grain
perpendicular to its fibers, NDS 2024 §12.2.2 gives
`W = 2850 G² D` lbf/in of threaded penetration. With the standard No. 10
diameter hypothesis `D = 0.190 in` and DF-L reference `G = 0.50`:

| Effective timber thread penetration hypothesis | Unadjusted withdrawal reference | 1811.6 N / reference |
| --- | ---: | ---: |
| 30.0 mm | 711 N | 2.55 |
| 38.1 mm | 903 N | 2.01 |
| 42.33 mm, approximate standard cut-thread scenario | 1004 N | 1.81 |
| 45.24 mm, full nominal timber projection | 1073 N | 1.69 |

The purchased nominal 63.5 mm length minus assumed 18.25625 mm plywood gives
45.24375 mm tip projection into timber. It does not establish effective
thread penetration. Appendix Table L3's approximately `2L/3` cut-thread
length gives the 42.33 mm illustrative scenario; actual unthreaded portions,
tapered tip, installed head position and product conformity remain unverified.
The reference also needs applicable adjustments and the §12.2.2.5 steel-root
tension limit. Neither root geometry nor steel resistance is established.

Across explicit `G = 0.45–0.55` and the four thread-length hypotheses, the
modeled-gap peak/reference ratio is **1.40–3.14**, before end-use adjustments.
The density sweep is hypothetical, not a replacement for the DF-L reference.

For this same peak state, §12.4.1 gives the combined-demand index
`V²/(R Z′) + T²/(R A′)`, where `R = sqrt(V²+T²)` and `A′ = W′p`.
Even allowing `Z′` to tend to infinity, the withdrawal term is 1.56 with
`G=.50` and full nominal projection, or 1.29 at the most favorable declared
withdrawal reference. Thus no finite lateral reference makes this fixed state
pass those unadjusted combined-reference scenarios. No Hillman lateral
resistance or adjusted connection capacity has been assigned.

## Head transfer: conditional equation path, not a product rating

NDS §12.2.5 uses circular head perimeter and net side-member thickness.
**Flat/countersunk profile alone does not exclude the equation.** The AWC
[supporting pull-through study](https://awc.org/wp-content/uploads/2021/12/2018-nds-head-pull-through-paper.pdf)
includes flush countersunk flat-head screws and models their net thickness
by subtracting one-third of head depth. This supporting research establishes
a conditional calculation path; it does not authenticate model 42605.

The declared sensitivities use plywood `G=.42/.50`, circular head diameter
7.5/9.2202 mm, and net thickness 14/17.25625/18.25625 mm. The 9.2202 mm value
is the standard No. 10 Table L3 hypothesis; 17.25625 mm illustrates a 3 mm
head-depth subtraction by the study's rule. The 14 mm value is a separate
reduced-net-thickness sensitivity. These are not measured product ranges.
Table 12.2F footnote 2 explicitly directs the head calculation to Table
12.3.3B: `.50` for Structural I/Marine and `.42` for other plywood or
unknown species. These values have a normative path for the head reference;
the actual grade/species assignment remains conditional. The research
study's effective `G=.50` does not override that assignment. See the
[corrected reference basis](../upper-corner-screw-layout/head-reference-basis.md)
for the equation, geometry bounds, duration adjustment and design reduction.
Actual panel grade is not claimed inspected. The selected countersink tool
does not supply head diameter, head depth or remaining panel thickness.

The resulting unadjusted head references are **277–629 N**; the saved
1811.6 N peak is **2.88–6.54 times** those references. For the standard-head
and 3 mm depth hypothesis, the references are 419 N at plywood `G=.42` and
594 N at `.50`. Product applicability, net geometry, end-use adjustments,
installation and simultaneous screw action remain conditional.

These are unadjusted ASD design allowances, not observed breaking loads.
The explicit favorable connection-duration scenario `CD=1.6` raises the
largest retained 628.941 N reference to 1006.306 N. Duration is not selected
by the word dynamic and does not remove the frame's separate 2× force
assumption. The relocated 250 lb nominal demand of 1871.251 N still exceeds
that favorable comparison. No physical test has failed.

## Does the existing geometry allow useful redistribution?

Each LP minimizes the largest of twelve nonnegative screw forces. The first
preserves the saved screw axial wrench and holds contact and lateral forces.
The second preserves the net panel normal wrench while allowing existing
normal face compression to redistribute; seam contacts and lateral forces
stay fixed. All six force/moment components are retained, rather than equal
dividing an aggregate force.

| Upper panel, modeled gaps; envelope across six cases | Saved largest tie | Best statics with contacts fixed | Best statics with face compression free |
| --- | ---: | ---: | ---: |
| Left | 1811.6 N | 856.2 N | 293.7 N |
| Right | 1542.4 N | 680.7 N | 293.4 N |

The columns have different governing cases. The LPs omit elastic
compatibility, normal opening/closure and individual receiver equilibrium.
Their allocations cannot replace the frame forces. In particular, the
294 N result exceeds the 277 N lower head sensitivity, while falling below
the standard-head scenarios. Force sharing and head geometry both matter.

## Earlier all-outer source: returned compatible stiffness sensitivity

The parent completed the proposed 2689.7, 1000 and 100 N/mm withdrawal sweep,
retaining the original 2689.7 N/mm lateral components, unchanged 66 stations,
six clearance joints and independent six-case floor/contact method. These
are explicit study hypotheses, not measured Hillman stiffness bounds.
The frozen `all-outer-corner-frame-attempt01` response is attempt05's input.
Attempts06 and 07 use separate parent comparison packets for their 1000 and
100 N/mm hypotheses. These are sensitivities; they do not establish a selected
screw law or replace attempt05's force allocation.

| Withdrawal stiffness hypothesis | Largest modeled-gap withdrawal | Lateral force at that same screw/state | Opening at that screw | Largest lateral force across modeled-gap states |
| --- | ---: | ---: | ---: | ---: |
| 2689.7 N/mm | 1812 N | 744 N | 0.67 mm | 1214 N |
| 1000 N/mm | 1240 N | 848 N | 1.24 mm | 1232 N |
| 100 N/mm | 916 N | 969 N | 9.16 mm | 1377 N |

The last column has separate governing screws/states. The two softer runs'
withdrawal peak moves to upper-right `edge_2`, into `base_rail_top`, K12-rear.
Their zero-gap peaks are 1314 and 951 N, respectively; ignoring zero-gap states
would omit part of the declared sensitivity envelope. The 100 N/mm peak is
1.54 times the standard-head/reduced-net reference of 594 N, and 1.46 times
the most favorable declared 629 N head reference. Even the softer run supplies
no normal-duration, unadjusted head-reference pass.

The returned motions are checked against `q = D a + e - H f`, with both the
signed spring laws and saved body equilibrium retained. At the governing
screw's single common datum, returned rigid motion components are:

| Withdrawal stiffness | Panel rigid motion `(x,y,z)`, mm | Receiver rigid motion `(x,y,z)`, mm | Rigid relative translation | Total connection relative translation |
| --- | --- | --- | ---: | ---: |
| 2689.7 | `(0.135, 5.229, -4.393)` | `(0.331, 5.440, -4.465)` | 0.297 mm | 0.728 mm |
| 1000 | `(-0.217, 5.692, -4.729)` | `(-0.410, 5.794, -4.723)` | 0.219 mm | 1.279 mm |
| 100 | `(-0.199, 8.769, -7.305)` | `(-0.351, 5.593, -4.556)` | 4.203 mm | 9.168 mm |

The first row uses the upper-left datum; the other rows use its upper-right
counterpart. Each row compares both bodies at the same point. Total relative
motion includes the elastic contribution from both bodies; their individual
absolute elastic motions are not reconstructed. No permissible opening or
motion limit is adopted. These values do not establish installation fit or
in-service behavior.

The parent's [90 N/mm attempt](../panel-stiffness-attempt03-k90/stop.json)
stopped at K12-rear, zero gaps, after four completed cases: its method rejected
positive spring normal motion beyond the declared 10 mm domain. It has no
complete twelve-state response and supplies no accepted replacement force
allocation. This is a model-domain STOP, not a claimed physical failure or
an adopted 10 mm installation tolerance. No domain limit is relaxed here.
The stop record SHA-256 is `7ee95762e306faf51ae628a27130f640430b6624206a6d2829c3ba4742883247`; its preserved producer matches the
1000/100 N/mm parent snapshots. Among the three completed compatible
hypotheses, the smallest modeled-gap peak remains 916 N, exceeding every
declared unadjusted head reference. The stopped attempt does not establish
whether another physically supported law would give a valid lower peak.

The later [quarter-stiffness trial for both axial and lateral components](../panel-stiffness-attempt04-kquarter-both/stop.json)
uses 672.4 N/mm for both directions. It completed seven zero/gap cases before
stopping at A12-forward, modeled gaps, on a normal active-set cycle. Its stop
record SHA-256 is
`3af6ba147ef9e16ee13c6dddc9a06448a662e3e89ea70453a508806b2ab3a7d8`.
This trial also supplies no complete accepted force set and makes no physical
failure claim. Both stopped trials remain preserved by the parent and do not
replace the baseline or the three completed postprocessing packets.

At the 100 N/mm peak, the unadjusted `G=.50`, full-nominal-penetration
withdrawal reference is 1073 N. The same-state NDS §12.4.1 combined equation
would additionally require at least **1704 N** lateral reference at that screw.
The envelope across all modeled-gap screws requires at least **1876 N**,
at upper-left `rim_4`, A12-rear. No Hillman lateral reference is assigned.
The 1000 N/mm peak would require 10.43 kN lateral reference under the same
withdrawal hypothesis. These are required-reference thresholds, not available
capacities; head pull-through remains a separate unmet reference screen.

### Finite decision and next useful check

For the preserved attempt05 batch, **head pull-through and timber withdrawal
both decide that screen**. Its 1812 N modeled-gap demand exceeds the
most favorable declared 629 N unadjusted head reference; its same-state
withdrawal term already exceeds one before adding lateral demand. Verifying
that the delivered screw matches standard No. 10 head/thread dimensions would
resolve applicability facts, but would not close these numerical deficits.
The favorable 294 N static allocation cannot be substituted into the batch.

The deciding compatible-sharing question is whether a defensible normal
head/withdrawal and contact response can produce forces below an applicable
head reference while meeting same-state combined loading and acceptable
motion. The completed axial-only stiffness sweep does not demonstrate that.
Further stiffness values should follow an explicit physical law or declared
bounded scenario; selecting a smaller number solely to obtain a pass is not
a supported sharing result. The parent owns that model choice and its runs.

**Robust within the calculated hypotheses:** the attempt05 high-stiffness
allocation concentrates panel forces; reducing axial stiffness lowers peak
withdrawal but does not approach the favorable 294 N static allocation and
increases movement and lateral demand. None of the three saved responses
passes the declared unadjusted head scenarios.

**Assumption dependent:** actual load sharing, applicability and adjustments
of the generic equations, effective timber thread length, head/net-plywood
geometry and the steel root/bending resistance. No SPAX values or installation
rules are transferred. Normal-duration references are retained; no favorable
duration factor is selected to close the screen.

**Next single check:** establish an applicable Hillman 42605 head transfer
basis, including actual circular head diameter/profile, installed net plywood
thickness and any defensible adjustments. The product record supplies no
technical head dimensions or pull-through rating. Under the current normal-
duration `G=.50` reference with full 18.256 mm net plywood, resisting the
916 N softer-run peak would require a circular head diameter of approximately
13.4 mm; the standard No. 10 hypothesis is 9.22 mm. This is a numerical
requirement, not a proposed product substitution or permission to countersink
deeper. Product thread/root conformity and lateral resistance also remain
unresolved. The main agent owns any further frame run or design decision.

An October 2 targeted product-source check found that the exact
[Lowe's 42605 specification](https://www.lowes.com/pd/Hillman-10-x-2-1-2-in-Ceramic-Deck-Screws-50-Count/999995042)
still supplies nominal size, flat head style, coarse thread and steel material,
without the required head geometry or resistance values. Manufacturer-site
searches did not locate an applicable 42605 technical drawing. The direct
manufacturer Q&A answer could not be reopened; its prior record is preserved,
not independently reauthenticated by this lookup. This observation concerns
the retrieved sources, not all possible manufacturer information.

The [bounded fact screen](results/product-fact-check01/observations.json), SHA
`96c40656a1cd8a03080060800cb48e03c47d34a737fe06e14519be05e7fc141d`,
binds the 100 N/mm demand report and missing facts. At the declared 9.22 mm
head and `G=.50`, the generic equation reaches only 794 N as thickness grows
beyond its saturation threshold. Thus increasing the assumed remaining
plywood thickness alone cannot meet the 916 N peak under that head hypothesis.
This is equation sensitivity, not a proposed thicker panel, actual density
measurement or adopted head capacity.

## Reproduce and preserve earlier all-outer/soft-law screens

```bash
uv run python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/panel-attachment/attachment_screen.py \
  --output /tmp/panel-attachment-reproduction
```

The default frozen source comparison SHA-256 is
`ec69b49c821a56fdde76d94148405f9f743e4f72add17c89d35af512be76f6a3`;
its response is
`aa70480aa18c33bb1cbd7d3a53ff582a0c7a90c93487f92721619474ec251901`.
Preserved default output is [attempt05-baseline](results/attempt05-baseline/comparison.json),
report SHA `da36efb1d343f5462fdda87055c38b635767e517a3ead5ac8e69922dbe4cc112`;
[receipt](results/attempt05-baseline/receipt.json) SHA
`255711e7289373e85675bc895d68bb137e18c5e991edac2b29f23039d8abb04f`.
It binds the unchanged original source and adds returned-motion and 264
same-state panel/receiver screw-group wrench records. Group records contain
screw actions only; contact and other joint actions are not inferred from them.

| Reused parent response | Parent comparison SHA-256 | Screen report SHA-256 | Screen receipt SHA-256 |
| --- | --- | --- | --- |
| [1000 N/mm](../panel-stiffness-attempt01-k1000/comparison.json) | `0fdef54e1c4c917a9e36a82b6bf375699b3c8f957b1ac4cc4507c753fbcd130c` | `ac1a6f0788661c9404e838d268ecabd66b45b6a69f8e26ec10bd3ae2abd1f3c3` | `6dbd5a55e629906b79f59ef2f6a50883e7be9a2b268ba7c8b77005585e456ed0` |
| [100 N/mm](../panel-stiffness-attempt02-k100/comparison.json) | `987bbd58316da45ac7e9bff2d6fc13109d86ac56f308a3545acd322e1bba50d6` | `45be72a715652f9770a0235c3468528cc8e15a85b35c49ed55d445c495c5ded8` | `68ec8f4eb3afcb05f61d2e27d0764e7ac271b47e0e2a01367c6e90c6315fa7ea` |

The two screens are [attempt06-k1000](results/attempt06-k1000/comparison.json)
and [attempt07-k100](results/attempt07-k100/comparison.json). Reproduce either
with `--source` pointing to its parent directory and a new `--output` directory.
All three share producer SHA
`e791bb3e914fcbfa70e4e28deb827d0cfc68d93d8c1a11e50e9dc2e52ad11e61`.
Each joins 792 screw states, checks saved motions and laws, and solves the same
48 small panel-only LPs. No software tests or review loop were added or run.

The pinned 2024 [Chapter 12](../../upper-block-strength-2026-10-01/source-cache/chapter12-2024-awc-20260911.pdf)
SHA is `53f6ec05dfd1ceabeccd4d6e88c342111678d3da4631ee7b482b706f77c1780f`:
printed pp.83–84 for withdrawal/head equations, p.95 for plywood SG and
p.97 for combined loading. Appendix Table L3 is printed p.193, SHA
`1fa2bcf52803b1bbed8ea30cf13551dd5f76c90bf110ac475b401f81d116ec31`.
The supporting paper is preserved once at
`/tmp/upper-panel-awc-head-pull-through-paper.pdf`, SHA
`b0f7b80cfa891b4babea733894ee856b3da944abb8ce9a982477cb90c4887e2f`.
If absent, retrieve the same published PDF from its
[AWC asset URL](https://web-media.awc.org/wp-content/uploads/2021/12/17210650/2018-nds-head-pull-through-paper.pdf)
and verify that hash before running. It is a shared source, not copied into
each calculation.

Attempts05–07 and adjacent stopped trials remain byte-preserved historical
evidence under their original all-outer and soft-law sources. The current
attempt08 all-two-receiver source is separate. All raw outputs and referenced
`/tmp` evidence remain available. The 47-criterion authority and release flags
are unchanged; complete joint acceptance and physical release remain false.

## Current bounded all-two-receiver screen: attempt08

The current source is
[`two-receiver-frame-attempt03/comparison.json`](../two-receiver-frame-attempt03/comparison.json),
SHA-256 `0ff0dfc00c112a906910641141fd242f4a58295aa3324ca569132a3fa2d388a5`,
with response SHA-256
`774c3bbddf8061f6b9d1cfdd5f22efbeb1025bd57431a249912ae8e60a731f52`. The
producer calls the parent's `frame_state_contract.force_state_scope` before
replaying arrays and records its returned scope in both the report and
receipt. Helper SHA-256 is
`22e1f8b864c03469701010fc856a815b3604a4efde2748531e36d284050266e5`.

All six nominal states have finite bounded fixed-force seating certificates:
A12-rear, A12-forward, K12-rear and A1-rear rank 296; A12-left and K12-right
rank 297. These certificates permit saved-force component arithmetic. They do
not establish a unique pose, strict tangent stability or complete joint
acceptance. The saved positions are representative positions only for this
bounded source; they provide no envelope over permitted seating and no motion
acceptance limit is adopted.

The screen joins **792 screw states**, runs **48 panel-only allocations** (24
fixed-contact and 24 contact-relaxed), and completes **264 common-port motion
group checks**. Each group check verifies finite common-datum motion values for
its saved panel/receiver group and state. Values remain representative source
positions; checks do not construct a seating-motion envelope.

The current full-state and modeled-gap withdrawal peaks are both A12-rear,
`round_panel_upper_left_edge_2`, into `base_rail_top`:

| Source state | Withdrawal T | Lateral resultant V | Generic withdrawal reference | Demand excess / ratio | Generic head reference | Demand excess / ratio | NDS 12.4 withdrawal term |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Zero gap | 1911.837 N | 730.822 N | 1072.630 N | 839.208 N / 1.782384 | 594.490 N | 1317.347 N / 3.215927 | 1.664889 |
| Modeled gap | 1836.884 N | 807.662 N | 1072.630 N | 764.255 N / 1.712506 | 594.490 N | 1242.394 N / 3.089848 | 1.567661 |

Withdrawal reference uses generic DF-L `G=.50`, No. 10 `D=.190 in`, and
45.24375 mm nominal timber projection; effective thread engagement remains
unverified. Head reference uses the declared standard-head 9.2202 mm diameter
and 17.25625 mm net-plywood scenario. Both are unadjusted conditional
references, not Hillman capacities. The NDS 12.4 withdrawal term exceeds 1.0
in both states, so required lateral reference is undefined for these
combined-reference screens. No product resistance or selected screw law is
inferred. Attempt08 uses saved 2689.6788 N/mm withdrawal and lateral
stiffnesses; product laws remain unmeasured.

Current artifacts:
[comparison.json](results/attempt08-all-two-receiver/comparison.json), SHA-256
`7146069ad3ecf913cbb354f3a37d1e6af6768fc3b577f574feb5a10bd483eb2f`;
[receipt.json](results/attempt08-all-two-receiver/receipt.json), SHA-256
`fd0ea72c61bd3ff8bc7295b68a639d5f9ef9174e119bb8f4cd03d2bf8ff34217`;
[screw-states.csv](results/attempt08-all-two-receiver/screw-states.csv), SHA-256
`a074b374f487ed05865a20c62f5395898338ceb9bce6f2e204406e84316d2e51`.
All 20 report source bindings match; receipt binds comparison, CSV and exact
producer snapshot hashes. The prior attempt05–07 reports, receipts, CSV files
and producer snapshots remain byte-identical.

```bash
uv run python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/panel-attachment/attachment_screen.py \
  --source docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/two-receiver-frame-attempt03 \
  --output /tmp/FRESH-PANEL-ATTACHMENT-ATTEMPT08
```

Attempt08 postprocessing performed no test suite, native/frame/CAD solve,
product, geometry, stiffness or authority change.

## All-two-receiver 100 N/mm sensitivity: attempt09

The parent replayed the already-declared **100 N/mm withdrawal hypothesis**
on the current all-88-two-receiver-clearance frame. All 132 screw lateral
components retain 2689.678816784642 N/mm. The 66 axes, geometry, frame
operators, mass, proportional equipment load, four zero-gap continuous bolts
and twelve zero-gap retained bolts remain unchanged. The baseline force source
and component table remain `two-receiver-frame-attempt03/`; this separate
unmeasured screw law is not selected.

All six zero-gap states pass the original conditional balance, connector,
floor and model-domain gates at rank 300. All six modeled-gap states pass
those gates with bounded fixed-force seating at rank 296/297. Floor/contact
branches are evaluated for each state rather than inherited from an earlier
response. The original 10 mm normal-motion domain is retained. The saved
positions below remain representative positions, not a unique pose or a
motion envelope. No complete joint acceptance follows from these statuses.

The governing withdrawal screw is K12-rear,
`round_panel_upper_right_edge_2`, into `base_rail_top`:

| Frame gaps | Withdrawal T | Simultaneous lateral V | Representative opening | T / 594.490 N head reference | T / 628.941 N largest head reference |
| --- | ---: | ---: | ---: | ---: | ---: |
| Zero | 951.104 N | 935.548 N | 9.511044 mm | 1.599865 | 1.512232 |
| Modeled | 906.577 N | 1022.807 N | 9.065770 mm | 1.524965 | 1.441434 |

The 594.490 N comparison uses the standard 9.2202 mm circular head,
17.25625 mm net-plywood and `G=.50` hypothesis. The largest head reference
remains 628.941 N. Neither is a measured Hillman capacity. The modeled-gap
peak is 0.845191 of the optimistic 1072.630 N timber-withdrawal reference;
this separate comparison does not satisfy head transfer or simultaneous
loading. At that same screw, the favorable generic combined index is
**2.212313**, requiring 1742.039 N lateral reference instead of the declared
463.413 N. The combined envelope is **3.006796** at a different screw,
K12-rear upper-right `rim_4`, with simultaneous **V=1405.398 N,
T=654.820 N**. See the [same-state comparison](lateral-reference.md#all-two-receiver-100-nmm-sensitivity).

The same 48 panel-only LPs give the following modeled-gap envelopes:

| Upper panel | Best statics with contacts fixed | Best statics with face compression free |
| --- | ---: | ---: |
| Left | 637.392 N | 293.353 N |
| Right | 586.033 N | 293.261 N |

These allocations omit receiver equilibrium, elastic compatibility and the
contact laws. They cannot replace the compatible frame response. Relative
to the older six-joint 100 N/mm hypothesis, adding all 88 two-receiver
clearances lowers the withdrawal peak from 916.049 to 906.577 N while raising
the favorable combined envelope from 2.9446 to 3.0068. It does not close
panel attachment. Further law values require a physical basis or a declared
bounded scenario; no value or favorable adjustment is selected to obtain a
pass. Any proposal changing the panel-edge or fastener constraints remains
subject to the pending owner choice.

The attachment screen checks **792 simultaneous screw states**, **48
panel-only allocations** and **264 common-port motion groups**. All 123 frame,
20 attachment and 12 lateral report source bindings match. Exact producer
snapshots are retained; outputs are local ignored evidence.

| Artifact | SHA-256 |
| --- | --- |
| `../two-receiver-panel-k100-attempt01/comparison.json` | `94a2c822c092bfb69ec3c8364740bbb776c7687c081908f20427540e076378e6` |
| `../two-receiver-panel-k100-attempt01/response.npz` | `078bd082f1b74a50105ae25d9a2b289b7a02520e224a85487c052d5abf1b957b` |
| `results/attempt09-all-two-k100/comparison.json` | `baf90788bb1e0c42c6115bdee04109ad8361f6c5a96635d120c41c935d01d301` |
| `results/attempt09-all-two-k100/receipt.json` | `7937655e7f9ef9110bd81117fe03962580f2a0d4a4d19c4b24b7fef458c3ab8f` |
| `results/attempt09-all-two-k100/screw-states.csv` | `22577859e4793dfefff4bda5aef918265af0e33d6d33167e424f3bfe56780277` |

The executed frame producer SHA-256 is
`85fcbeb6f0c8083fceff48bd6b581402329e2cf1c3422753b0088e1a7fee3372`;
the attachment producer remains
`c2acb48370cecb3964172e8ab82d3c8999e2836e97025e1bde778bc03cf6b9dc`.
Reproduce from the repository root with fresh output directories:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 uv run --offline --no-project --python 3.12 --with numpy==2.2.6 --with scipy==1.15.3 --with osqp==1.0.4 python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/both_corner_frame.py \
  --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/FRESH-FRAME-K100 \
  --service-joints --bottom-corners --all-two-receiver-clearances --bounded-freeplay \
  --panel-withdrawal-stiffness 100

OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 uv run --offline --no-project --python 3.12 --with numpy==2.2.6 --with scipy==1.15.3 --with osqp==1.0.4 python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/panel-attachment/attachment_screen.py \
  --source docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/FRESH-FRAME-K100 \
  --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/panel-attachment/results/FRESH-ATTACHMENT-K100
```

No native/CAD solve, software tests or review loop was run. Reviewed geometry,
hardware policy, formal authority and physical-release flags are unchanged.
