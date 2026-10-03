# Complete left corner resistance register

The assembly is BG001 post/spine → BG003 spine/side/inner block → BG045
inner block/header, with simultaneous timber contact and onward transfers.
This register identifies the current evidence for every component of that
path. No row below is a complete-joint acceptance. Inputs remain the reviewed
92 new attachment axes, twelve original frame-bolt arrangements and 66
Hillman screws; none is altered here.

## Signed conditional demands

[signed-demands.json](signed-demands.json) authenticates all three accepted
exports and retains 168 lateral-plane states: eight planes over seven
increments in A12-rear, A1-rear and K12-rear. Each peak retains the same
state's axial tie and both lateral planes of its physical bolt. The following
vectors are forces on the named first receiver; its other receiver has the
opposite force. Values below omit numerically negligible components.

| Group / bolt / plane | First receiver | Peak case | Signed force `(Fx,Fy,Fz)` N | Resultant N | Same-state tie magnitude N |
| --- | --- | --- | --- | ---: | ---: |
| BG001 post 1 / 35 | spine | A12 rear | `(0,-151.250,-260.999)` | 301.657 | 64.966 |
| BG001 post 2 / 36 | spine | A12 rear | `(0,+213.222,-258.461)` | 335.061 | 18.473 |
| BG003 side 1 / 37 | spine | A12 rear | `(0,-292.424,+385.608)` | 483.948 | 95.967 |
| BG003 side 1 / 38 | side | A1 rear | `(0,-102.215,+8.094)` | 102.535 | 21.794 |
| BG003 side 2 / 39 | spine | A12 rear | `(0,+230.451,-64.212)` | 239.230 | 43.508 |
| BG003 side 2 / 40 | side | A12 rear | `(0,+20.715,-84.481)` | 86.983 | 43.508 |
| BG045 header 1 / 33 | header | A12 rear | `(-89.016,-14.035,0)` | 90.116 | 119.343 |
| BG045 header 2 / 34 | inner block | A1 rear | `(+50.096,-71.224,0)` | 87.077 | 98.442 |

Every listed peak is at load factor 1.0. These are individual source planes,
not independent physical bolts in BG003. They are neither six-case demands
nor conservative bounds on real joint actions. Do not combine the listed
independent peaks into a synthetic simultaneous load state.

## Resistance and transfer table

| Affected component | Available method and input basis | Current result / exact open issue |
| --- | --- | --- |
| BG001 lateral bearing and bolt yield | Reviewed NDS/TR12 individual-bolt helpers, hypothetical smooth 1/4-in shank, specified bearing geometry, SG/Fe/Fyb assumptions in the [A12 comparison](../current-corner-a12-conditional-resistance-screen-attempt01/README.md) | [The three-case paired-resultant screen](../current-bg001-three-case-resultant-reference-attempt01/README.md) now covers both physical bolts in all 21 states (42 rows). It applies receiver-specific grain angles and all six raw yield modes to simultaneous Y/Z resultants. Maximum raw ratio is 0.490816, A12 bolt 2, with its 18.473 N axial tie kept separate. Oblique end-distance adjustment, other adjustments, group/splitting and axial/lateral interaction remain open; this is not an adjusted DCR or a combined joint pass. |
| BG003 continuous bolt and bearing | One continuous biaxial EB bolt, three free receivers, source wrenches once; reviewed isotropic/rotated and [radial-clearance diagnostics](../current-bg003-radial-clearance-diagnostic-attempt01/README.md) | Opposed/unequal source planes do not match symmetric double-shear references. Clearance can increase or decrease internal bending. [A combined anisotropic circular-clearance point-law fixture](../current-bg003-anisotropic-clearance-point-law-fixture-attempt01/README.md) now passes known-force, isotropic, zero-gap, rotation and tangent checks; [Its bounded finite beam application](../current-bg003-anisotropic-clearance-finite-adapter-attempt01/parent-results.md) completed eight A12-rear bolt-1 scenarios with source closure and signed action refinement below 0.276%; clearance concentrates sampled bearing. Inner-block pressure refinement is still 3.49–4.27%, so pressure convergence is not claimed. Grain-dependent physical bearing law and bounded stiffness/engagement, shared two-bolt timber behavior, continuous steel/shank/thread response and combined actions remain open. No plane capacities are summed. |
| BG003 smooth-shank normal stress | [Saved compatible radial-proxy steel screen](../current-bg003-compatible-steel-normal-stress-screen-attempt01/README.md), A12-rear bolt 1, four 32-division scenarios, same-state 95.96739 N tension used once | Conditional full-diameter T/A plus paired sampled bending gives 75.370–178.131 MPa against specified Grade 5 direct yield 634.318 MPa; maximum stress/reference ratio 0.280822. This is a sample-derived proxy, not a physical bound, steel design capacity, or combined-action pass. Threads, shear, torsion and actual material/contact remain open. |
| BG003 necessary receiver bearing | [Signed force/first-moment equilibrium bounds](../current-bg003-bearing-necessary-bound-attempt01/README.md), full modeled receiver lengths and sole-bore transfer | Required projected peak is at least 4.8292 MPa in spine, 1.9855 MPa in side and 0.4385 MPa in inner block. These lower bounds cannot establish a pass; an actual compatible peak/upper bound and appropriate embedment resistance remain missing. |
| BG045 lateral bearing and bolt yield | Existing angle-dependent NDS/TR12 individual-bolt reference and Ceg scenario in [two-case screen](../current-corner-bg045-two-case-wood-mode-screen-attempt01/README.md) | The conditional component comparison is reused. Adjusted mixed-action/group resistance, physical bearing/clearance and bolt axial/lateral interaction remain open; favorable individual ratios do not waive detailing/splitting. |
| BG045 edge/end/row detailing | [Signed 2024 NDS detailing and splitting review](../current-bg045-edge-splitting-applicability-attempt02/README.md), proposed grain and model envelopes | A1 axis 2 has a 20 versus 25.4 mm conditional minus-Y loaded-edge exception, short 5.4 mm. [Finished-STEP queries](../current-bg045-finished-profile-edge-attempt01/README.md) confirm the same 20 mm block minus-Y distance at all five tested shaft-overlap stations; all 80 profile queries match the previous rectangular distances. This closes the sampled model-profile discrepancy only, without continuous-span proof or a loaded-edge assignment. Oblique face selection and mixed-grain header detailing remain unresolved. The 93.35 mm pair pitch exceeds numeric comparators but is not an applicable row check: its bolt line is not aligned with the accepted group loads. The axis-2-only proposal reaches exactly 4D without tolerance margin; no move is approved or made. |
| BG001/BG003 spine and inner-block sections | [252 signed one-sided cuts](../current-corner-conditional-section-demands-attempt01/README.md), additive [net-section correction/normal traction](../current-corner-net-section-normal-traction-attempt01/README.md) | Signed N/V/M and source-discrete load jumps are available. Common affine strain across disconnected ligaments is a proxy. The [grain-aligned material reference screen](../current-corner-net-section-material-reference-attempt01/README.md) covers all 252 records: maximum raw Ft/Fc ratios are 0.107877/0.032470 for the spine and 0.010454/0.004424 for the inner block. These are unadjusted reference comparisons under declared material hypotheses. Applicable adjusted material strengths, local concentration/transfer, shear/torsion, net/row tear-out and splitting resistance are missing. |
| BG045 header section/onward transfer | [Complete source-bound header cuts](../current-bg045-header-transfer-section-demands-attempt01/README.md): 160 owner actions and 212 physical load nodes per state, 84 independently reconstructed segment wrenches | Three-case header closures and BG045 transfer jumps pass. No isolated bolt vector or member resultant is labeled a local tension-perpendicular splitting demand. A supported local splitting mechanism/resistance remains missing. |
| All groups: splitting and shared timber/group behavior | Existing geometry/spacing records and NDS hazard provisions; no adopted general splitting equation for this topology | Bind a mechanism applicable to the actual grain, receiver topology, edge/end distances and simultaneous bolt/contact actions. Net-section or Appendix E row tear-out arithmetic is not a cross-grain splitting check. Missing evidence is not physical failure. |
| Six outer-seat ties / twelve seats | [Three-case axial/seat register](../current-corner-three-case-axial-seat-register-attempt01/README.md), existing A12/A1 component screens and [washer geometry](../current-corner-washer-seat-screen-attempt01/README.md) | All 126 signed ties are tension; 252 seat states are covered. Maximum tie is 119.343 N and full-annulus average 0.535828 MPa, BG045 header axis 1 in A12 rear. CAD annulus is 222.7262 mm². DF-L No. 2 Fc⊥ component references apply only to explicitly matching transverse seats; block elastic properties do not assign block strength and BG045 block seats load along proposed grain. |
| Bolt tension, thread and nut engagement | Existing conditional Grade 5 tensile first-yield reference; original partially threaded policy and candidate hardware leads | [The hardware/material packet](../../hardware-material-specification-2026-09-30/README.md) specifies conditional bolt-body/full-thread/nut profiles and direct steel references. Long BG003 product fit, dowel-bending strength adoption and combined tension/shear/bending/stripping/fracture methods remain open. First yield is not design resistance; delivered conformance remains separate. |
| Washer steel and local wood seat | Existing candidate dimensions, ideal annulus pressure conversion and limited conditional wood-bearing comparisons | [The three-case catalog-area wood compression screen](../current-corner-catalog-washer-wood-compression-screen-attempt01/README.md) covers all 252 seats. Under its full sound USS-annulus and conditional material scenario, maximum transverse stress/reference ratio is 0.129640; the BG045 parallel-grain block comparison is 0.060019 and has no adopted local bearing method. [Finished-CAD wood support](../current-corner-washer-wood-support-attempt01/README.md) now verifies all twelve seats against both catalog annulus bounds: 100% support, no modeled plane gap or tilt, with the same 252 conditional seat averages. This closes the modeled wood support-area dependency only. Head/nut-to-washer metal footprint, washer bending/spreading/pull-through, physical seating and applicable resistance remain unbound. No preload/friction is credited. |
| Seven neighboring timber interfaces | [588 contact states and 147 signed pair wrenches](../current-corner-timber-contact-pressure-screen-attempt01/README.md), plus [conditional grain applicability](../current-corner-timber-contact-grain-applicability-attempt01/README.md) | Of 14 receiver/interface combinations, ten are transverse to proposed grain, three parallel and one oblique. Maximum transverse cell-average/reference ratio is 0.119143, header/post on the header in A1 rear, against conditional DF-L No. 2 Fc⊥625 psi with no Cb credit. Parallel/oblique local-bearing treatment remains unbound. Cell average is not a local peak; actual support/distribution and complete bearing resistance remain open. |
| Complete corner boundary and onward path | [Five-body assembly reconstruction](../current-corner-whole-assembly-transfer-attempt01/README.md), all simultaneous native export interfaces | Internal actions cancel in all 21 states; 62 signed boundary ports retain incoming/onward actions. Net boundary gravity balance is not an individual group demand. Panel work is limited to specifically affected receiver/transfer dependencies. |
| Original LEG/FLOOR-RUNNER interfaces | Existing resistance/geometry evidence, retained as the original twelve arrangements | Reuse unchanged calculations. Reopen only an identified changed demand, receiver, geometry or hardware item; no blanket qualification campaign or historical-case pass transfer. |
| Full frame/support envelope | Three authenticated rear exports; [six-case necessary normal-resultant screen](../current-six-case-floor-global-necessary-statics-attempt01/README.md); passing prescribed native reference coupons | Forward/left/right remain unusable. [The initial rigid-body rank audit](../current-frame-gravity-rank-readiness-attempt01/README.md) confirms additional all-open mechanisms; it is not a full tangent/state check. [The source-bound elastic reduction](../current-frame-connector-compliance-attempt04/README.md) now passes all 50 bodies and full connector reciprocity/positivity checks. Its H/D/e/W maps retain separate gravity/climber loads and raw body wrenches. The initial zero-load touching/reference contract is source-bound. The first coupled gravity-direction selector reached its 45 s limit with no feasible state found, so admissibility/uniqueness and actual branch mechanisms remain unresolved; it is not an infeasibility proof. [A separate 100-floor-binary convex gravity selector](../current-a12-gravity-direction-convex-selector-attempt01/README.md) also stopped at its 45 s root-node budget with zero feasible states and no force output; neither stopped selector is an infeasibility proof. [The prescribed A12 known-answer QP](../current-a12-fixed-episode-dual-qp-known-answer-attempt02/README.md) reached solved in 0.652 s with adaptive residual balancing, but failed its numerical sign and original DAT comparison gates; no candidate forces are adopted. Absolute-only precision tightening then failed its tiny preflight, so no further frame run was made. Full-frame coupled contact/history and compatible gravity remain open. Native coupon passes and inside-hull centers of pressure do not qualify these cases or the physical floor. |

Conditional strength and hardware scenarios can be investigated before stock
inspection. Their assumptions must be explicit and source-bound; actual
conformance remains unobserved. None of the missing inputs above adds a
blanket external sign-off prerequisite or authorizes physical work.

Reproduce the signed demand register from the repository root:

```sh
OPENBLAS_NUM_THREADS=1 .venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-corner-complete-resistance-register-attempt01/produce.py --verify
```

The next useful acceptance evidence is compatible gravity plus one currently
unusable frame case through the unchanged contact/MPC/body/global gates,
alongside closure of the named corner resistance rows. Reserve further
coupons/contact studies for a specific dependency in those deliverables.

## Independent support/corner guidance received October 1

The parent read and reproduced the [independent packet](../../support-corner-review-2026-09-30/README.md)
with its read-only `diagnose.py --verify`: `PASS_BYTE_IDENTICAL_SMALL_MODEL_DIAGNOSTICS`.
Its 18 isotropic zero-gap BG003 scenarios establish compatible continuous-bolt
responses, including nonzero signed middle-cut actions, without establishing
physical bearing or strength. The later anisotropic/circular-clearance proxy
above addresses additional compatibility mechanisms conditionally; it still
does not supply calibrated physical bearing, a conservative upper bound,
shared two-bolt splitting resistance or a complete mixed-action check.
Further proxy parameter sweeps are not the next deliverable.

The BG045 20 mm versus conditional 25.4 mm comparison stays an explicit
5.4 mm detailing exception. Finished-profile sampling confirms the modeled
distance; it does not settle the applicable edge/splitting interpretation.
The packet's both-Y-face axis band is a conservative proposal envelope,
not a universal NDS rule or authorization to move the reviewed axes.

For unresolved support cases, distinguish the historical proportional
gravity-plus-climber episode with fixed zero tangent references from a new
gravity-settle then climber-ramp scenario with contact-event references.
All gravity sources, coupled normal/tangent states and strict original
validation gates must remain. A staged scenario must stop on no admissible
state, unresolved multiple states, cycles or exhausted budget. No guessed
mask retries or rejected forces are adopted. Numerical reproduction of the
old A12 episode is only a bounded method check, not proof of this new history.

The corner deliverable remains the complete BG001/BG003/BG045 path from
the three authenticated rear exports: signed sections, receiver bearing,
continuous bolt behavior, splitting, washers and onward transfer. The
twelve original leg/runner resistance arrangements remain separate from
the 92 new block axes; only concrete changed inputs reopen their checks.

The parent subsequently replayed the older BG001 A12 signed-end-distance
screen. Its arithmetic passes, but the [source-attribution audit](../current-bg001-end-distance-source-audit-2026-10-01.md)
finds that the pinned 2024 Chapter 12 extract does not contain the cited
commentary interpolation passage. The passage is verified in the official
2018 Commentary. Until exact current-edition applicability is bound, retain
the A12 factor 0.703901 and maximum geometry-only ratio 0.69728 as provisional
historical-method sensitivities. Signed source actions and measured geometry
remain available; this is a method-evidence gap, not physical joint failure.

The parent has now replayed the [42-row BG001 three-case historical sensitivity](../current-corner-bg001-signed-end-distance-three-case-attempt01/README.md).
It retains all 21 simultaneous states and separate axial ties. Full-load
group-min historical factors are 0.725371 (A1), 0.703901 (A12) and 0.963117
(K12); corresponding bolt-2 geometry-only comparison ratios are 0.30171,
0.69728 and 0.12437. All remain sensitivities, with current-edition
interpolation and oblique group treatment unbound; they are not adjusted
resistance or complete joint passes.

The [parent direct A12 refinement](../current-a12-fixed-active-kkt-parent-attempt01/results.md)
completed in 4.192 seconds under frozen inputs and serialized controls.
Its 2,649-order KKT rank, fixed active-set, all ten physical checks and all
q/rigid-coordinate DAT intervals pass. Original force intervals still fail
25 rows, so known-answer reproduction remains stopped and all forces remain
unadopted. No new floor mask/history, native solve or fourth case follows.


Parent stable replay of the [three-case BG001 Appendix E component extension](../current-bg001-appendix-e-parallel-row-three-case-attempt01/README.md)
passes 21 states and 42 paired bolt actions. Maximum base-reference comparisons
are 0.21626 for the post parallel row and 0.02601 for the candidate spine
net section. Cross-grain actions and axial ties remain explicit; adjusted
resistance, mixed-action applicability and splitting are not settled.

The [coordinate-translation diagnostic](../current-springa-ghost-coordinate-translation-diagnostic-attempt01/README.md)
rejects translation as a demonstrated reproduction remedy for the examined
A12 row. The [raw-H tiny fixture](../current-fixed-active-raw-H-linear-fixture-attempt01/README.md)
passes parent replay and supports preparing one bounded original-operator
comparison, without changing the fixed branch or source gates. No additional
force export is authenticated by these diagnostics.


The [actual raw-H A12 comparison](../current-a12-fixed-active-raw-H-comparison-attempt01/results.md)
completed under frozen controls. All physical and fixed-branch checks pass;
27 original force intervals still fail, while q and rigid-coordinate
intervals pass. Raw-H improves source-law consistency but does not clear
reproduction. Saved full vectors and row identities support a bounded
diagnosis; no force export, fourth case or complete corner pass is adopted.


Parent replay of the [BG045 bounded symmetric proposal](../current-bg045-symmetric-inward-detail-proposal-attempt01/README.md)
passes byte identity. Conditional opposite-face clearance of 25.4 mm can be reached
by inward shifts of 5.4 mm each, reducing pitch from 93.35 to 82.55 mm but reducing the
neighboring orthogonal-bore modeled web from 7.453 to 2.053 mm. Current four washer
annuli have exact CAD support; moved-seat margins are rectangular/circular-loop
arithmetic only, not relocated support proof. Preserving pitch and adding the
same conditional clearances requires a 144.15 mm block-face envelope rather
than 133.35 mm, with centers unchanged. Neither option is adopted, verified
on moved CAD, or a splitting/resistance solution. Existing geometry remains
reviewed and unchanged; source edge applicability and complete mixed-action
checks remain open.


Parent replay of the [BG003 anisotropic/clearance component references](../current-bg003-anisotropic-clearance-component-reference-screen-attempt01/README.md)
passes all eight saved scenarios, 24 signed receiver sample/reference rows
and eight paired signed stress records. At 32 divisions, maximum sampled
p/d-to-directional Fe reference is 0.52215 (spine, density hypothesis 550 kg/m³,
gap 0.575 mm). Maximum sampled smooth-section absolute normal stress is
180.698 MPa, ratio 0.28487 to conditional Grade 5 direct yield 92 ksi, with the
same 95.96739 N physical tension included once. These extend the completed
proxy evidence with directional material comparisons; they are not adjusted
capacities, design DCRs or conservative physical bounds. Earlier isotropic
radial stiffness scenarios are separate and retain their own results.
Uncalibrated bearing, sampled-pressure refinement, delivered shank/thread
sections, shared receiver splitting, washers and mixed-action interaction
remain open. No further beam/contact scenarios were run.
