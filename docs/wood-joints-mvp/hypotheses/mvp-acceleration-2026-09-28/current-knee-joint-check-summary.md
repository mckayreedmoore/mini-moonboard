# Current left outer knee: calculation and transfer summary

This report concerns the reviewed wood-joint development revision
`led-clearance-2x6-runner-seated-blocks-v1`. It assembles current-joint results
under the owner's bolt/block priority. The selected angle-frame baseline and
its evidence remain separate. No accepted six-case knee wrench exists yet.

## Original bolts and replacement block axes remain separate

The inventory contains **92 introduced block-attachment axes** replacing the
former ML24Z/SDS structural duties, plus **12 separate retained original axes**:
four leg-to-side-member bolts and eight floor-runner front/rear bolts. BG001,
BG003 and BG045 are six of the introduced axes in the left outer corner-block
assembly. They are not the original leg or floor-runner arrangements.

Reuse the original leg/runner calculation methods and unchanged resistance,
hardware and geometry evidence from the [baseline master plan](../../../floor-runner-mvp-master-plan.md)
and [baseline evidence ledger](../../../floor-runner-mvp-completion-ledger.md).
No general retained-bolt qualification campaign is scheduled. Reopen only an
identified change in geometry, receiver, hardware or calculated demand,
state that difference first, and preserve the unaffected checks. Changed
frame stiffness can change demands; prior case passes are not automatically
transferred. Historical inventory text saying a retained-bolt recheck is
required does not override this owner-directed, issue-specific scope.

## Physical transfer arrangement

The nominal new-bolt chain connects the post to the exterior spine through BG001. The spine, inclined
base side and inner frame block share two continuous BG003 bolts. The inner
block connects onward to the header through BG045. These connections can
carry concurrent actions; BG003 is one three-member stack, not three
independent two-member groups. The current sources identify receiver order
and geometry, but do not determine the simultaneous action split. The chain
is not the only modeled transfer route: direct member bearing and the
runner-seated spine provide parallel paths, described below. Do not assign
the whole corner wrench to BG001, BG003 or BG045 alone.

| Current group | Physical receivers | Usable calculation | Exact limitation |
| --- | --- | --- | --- |
| BG001, `knee_outer_left_post_1/2` | Post and exterior spine | Prescribed lateral wrench maps to two bolt actions; 42.05 mm pitch gives opposite 23.781 N per bolt per N·m of Mx. Individual lateral references are 567.848 N in Y and 796.262 N in Z under the recorded assumptions. | No actual case wrench, adjusted group resistance, splitting or combined-action acceptance. |
| BG003, `knee_outer_left_side_1/2` | Exterior spine, base side, inner block | Ordered modeled bearing lengths are 38.1, 88.9 and 88.9 mm. NDS §12.3.5.4 provides a shorter-side-length rule for a conditional double-shear screen. | Actual outer-member actions are not known to be equal; continuous-bolt and complete-joint behavior must not be replaced by summed pair capacities. |
| BG045, `knee_outer_left_inner_header_1/2` | Inner block and header | Eligible main-member end-grain lateral scenarios give 401.636 N along header grain and 380.458 N across it, with Ceg only. | Role applicability, signed case actions, other adjustments, group effects, splitting and axial/hardware checks remain open. |

## Current bolt-group and three-member reference results

The [BG001 group-factor packet](current-knee-post-group-factor-attempt01/README.md)
binds the existing NDS helper to the current straight two-bolt Z row. Both
supported material-ring assignments have matched conditional EA of 13.2
million lbf per member and return Cg=1.0. Combining only Cg and the recorded
Cdelta branch with the single-bolt Z reference gives 455.007 N toward the
short ends and 796.262 N for the reverse branch. These are limited reference
scalings, not an adjusted resistance or group capacity. The two ring cases
have no longitudinal EA variation; no unsupported material perturbation is
presented as source evidence.

The [BG003 three-member packet](current-knee-three-member-transfer-attempt01/README.md)
uses the existing double-shear helper and NDS §12.3.5.4's shorter outer
bearing length. Conditional matched-outer-property, equal-outer-action
scenarios give one-physical-bolt references of 1,396.479 N for Z loading,
1,486.407 N at the grain bisector, and 1,160.581 N for Y loading. Parent
reproduction matches all four modes and an independent mode-IV formula.
These three directions are not an exhaustive envelope. Neither two-bolt
sharing nor the actual simultaneous side-member actions are known; no
pairwise or group capacity addition is allowed.

## BG001 geometry and axial transfer

The finished-profile query finds square terminal grain faces at the three
sampled receiver-depth stations. The shortest post end is 25.40 mm (4D) and
the shortest spine end is 31.75 mm (5D). For the recorded opposed softwood
tension-toward-end branch, the preliminary end factors are 4/7 and 5/7; the
NDS minimum-factor rule would govern all BG001 fasteners at 4/7. The reversed
tension branch has end factor 1.0. This is an end-distance result, not an
overall connection factor or a failure finding. Discrete rays do not prove a
continuous through-thickness minimum. Internal bores remain relevant to
splitting and net-section checks.

The actual post/spine contact face supplies an axial moment arm. With zero
net axial force, ideal equilibrium requires at least 13.550/14.826 N total
ties per N·m for positive/negative My, and 10.499/26.247 N for Mz. These bounds
allow compression resultants anywhere in the face's convex hull and place no
finite pressure limit on the timber. They establish neither a physical
pressure distribution nor washer resistance. A self-equilibrated bolt-tension
and contact-compression mode makes upper tie actions unbounded unless
compatibility, preload and pressure/stiffness behavior are specified.

The shaft-centroid datum is `(-1208.151, -137.600, 192.475) mm`. At the
projected face datum, `(-1219.200, -137.600, 192.475) mm`, moment translation
adds `-11.049 Vz` to My and `+11.049 Vy` to Mz. Preserve this translation
when combining the lateral and axial calculation inputs.

## Evidence and stops

- [BG001 lateral map and reference scenarios](current-knee-post-conditional-bolt-screen-attempt01/README.md): source-pinned reproduction and parent mixed-wrench cross-product check passed.
- [Finished BG001 profile query](current-knee-finished-profile-attempt01/README.md): parent replay reproduced all 48 rays and checked producer/output/input pins.
- [Axial/contact bounds](current-knee-axial-contact-bounds-attempt01/README.md): six unit witnesses and the self-equilibrated mode close; parent independently checked a mixed signed wrench.
- [BG045 end-grain screen](current-knee-header-endgrain-screen-attempt01/README.md): six-mode helper calculation and independent mode-IV check passed; parent checked the pinned primary-source provisions directly.
- [Three-member receiver order](bolt-groups/three-member-stack-order-attempt01/README.md): preserves the two physical BG003 bolts and ordered receiver intervals.
- [Finished BG003 profiles](current-knee-three-member-profile-attempt01/README.md): parent replay reproduced all 72 rays; square block profiles, oblique base-side end and the additional inner-block bores remain distinct. These are geometry inputs for local wood checks, not proof of splitting resistance.

For each of the six source cases, the missing demand input is the signed
six-component action on each connected member at an explicit cut datum,
including equal-and-opposite closure and simultaneous BG001/BG003/BG045
actions. Upstream panel resultants are not these actions. Conditional imposed
wrenches remain useful for mechanism and reference calculations; complete
panel qualification is not a prerequisite for investigating them.

Resistance still needs applicable group/geometry/service factors, local
wood limit states, axial washers/seats, bolt/nut tensile and engagement basis,
and complete transfer. Delivered identities are not observed. Stop an
affected check at the precise absent input; do not invent a product capacity,
change reviewed geometry, or transfer a historical candidate pass.

## Existing conditional compatibility inputs

The [existing compatibility reuse map](current-corner-existing-compatibility-reuse.md)
records how the later frozen C11 model already implements a tension-only outer-seat tie
for each of these six physical bolts. Earlier preparation statements that
no axial law exists describe the earlier preparation state. Parent extraction
from the frozen model confirms paired stiffnesses of 4,670.054 N/mm for
BG001, 4,234.008 N/mm for BG003 and 3,207.383 N/mm for BG045. Each lateral
shear-plane component has conditional stiffness 3,086.746 N/mm. BG003 has
two lateral planes per bolt but only one axial tie spanning spine to inner
block; it does not introduce a middle-member washer or independent axial tie.

These are existing model inputs, not measured connection properties or
resistances. The axial approximation combines a nominal steel shaft and two
orthotropic timber bearing columns in series, using modeled washer area.
It does not establish washer bending, installed preload, delivered shank or
thread engagement, crushing behavior, or the actual coupled three-member
lateral response. The contact law and active contact pattern also require
applicability checks. Reuse the implemented inputs for a bounded sensitivity
assessment rather than claiming that an axial model must be developed anew.
The C11 response failed contact-sign checks: neither its forces nor its
active states are accepted corner demands. Recovering its source-bound input
coefficients does not rehabilitate that response or authorize another run.

## Current outer washer-seat calculation

The [six-axis washer-seat packet](current-corner-washer-seat-screen-attempt01/README.md)
passes parent source/arithmetic verification and independent seat-force
closure, with maximum residual 1.11e-16 N.
For all six new corner axes, the source-bound modeled outer washer annulus
has area 222.726212 mm² and thickness 1.651 mm. Under uniform full-annulus
sound-wood support, each outer seat sees average pressure
`p = 0.0044898173 T MPa`, where T is that physical bolt's axial tension in N.
This is a usable demand conversion, not an actual pressure distribution.
The two outer seats each see the bolt tension; their resistances must not be
added. The middle member of BG003 has no additional washer-seat tie.

The conditional DF-L No. 2 transverse bearing reference Fc-perpendicular of
625 psi gives 959.777 N per eligible fully supported annulus before other
applicable conditions. It is only a timber bearing comparison for the
source-bound post/header transverse seats, not a selected washer rating or
complete axial capacity. The BG045 inner-block seat is parallel to its
proposed grain: this transverse reference does not apply there. Candidate
block strength properties, actual sound seat support and washer metal bending
remain distinct missing inputs. Neither a modeled annulus nor a dimensional
product lead proves delivered fit, flatness, yield strength or bearing.

## Local wood section inputs

The [local wood packet](current-corner-local-wood-screen-attempt01/README.md)
reproduces these geometry inputs and source hashes; parent verification passed.
Under the rectangular-section and cylindrical-bore idealization, the exterior
spine's gross Z-normal area is 5,322.570 mm². At any one of its four separate
transverse bore center planes, subtracting the 38.1 × 7.5 mm strip leaves
5,036.820 mm². Do not subtract all four bores at a single plane. The inner
block's corresponding gross area is 88.9 × 133.35 = 11,854.815 mm². At either
BG003 bore center plane, its transverse strip and the two separate BG045
longitudinal circles leave 11,099.708 mm²; away from the transverse bores,
the two longitudinal circles alone leave 11,766.458 mm². The sourced bore
centers keep these strips and circles disjoint at those planes.

These are candidate net-section inputs, not section-capacity or splitting
results. A uniform imposed Z-axis tensile force gives nominal average stress
`N / A_net`; the spine and inner block at the BG003 bore plane give
0.000198538 and 0.0000900925 MPa per N respectively. Actual bending, local
concentration and the complete cut geometry require separate treatment.
Current signed axial/member moments and matched final-piece adjusted timber
strength remain missing. A sourced splitting equation is also not evidence
that its illustrated arrangement applies to this three-member corner or
the end-grain-axis header connection. No splitting acceptance is inferred
from end/edge-distance compliance alone.

This report grants no new mesh/native-run authority and changes no criterion,
fabrication, candidate selection or climbing disposition.

## Parallel bearing routes that a complete corner cut must include

Parent extraction from the pinned C11 input, excluding response forces and
active states, finds seven internal contact pairs among post, spine, side,
inner block and header. Each pair has four sampled contact cells. The
recorded cell areas sum to:

| Member pair | Modeled contact area (mm²) |
| --- | ---: |
| Header / outer post | 5,322.570 |
| Header / side | 11,930.617 |
| Header / inner block | 11,766.458 |
| Header / spine | 5,080.635 |
| Post / spine | 13,139.963 |
| Side / inner block | 15,653.565 |
| Side / spine | 15,653.565 |

The spine also contacts the left floor runner. These are source-bound
potential bearing interfaces, not proven active supports or qualified
capacities. Header/post, header/side and header/spine can share or bypass the
nominal bolt chain when their compression signs and compatibility permit.
Runner/spine bearing is a direct onward route that must not be omitted merely
because BG045 connects the block to the header. Therefore complete corner
equilibrium must sum the simultaneous bolt-plane actions, outer-seat ties,
bearing cells and applicable boundary/member-cut actions at explicit datums.
Recover each member separately as well as the aggregate corner; internal
forces cancel in an aggregate cut and cannot establish local joint demand.
The original leg/runner connectors can be identified as boundary carriers
without reopening their unchanged resistance calculations.

The [reproducible interface recovery map](current-corner-interface-recovery-map-attempt01/README.md)
now records all seven internal pairs, eight corner lateral planes, six
outer-seat ties and the full five-member boundary-carrier inventory. Parent
verification checks each physical corner axis separately and all four paired
post/floor normal/tangent ownership rows. Across these five members, it
records 36 contact pairs / 236 cells; the 29 boundary pairs are bookkeeping,
not a new qualification campaign. No response forces or active branch states
are read. Carrier coverage is complete for this pinned abstraction; valid
simultaneous signed demands and physical applicability remain outstanding.

## Conditional contact-sharing result and resolution dependency

The [bounded BG001 compatibility calculation](current-post-spine-conditional-sharing-attempt01/README.md)
uses the existing two axial tie stiffnesses and four contact-centroid cells,
with rigid local members and imposed interface moments. It inherits no C11
force or active state. Per +/−1 N·m My it gives total tie actions 22.622 /
23.489 N; per +/−1 N·m Mz it gives 16.152 / 207.169 N. Independent scalar
known answers and parent 3D force/moment closure pass. These are conditional
mechanism actions, not six-case demands or assembly capacity.

The reverse-Mz value is about 7.9 times the unrestricted-footprint necessary
bound because the four contact centroids provide only a 4.827 mm short-side
lever arm. This supplies a concrete contact-resolution concern before local
ties are interpreted as design actions. Neither sampled-cell pressure nor
the earlier convex-hull bound is an actual distributed-pressure solution.
A pure positive Fx probe stops on different compatible displacement states;
no result is adopted for that probe. Full corner sharing, pressure resolution,
member flexure and simultaneous boundary actions remain required.

The subsequent [pressure-resolution experiment](current-post-spine-pressure-resolution-attempt01/README.md)
holds that local geometry, ties and penalty fixed while refining quadrature
from 16² to 512² and excluding the two modeled bores. Total tie actions at
512² are 16.715 / 18.103 N for +/−My and 10.980 / 28.119 N for +/−Mz,
per imposed 1 N·m. Last-grid changes are below 0.009% for these probes.
Thus the 207 N reverse-Mz value is strongly affected by coarse sampling;
it is not a resolution-independent bolt demand or a physical failure.
Source reproduction, independent-start agreement and force/moment closure
pass. The normal penalty law and rigid-member approximation remain
conditional; this does not validate other corner interfaces or global loads.

The subsequent [existing-compliance scenario sweep](current-post-spine-compliance-sensitivity-attempt01/README.md)
reuses 24 paired ring/depth/steel-modulus scenarios with 256² fixed quadrature.
Across effective tie stiffnesses 1,780.926–8,869.699 N/mm, total tie actions per
imposed N·m remain 16.608–16.785 N for +My, 18.058–18.107 N for −My,
10.800–11.155 N for +Mz and 27.429–28.781 N for −Mz. All 96 prescribed probes
close and reproduce. These named scenarios are not measured or statistical
property bounds. This reinforces the coarse-sampling diagnosis in the local
model while leaving actual simultaneous complete-corner demands outstanding.

## Coupled five-member equilibrium result

The [complete corner operator](current-corner-equilibrium-operator-attempt01/README.md)
assembles 30 body force/moment rows and all 50 internal carrier components.
Bolts alone have rank 18, leaving six relative rigid-member motion modes
after the six common rigid motions are removed. Adding all potential bearing
cells raises algebraic rank to 24. This demonstrates the importance of
bearing/contact to this complete corner abstraction; it does not prove those
unilateral contacts engage or that the actual joint is stable.

The complete operator has 26 algebraic force-sharing directions, so balance
alone cannot select the simultaneous bolt/contact actions. Global internal
wrench cancellation and source reproduction pass. Compatible deformation,
unilateral signs and boundary actions remain essential. These rank/nullspace
results do not create capacity, preload or an accepted frame demand.

The [coupled conditional sharing packet](current-corner-conditional-sharing-attempt01/README.md)
now calculates all three groups and seven bearing pairs together under 48
balanced imposed local actions. A constrained complementary-energy method
closes all 48 probes with the original spring-law consistency, unilateral
signs, two-start force agreement and independent five-member physical-wrench
recovery. The former negative-X spine exception is resolved by a compatible
displacement witness without changing its forces: each BG001 tie carries
0.5 N under that unit probe. Its displacements are nonunique, explicitly
recorded; force closure does not prove stability. Independent Luna/max
sign/duality/gauge and conditional-force criterion reviews are complete.
The fixed coarse contacts, rigid members and zero-clearance/preload assumptions
remain explicit. These are reproducible imposed-action responses, not the
missing six-case frame demands. No criterion changes disposition.

## Minimum inputs for an actual corner evaluation

1. For each source load case, a simultaneous, closed signed boundary wrench
   on each of the five corner bodies, referenced to recorded cut datums and
   including onward carriers. A resultant at the panel is not this input.
   The source-bound outward map includes the spine/runner bearing route;
   it must not disappear when checking only the three new bolt groups.
2. An applicable complete-corner compatibility model: member flexure and
   contact footprint/compliance, clearance/preload policy, and the continuous
   three-member BG003 shaft. The fixed coarse rigid-body unit model above is
   a bounded mechanism reference, not evidence for those physical choices.
3. Matched material/hardware resistance inputs: block species/grade/grain
   and applicable adjusted timber strengths, splitting applicability,
   washer metal/seat support, and bolt/nut tensile/shank/engagement basis.
   Existing NDS helpers, geometry, lateral references and washer pressure
   conversions are reused; absent product resistance is not filled by a
   historical pass.

These dependencies apply to the new corner-block path. Original LEG and
FLOOR-RUNNER resistance work remains reusable; only a concretely changed
receiver, geometry, hardware or calculated demand reopens an affected check.
No blanket retained-bolt or panel qualification campaign is added.


## Corner-demand dependency: coupled support rule and exact limitation

The [bounded structural-coupling fixture](conditional-floor-structural-coupling-fixture-attempt01/README.md)
now tests normal/tangent coupling, ideal stick only while bearing, release,
and discrete reference reset. Four hand-answer stages each have exactly one
admissible mask. Standard-library KKT and independent constrained-coordinate
elimination agree on all 16 candidate states, with selected force-balance
residual below 3.56e-15 N. This closes that small-fixture coupling question,
not the full-frame support gate or any corner-demand check.

The [exact-rational applicability counterexample](conditional-floor-structural-coupling-fixture-attempt01/parent-reference-counterexample.md)
also proves that this fixed preceding-open-state reference rule does not
ensure existence or uniqueness under arbitrary coupled loads. One cell with
fixture carrier `[[20,5],[5,100]] N/mm`, normal penalty 100 N/mm and reference
x=0 has no admissible static branch under `(Hx,Pz)=(4,+0.5) N`: its open
branch penetrates; its stuck branch requires negative normal force. The
sign-reversed load has two admissible branches. These are method examples,
not source-case loads or physical failure findings. The corner's convex
force-energy argument does not prove uniqueness for this disjunctive floor law.

Parent source-pin extraction finds 100 frozen floor-normal cells, each with
a paired old tangent ownership row: 38 per runner and four per remaining
six supported posts/legs. Exhaustive normal-mask enumeration has up to
`2^100` candidates and is not a practical frame selector. No C11 force or
finite-tangent acceptance transfers.

The precise remaining floor dependency is an applicable reference-capture
and loading-history/state-selection treatment for the coupled frame, with
bounded failure behavior; neither four passing stages nor selecting one
admissible mask supplies it. Do not fix it by accepting negative normal
forces, retaining tangent restraint at zero bearing, or changing stiffness
until a branch passes. No frame/native run, geometry, criterion or original
LEG/FLOOR-RUNNER resistance change occurred. Signed actual-case corner
boundary forces and applicable member/hardware checks remain outstanding.


## Six-case aggregate support feasibility: all-bearing witnesses exist

The [global floor-wrench screen](current-global-floor-wrench-screen-attempt01/README.md)
reconstructs all 778 gravity sources and the six external force wrenches,
using frozen input floor coordinates. For all six cases, both without the
accessory diagnostic allowance and with the recorded 25 kg mean placement,
aggregate equilibrium admits strictly positive normal forces at all 100
floor cells. Full six-component force/moment witnesses close independently
within 1.52e-11 N / 1.18e-8 N·mm. Source reconstruction, known-answer square
support fixtures and reproduction pass. These are algebraic witnesses, not
compatible actual reactions, a tipping pass or signed corner demands.

Global balance therefore does not force lift-off in these scenarios. This
supports testing an all-bearing branch for compatibility; it does not prove
that branch, remove the fixed-reference counterexamples, or close global
readiness. The next response check must verify actual normal signs and full
body closure with the supported frame/receiver/member mappings. No native
run, floor-law change, geometry or old-bolt resistance work is authorized by
this screen. Corner-block demand remains the primary missing result.

A targeted official-documentation search found Abaqus rough contact, together
with reopening limitations, and Code_Aster's Coulomb friction description.
Neither provides a verified immediate substitution for the present floor
predicate/reference policy. Details and links are in the packet; no new
solver-selection campaign or unsupported friction value follows.


## September 29: corner priority and bounded native method result

BG001 (post/exterior spine), BG003 (spine/side/inner block) and BG045
(inner block/header) are the left outer corner-block assembly. The primary
engineering deliverable remains its complete transfer path, including member
bearing/contact, physical bolt groups, splitting/net section, washers and
onward transfer. The 92 introduced block-attachment axes replacing old
ML24Z/SDS duties are separate from the twelve retained original LEG and
FLOOR-RUNNER bolt arrangements. Reuse unchanged original resistance and
geometry calculations; reopen an original arrangement only after naming its
specific changed geometry, receiver, hardware or calculated demand.

The independently reviewed, frozen nonlinear SPRING2 known-answer coupon
used its single serialized 60-second launch budget. Docker and the pinned
2.23 binary ran successfully; the solver returned 201 after exhausting
increment cuts at the zero crossing in step 2. Step 1 attained the known
answer: +10 N applied, +0.1 mm displacement, +10 N positive internal spring
force, zero negative spring force, and -10 N ground reaction. All 17 printed
converged increments before failure obey the intended table force law within
8.9e-16 N (printed precision); the negative branch and reversal did not
complete. This is partial method evidence, not a method pass. The assessor
correctly rejects the run. No automatic retry, new full-frame launch,
criterion change or geometry change follows.

See [the bounded coupon packet](nonlinear-spring2-known-answer-attempt01/README.md)
and its partial-observations.json. Actual six-case signed boundary actions
for this corner remain missing; aggregate support witnesses and local unit
probes cannot substitute for compatible frame demands. Remaining corner
checks also need applicable member/seat/washer and delivered bolt compatibility
evidence at the resulting combined actions. Existing evidence is reused where
applicable; no general LEG/FLOOR-RUNNER qualification campaign is started.


## Source-bound carrier law inventory for the corner-demand dependency

The [input-only law inventory](current-native-carrier-law-inventory-attempt01/README.md)
now binds all 1,840 scalar carriers to the frozen frame input and their
physical owners: 1,122 compression rows, 170 tension rows, 348 bilateral
lateral components and 200 conditional all-bearing floor tangent components.
The physical bolt-axis partition is checked explicitly: 92 new block axes
and 12 original LEG/FLOOR-RUNNER axes are disjoint, and their union is exactly
the 104 outer-seat axial ties. The four extra new-bolt shear planes remain
planes on existing physical bolts, not extra bolts or extra axial ties.
All frozen stiffnesses, force bases and attachment datums are preserved; no
rejected response or historical active states enter the intended laws.

The inventory unlocks an exact input/output mapping if a native method passes
its branch-switching fixture. It is not a replacement solve or native run
authority. If an all-bearing response is tested, every paired normal must
be strictly positive before its floor tangent hypothesis is usable; aggregate
support equilibrium is insufficient. Current frame readiness remains false.


## Native branch diagnosis and exact workaround fixture freeze

Inspected 2.23 source computes current signed force correctly for SPRING2,
but its nonlinear tangent branch selects the interval with an unassigned
`val`; SPRING1 has the same limitation. The failed coupon stopped at the
load zero crossing and never verified the negative branch. This is a strong
source-based explanation, not binary causation proof or a physical failure.
The SPRINGA branch explicitly calculates current-minus-initial length.

A [separate straight-line SPRINGA coupon](nonlinear-springa-known-answer-attempt01/README.md)
is frozen at SHA c782f4c39c764691b6de0ed608798d43bd3b7310badf769eee3b8aa13ca230ba.
It preserves the same opposing laws, three force ramps and hand answers,
uses 100 mm numerical spans with fixed transverse motion, and remains
unexecuted pending focused independent review and parent readiness. It
changes no pinned runtime or frame inputs and grants no frame run.

The carrier inventory additionally binds engagement signs to the existing
helpers: their current tension and compression branches both engage for
`u_second-u_first > 0`, hence both use negative native
`delta=u_first-u_second`. Ordered physical endpoints and projected axes
distinguish the mechanisms. No generic tension-sign assumption is used.


## SPRINGA native signed-law and reversal method verified

The [straight-line SPRINGA coupon](nonlinear-springa-known-answer-attempt01/README.md)
passed its controlled single native launch with the same pinned 2.23 binary.
All three hand answers, signed endpoint actions, physical/ground equilibrium,
MPC closure and fixed directions pass: +10 N -> +0.1 mm, -20 N -> -0.1 mm,
then +10 N -> +0.1 mm. Parent's additional 18-increment check has maximum
table-law / ground-balance residual 1.78e-15 / 7.11e-15 N. No residual, sign
criterion, stiffness or geometry was relaxed to obtain this result. The
SPRING2 packet remains failed; its source diagnosis is an inference and no
pinned binary was patched.

Engineering result unlocked: a built-in signed unilateral scalar carrier
that opens and recloses across reversal, with verified endpoint RF meaning.
The next task is a bounded two-moving-body nested relative-coordinate MPC
fixture; it stops when complete physical-body transfer and its known answers
are verified or a specific incompatibility is exposed. This method bridge
retains the old physical projection equations and tests the newly introduced
relative layer. It provides no fresh frame run authority. Actual six-case
corner demands, applicable floor support and complete corner resistance
evidence remain pending.


## Exact-stick constraint representation at the frozen floor points

The [floor constraint expressibility audit](current-floor-stick-constraint-audit-attempt01/README.md)
expands all 200 tangential rows onto 800 unconstrained physical solid DOFs.
Their rank is 200. A distinct-pivot representation reconstructs every
original source row within 1.95e-16 coefficient residual and satisfies
the pinned manual's unique dependent-DOF rule. An admissible trial field
closes all original constraints within 2.92e-16. This avoids the illegal
approach of directly fixing an already dependent projection ghost.

Engineering result unlocked: an exact geometric representation for a
conditional all-bearing stick branch, preserving every source floor point.
Existing finite tangential springs are not automatically exact stick. No
frame deck or native solve is produced by the audit. Native constraint
reaction recovery, compatible positive normal bearing and history/recontact
remain unverified; no fixed-reference counterexample is dismissed. A native
method check must settle force transfer/reaction output before frame use.


## Nested moving-body transfer and geometric-linear iteration verified

The [relative-coordinate fixture](current-springa-relative-coordinate-fixture-attempt01/README.md)
passed its single scoped native run. Existing projection ghosts plus
`Q=u_second-u_first` with positive unilateral table law transfer equal and
opposite forces to both moving bodies and close each body. Opening and
reclosing hand answers pass. Parent independently checks all 18 printed
increments: maximum body residual 4.01e-6 N, physical global residual zero.
The numerical SPRINGA ground is explicitly excluded from physical balance.

The verified runtime also uses Newton iterations while geometric effects
are off under the frozen `NLGEOM,NLGEOM=NO` option sequence, preserving the
original small-deformation frame/body-audit assumption. The positive
relative coordinate leaves a closed-side tangent at the zero knot without
changing force law, preload or stiffness. A negative-coordinate/min law
would pick an initially zero tangent in the pinned interval lookup.

Engineering result unlocked: source-owned unilateral carrier assembly with
verified nested-MPC physical transfer and stable initial closed-side tangent.
Luna now prepares a bounded input-only a12-rear frame adapter using these
stock native carriers and the exact floor constraint representation. It
stops at source-bound deck/model/audit; no freeze, force solve or acceptance
is delegated. Exact floor reference RF interpretation remains a separate
small method check. Full-frame readiness remains false pending that mapping
and response-audit integration. No C12 authority or old-bolt resistance
requalification follows.


## Exact-floor reaction recovery verified; corner scope reaffirmed

The left outer corner assembly under evaluation is BG001 (post to exterior
spine), BG003 (spine/side/inner block through two continuous three-member
bolts), and BG045 (inner block to header). Its complete load path includes
member contact/bearing, lateral and axial bolt actions, splitting/net
sections, washer seats and onward transfer. The 92 introduced block axes
replace former ML24Z/SDS duties; they are distinct from the twelve original
LEG/FLOOR-RUNNER arrangements. Reuse unchanged baseline resistance methods
and evidence for those twelve. Reopen only an identified geometry, receiver,
hardware or demand difference; do not transfer historical case acceptance.

The [exact-floor method attempt01](current-exact-floor-mpc-fixture-attempt01/README.md)
ended before mechanics because the linear stiffness token `20` lacked a
real-data decimal point. It remains preserved as failed. The separate
[attempt02](current-exact-floor-mpc-fixture-attempt02/README.md) changes only
real-number formatting and its run identity, preserving numeric inputs and
hand answers. Its one authorized native launch returned zero. Both known
answers, Newton/geometrically-linear runtime, isolated spring forces and
physical body balance pass. Parent independently checked all twelve printed
increments: maximum RF error 5e-6 N and body-balance residual 3.56e-15 N.

Exactly one of the four predeclared reaction interpretations passes both
cases: `RF_REFERENCE_MINUS_DEPENDENT_CLOAD`. Raw reference RF is -0.5/-1 N;
after subtracting the respective applied dependent loads +6/-4 N, actual
floor x reactions are -6.5/+3 N. This is a source-load correction, not a
force fitted to residuals. Numerical SPRINGA grounds are excluded from
physical balance. For the transformed frame constraints, recover the
transferred load from `(S^-1)^T F_pivot` and restore original row ownership.
The adapter must retain raw output and this explicit source correction.

Engineering result unlocked: exact stick reference-force recovery for the
verified small compression-bearing model. Luna's next deliverable remains
an input-only source-bound a12-rear adapter; its stop condition is an
inspectable deck, model and mapping audit. Whole-frame response recovery and
positive-bearing compatibility must still pass before a scoped frame run
can produce usable corner demands. No new frame launch is authorized by
this coupon result. Minimum outstanding mechanical input is the signed
current-frame corner actions with compatible contact states and verified
body/global transfer. Applicable hardware/material and washer/splitting
exceptions remain explicit conditional checks, not accepted capacities.


## Complete corner response inventory

The [source-bound demand contract](current-corner-demand-contract-attempt01/README.md)
identifies all five corner bodies and their internal/incoming/onward
interfaces. BG001/BG003/BG045 contain six physical bolts, eight lateral
planes and six outer-seat ties. The response must also include parallel
contact and transfers crossing this five-body boundary; the 338 incident
owned groups are not 338 bolts. This inventory prevents a group-only force
summary from being mistaken for complete corner closure. No response is
used and no unchanged original LEG/FLOOR-RUNNER resistance is reopened.


## Source floor force/moment ownership verified

Parent independently checked all 200 original source tangent rows against
their physical master-node reactions and recorded floor-point/tangent
owners. Each unit reference channel preserves force and moment, with
maximum errors 1.82e-13 and 2.27e-10 mm per unit force. The reproducible
[parent input-audit packet](current-springa-parent-input-audit-attempt01/README.md)
records this source-only result. Its serialized-deck checker also verifies
reference-transfer coefficients, emitted CLOAD corrections and every
reference channel's physical wrench; no serialized pass is claimed before
the adapter emits its files. No corner forces, floor qualification or new
frame launch follows from this algebra check.


## Nonidentity floor equation reaction map verified natively

The [transformed-reaction method coupon](current-transformed-floor-reaction-fixture-attempt01/README.md)
passed its single scoped stock 2.23 launch, returned zero and reproduced both
predeclared known answers. Its nonidentity matrix and reversed source-row/
physical-pivot orders recover original-row reactions [-11.25,+7.75] and
[+6,-9] N. Those reconstruct physical support forces [-6.5,+3] and
[+2.25,-5.25] N and preserve the source/physical yaw moments -300/+525 Nmm.
The transformed source-load subtraction and row permutation are now observed
native behavior, not an extrapolation solely from the scalar coupon.

Parent independently checked every twelve printed increments: maximum RF
and body residual 5e-6 N; maximum source/physical/global yaw residual
5.69e-13 Nmm. This closes the bounded force-output-method question. It does
not close frame floor-bearing compatibility, stiffness/engagement
applicability, 50-body equilibrium or six-case corner demands. The frame
input adapter and new physical response auditor remain the next bounded
deliverables; no C12 or complete-joint acceptance follows.


## Frame builder load representation identified

The first corrected fresh assembly stopped before emission because its raw
builder load-node map differs from the frozen C11 deck's physical load map.
This is a representation dependency: the original
`freeze_trial` resets `structure.loads` from the freshly compiled
`physical_external_loads` before configuring trial springs. Panel attachment
slave loads are expanded onto physical C3D20 nodes by the existing
`_equation_load_expander`/`_record_panel_loads` virtual-work mapping.

The adapter will use that existing normalization, compare fresh body and
global physical load maps to the pinned source input, and independently
verify that raw builder loads expand to the same map before emission. Its
source-load reaction correction then uses the actual serialized physical
CLOADs. No source case load is borrowed from the rejected C11 response; no
nodal-load difference is waived without the explicit transfer proof. A
frame input pass remains pending this reassembly and parent serialized audit.


## Corrected current frame input and independent serialized check passed

The one source-bound a12-rear [adapter](current-springa-frame-input-adapter-attempt01/README.md)
has emitted its model, deck and audit. The freshly normalized physical loads
match the pinned source input, while raw attachment loads expand to that map
with maximum nodal discrepancy 1.14e-13 N. It retains 1,903 C3D20 solids,
1,292 SPRINGA carriers and 348 unchanged bilateral SPRING2 components.
All 218 material/orientation/section cards match the source deck.

Parent's independent serialized audit passes: 50 bodies and source ownership/
loads preserved; exact floor reconstruction error 7.54e-14; reference-transfer
error 4.76e-14; unit channel force/moment errors 3.61e-13 / 4.45e-10 mm;
emitted-load correction discrepancy zero; all 21,998 pivots distinct and
unfixed. Model and deck digests are respectively
`61f95ec9e670b2bd0e95d426cc14ff381283edfc4f9c87e47c2b344dd4fe50b8` and
`11674a8b50f0c292e7e03288697afa7bbfaebc0f3db5f49b0439c125a5ab9a4c`.

Next engineering gate: the source-bound physical-force auditor must pass its
actual native fixture replays and exact model/deck contract. Parent then owns
a fresh, one-launch diagnostic freeze/review; this input pass itself supplies
no run authority, frame forces or joint acceptance. The complete corner
exporter is being prepared in parallel for verified current results only.
Original LEG/FLOOR-RUNNER resistance evidence remains separate and reused.


## Corner priority confirmed; first current-frame diagnostic launched

BG001/BG003/BG045 are the left outer corner-block path: post/exterior spine,
spine/side/inner block, and inner block/header. The 92 new block-attachment
axes replace former angle/SDS duties. The twelve original LEG/FLOOR-RUNNER
arrangements remain a separate evidence class; their unchanged resistance
calculations are reused. A retained arrangement is reopened only for a named
changed geometry, receiver, hardware or current demand issue.

The final physical-response auditor passed 42 printed method-fixture states
and a near-zero SPRINGA endpoint-length arithmetic witness. Parent froze the
one a12-rear diagnostic and independently rechecked its actual serialized
inputs. Deck SHA remains `11674a8b50f0c292e7e03288697afa7bbfaebc0f3db5f49b0439c125a5ab9a4c`;
frozen model SHA is `58daa4d557c929b83fdffd989ba53ac75b82f6c87f3bc848cb1af28562a0e8fe`.
The standard serializer changes only diagnostic scope and truthful
always-active bilateral metadata. The source geometry, constitutive inputs,
loads and exact-floor reaction mappings are preserved.

[Attempt packet](current-springa-frame-a12-rear-attempt01/README.md) owns exactly
one 240-second/4-GiB serialized launch. Every printed state must pass physical
law, MPC, all-positive floor normal, global and all-50-body balance gates
before any corner force is usable. This remains a zero-gap, zero-accessory,
all-bearing exact-stick diagnostic; it supplies no joint acceptance or
historical pass transfer. The complete corner exporter is being prepared for
source-bound verified outputs. Minimum next dependency is a passing current
response; splitting, washer, bearing/contact and onward-transfer checks still
require their recorded applicable material/hardware and compatibility inputs.


## Current-frame attempt terminal: no accepted increment

The one scoped a12-rear launch ended with return code 201 after 51.43 seconds,
six failed cutbacks and accepted time zero. No usable corner forces were
gained. The same normalized residual/correction pattern persists as the
load increment is quartered, so smaller increments alone are not an evidenced
remedy. Rejected best-iterate FRD results are not promoted to demands.
This does not establish physical failure of the corner blocks.

The native slot is idle, the launch budget is consumed, and there is no
automatic retry. A bounded read-only pinned-manual/source and primary-online
diagnosis will identify at most two mechanics-preserving next methods. The
complete corner exporter remains blocked on precisely a passing current,
source-bound response; no blanket original LEG/FLOOR-RUNNER resistance work
was reopened.


## Native iteration issue resolved; exact remaining floor compatibility issue

The fresh controlled-iteration a12-rear diagnostic returned zero in 45.06
seconds and reached full load in seven accepted increments. The first took
13 iterations; later increments took two. No geometry, material, source load,
connection law, FIELD criterion or physical closure criterion changed. The
documented time controls delayed the premature residual-growth cutoff.

The strict response audit correctly rejected this all-bearing support branch.
A source-bound diagnostic screen of all 100 nonlinear normals at all seven
printed states found 17 strictly positive cells and 83 strictly separating
cells, with the same set throughout. Exact tangent restraint at those 83 open
cells is incompatible with the specified bearing-dependent no-slip law.
No corner demand is usable and no physical corner failure is established.

The next bounded engineering result is one conditional selected-bearing
branch: retain every normal law and physical input, impose exact zero tangent
motion only at the 17 proposed bearing cells, and release the 83 others.
This is a proposed state from a rejected branch, not accepted support evidence.
Fresh input/algebra and physical-response checks must prove normal/tangent
compatibility and all-body/global balance before any BG001/BG003/BG045 action
is recovered. There is no general recontact or uniqueness claim and no
unbounded native mask iteration. The original LEG/FLOOR-RUNNER resistance
work stays separate; any later affected demand is a concrete demand-only
check using unchanged resistance where applicable.


## Selected-bearing subset independently expressible; response not yet evaluated

Parent independently derived the proposed 17-cell / 34-row restraint subset
from the original source equations. Rank is 34; singular ratio is 0.158114;
pivot condition is 11.6773; source/reference reconstruction residuals are
1.11e-16 / 2.78e-16. The independent actual-deck checker is prepared in
`current-springa-selected-floor-parent-input-audit-attempt01/`. These are input
algebra results, not accepted floor reactions or corner demands.

The input adapter and response auditor have agreed the source-row, physical
pivot, reference and active/inactive map contract. Their bounded stop is one
prepared branch and a checked response method; parent still owns fresh frozen
inputs, readiness, one serialized run and final validation. Every normal,
active tangent, released tangent and physical-body/global balance must pass.
No geometry change, original bolt resistance restart or general recontact
solver is authorized by this record. BG001/BG003/BG045 remain the primary
complete corner path, and all six cases and sensitivities remain outstanding.


## Owner corner priority confirmed; two conditional support proposals rejected

BG001 (post/exterior spine), BG003 (spine/side/inner block through two
continuous three-member bolts), and BG045 (inner block/header) are the left
outer corner-block assembly: six physical bolts, eight lateral planes and six
axial ties. The 92 new block-attachment axes replace former ML24Z/SDS duties;
the twelve original LEG/FLOOR-RUNNER arrangements are separate. Their unchanged
resistance evidence is reused. No original resistance work was reopened and
no historical frame-case pass transferred. The complete corner deliverable
includes contact/member bearing, lateral and axial bolt groups, splitting,
washer seats and onward transfer, rather than isolated bolt capacities.

The 17-cell proposal reached full load (native return 0, seven printed states),
but its strict floor audit rejected inactive SPR1185. All 100 normal laws
were independently screened at every state: 23 cells bear and 77 separate,
with the same inventory throughout. A fresh input-only 23-cell proposal
passed the parent actual-deck audit and three replayed method fixtures.
Its 46 exact tangent constraints reproduce the source equations within
7.32e-14; source unit-wrench errors are 1.70e-13 N / 2.08e-10 Nmm.
Geometry, loads, laws, materials and the 92+12+66 axis classes are preserved.

Parent froze and ran that single proposal in
`current-springa-selected-floor-a12-rear-attempt02/`: native return 0,
59.56 seconds, confirmed terminal, full factor 1. Its strict response audit
rejected inactive SPR1215 at time 0.1. Diagnostic screening of all 100 normal
laws at all seven states gives 25 bearing / 75 separated cells, adding
`floor_base_floor_right_26` and `floor_base_floor_right_28`, losing none.
This diagnoses an incompatible prescribed bearing set; it does not establish
physical corner failure or usable corner forces. No response is promoted, no
third native mask run is authorized by this record, and tolerances remain
0.1 N / 2 Nmm. The two terminal assessments and diagnostic screens preserve
the exact rejection and file pins.

Minimum calculation dependency: a compatible source-bound frame support
response, with signed corner/onward interface actions and all-body/global
closure. Then reuse the existing conditional NDS/washer/net-section arithmetic
with those concurrent forces. Accepted corner resistance additionally needs
applicable member design strengths/grain/service assumptions, washer/bolt
compatibility and an applicable splitting treatment for the actual topology
(in particular BG003's oblique middle-member end and orthogonal bore families).
These are explicit conditional limits, not a new inspection or blanket external
sign-off prerequisite. All six cases and stiffness/engagement sensitivities
remain outstanding; solver convergence alone closes none of those gates.


## One current conditional response closes the numerical demand gate

The freshly frozen 25-bearing / 75-separated a12-rear proposal in
`current-springa-selected-floor-a12-rear-attempt03/` completed with native
return 0 in 60.37 seconds, confirmed terminal, seven printed increments and
full load factor 1. All source MPC, 1,292 SPRINGA, 348 bilateral, 100 floor
normal and 50 active / 150 inactive tangent checks pass at every increment.
The prescribed bearing set remains compatible. Raw and rounding-interval
all-body/global equilibrium pass without changed tolerances.

The independent parent sums also pass all 50 physical bodies and the global
frame at all seven increments. Maximum raw force residual is 0.000813895 N;
maximum raw moment residual is 0.877489569 Nmm, within 0.1 N / 2 Nmm. Numerical
ground reactions are excluded. Frozen model/deck/live-source verification
passes after terminal assessment. Response SHA-256 is
`892dadeed0b20d809ce5250d3cd1c3deb31697f69208d8bbefb5f702160e1274`.

The immutable auditor passed its calculation but its CLI could not encode
NumPy Boolean values as JSON. The separately recorded parent writer converts
only NumPy scalars to Python scalar values, uses strict JSON, and reruns the
unchanged pinned audit. No native run, threshold, mechanical computation,
frozen source or response gate was changed for serialization. The independent
parent audit reads the serialized response and passes.

Parent adopts this response only as conditional numerical case forces:
ring A, Hillman axial proxy ratio 1, zero bolt gap, zero accessories and an
unverified no-slip floor assumption on the reviewed geometry. It is not a
joint resistance pass, six-case envelope, sensitivity closure or floor/build
qualification. BG001/BG003/BG045 complete-path export and applicable screens
are the next immediate result. The 92 new axes remain separate from the
twelve original LEG/FLOOR-RUNNER arrangements; unchanged original resistance
evidence is reused. The remaining five cases need their own compatible
support responses, and stiffness/engagement/accessory exceptions stay open.


## Complete left corner numerical path exported for the first conditional case

`current-corner-native-demand-export-attempt03/corner-demand-report.json`
now reports all 338 owned interfaces, including incoming/onward transfer,
232 contact rows and twelve outer head/nut washer-seat records. All five
corner members close independently at each of seven increments; worst local
raw residual is 0.000696 N / 0.4754 Nmm. Parent additionally checked exact
signed exported vectors against the passed native response, complete source
inventory, all six physical bolts / eight planes / six ties, and all four
local released zero-action floor groups at every increment.

At full load in this conditional a12-rear scenario:

| Group | Separate lateral-plane resultant magnitudes (N) | Axial tie magnitudes, one per physical bolt (N) |
|---|---|---|
| BG001 post/spine | 301.657; 335.061 | 64.966; 18.473 |
| BG003 spine/side/inner block | bolt 1: 483.948 / 65.913; bolt 2: 239.230 / 86.983 | 95.967; 43.508 |
| BG045 inner block/header | 90.116; 24.946 | 119.343; 19.882 |

These magnitudes summarize separate signed vectors preserved in the report.
They are not independent capacities, a force envelope or joint acceptance.
BG003's unequal outer-plane actions prevent blindly applying its earlier
equal-outer-action double-shear reference. Maximum modeled full-annulus
washer pressure is approximately 0.536 MPa; this is a geometry conversion,
not a washer steel/pull-through or wood resistance pass. Splitting/net
section work still requires applicable methods and actual section actions,
not the whole-body equilibrium resultants.

The remaining five fresh case inputs and the source load register are in
progress. Each case needs its own compatible support response; no force or
bearing-mask transfer from this first case is allowed. The conditional
resistance comparison reuses reviewed original methods and keeps genuine
applicability exceptions explicit. All original LEG/FLOOR-RUNNER resistance
evidence remains separate and unchanged.


## Six fresh source cases registered; five native inputs in progress

`current-six-case-source-load-register-attempt01/register.json` contains fresh
source assemblies for a12-rear, a12-forward, a12-left, k12-right, k12-rear and
a1-rear, with a common non-load geometry/carrier signature and exact per-case
load/wrench maps. Parent checked all recorded source hashes and independently
recomputed the hold-standoff moments for every case. Register SHA-256 is
`7a638a49fc5086b4d5fed52148286a300b8b271f7d380b1a131ea8e17b094508`.
Only a12-rear has a passed conditional native response. The five remaining
inputs are being prepared in `current-springa-six-case-frame-input-adapter-attempt01/`,
with no native/freeze authority delegated and no bearing-mask transfer.

Final corner report SHA-256 is
`812a62fa3cd96a8983649c84a8c78a8d176d639465c887b11d1827a3f8f1ee17`.
Parent exact signed-force/inventory audit passes for that final report at all
seven increments. A stale washer-source unit-action caveat was corrected
only in the fresh export projection; forces and original source evidence
were unchanged. Applicable component resistance arithmetic is being recorded
separately; it remains conditional and cannot supply a combined joint pass.


## First resistance comparability screen and five audited case inputs

`current-corner-a12-conditional-resistance-screen-attempt01/` is complete and
its pinned producer replay passes. For the passed conditional a12-rear
response, BG001's separate Y/Z component/reference ratios are
0.266/0.328 and 0.375/0.325; BG045's are 0.222/0.0369 and
0.0604/0.0151. These are necessary individual component screens, not
combined-action DCRs, adjusted design capacities or joint passes. BG003 has
no applicable symmetric double-shear comparison: paired plane magnitudes
differ by 7.342 and 2.750, with non-collinear actions. Four eligible
base-post/header washer references have conditional ratios 0.0192–0.1243;
block seats are not given a perpendicular-grain reference. Splitting,
section actions, adjustment/interaction and bolt/washer compatibility stay
explicitly unresolved. No original resistance check was reopened.

All five remaining fresh source-bound frame inputs now pass independent
parent serialized-input audits in
`current-springa-six-case-frame-input-adapter-attempt01/`. Their load maps
match the fresh register; material/orientation/geometry are preserved.
No a12-rear bearing mask or response is transferred.

The separately frozen forward all-bearing diagnostic completed at full
load with native return 0 in 40.85 seconds. Its source-bound normal-law
screen gives 35 bearing / 65 separated cells at each of seven increments,
so all-bearing tangent restraint is rejected and its forces are withheld.
One forward-specific 35-cell/70-row proposal is being prepared. The left
case all-bearing diagnostic is independently frozen/audited and running
under parent serialized control. One conditional six-case response is
usable; the other five response/support pairs and sensitivities remain open.


## September 30: five diagnostic runs complete; forward selected branch underway

All five remaining case-bound all-bearing native diagnostics reached full
load with confirmed terminal execution. The summary is
`current-five-case-native-diagnostic-register-attempt01/register.json`.
Their forces remain withheld because tangent restraints include separated
cells. Stable positive-normal counts are forward 35, left 10, K12-right 10,
K12-rear 16 and A1-rear 44. K12-rear has one first-increment cell whose
printed displacement interval is inconclusive; a bounded zero-SPC evidence
check is in progress, without relaxing physical criteria.

The forward-specific 35-bearing/65-released proposal passed independent
serialized-deck and frozen case-context checks. It is now under one
parent-owned serialized native run in
`current-springa-selected-floor-a12-forward-attempt01/`. Its frozen model
SHA-256 is `50edee6194d3abdb758e8e7eb17f361b10cae7fc839dcedfa9f24f070d25324b`;
the deck is `401930f909d503e388a68f3eade5ebfaa1e228d5bc48712a217e170fe8bef553`.
The stop condition is terminal execution followed by strict support,
carrier-law and all-50-body/global balance checks at every increment.
Until those pass, only the earlier conditional a12-rear corner response is
usable. No mask, force or acceptance is transferred between cases.

BG001/BG003/BG045 are the left outer corner assembly: post to spine,
spine/side/inner block, then inner block to header. The six physical bolts,
eight lateral planes and six axial ties form one complete path. The 92 new
block axes remain separate from the twelve original LEG/FLOOR-RUNNER
arrangements. Their unchanged resistance evidence is reused; none was
reopened by this work. Remaining joint dependencies include the response
envelope, unequal three-member BG003 action compatibility, timber splitting
and section actions, and actual bolt/washer/grain compatibility.


### Forward selected proposal terminal result

The forward 35-bearing proposal reached full load with native return 0 in
43.06 seconds and confirmed terminal execution. Its strict case-bound
response audit rejected inactive normal SPR1026: strict separation with
zero endpoint RF was not established. Forward corner forces are withheld;
this is a support-pattern mismatch, not a demonstrated physical joint
failure. `current-springa-selected-floor-a12-forward-attempt01/parent-terminal-assessment.json`
records the exact rejection. A bounded fresh normal-law screen is identifying
changed support states; no automatic iteration or geometry change is authorized.
The usable conditional case count remains one, and the native slot is idle.


### Exact forward support mismatch localized

Parent read-only diagnosis binds the terminal DAT and confirms SPR1026,
`floor_base_floor_left_1`, is strictly bearing at all seven increments despite
being designated inactive. Its final normal force is 9.570275 N with a
0.0000005 N printed-force radius; projected closing displacement is
0.00005257167 mm with a 0.000000500005 mm printed-displacement radius.
This is not merely an ambiguous zero token. Evidence is
`current-springa-selected-floor-a12-forward-attempt01/parent-offending-cell-diagnosis.json`.
The full normal-only diagnostic screen reports a stable 31 bearing / 69
separated inventory; that remains diagnostic, not a validated replacement
branch. A future proposal must explicitly record support-stage lineage and
pass complete compatibility again. No corner force adoption follows here.


### Forward mask changes and bounded follow-on work

The fresh selected-floor normal-law screen pins terminal output and records
31 strictly bearing / 69 strictly separated / zero ambiguous cells at all
seven increments. Relative to the proposed 35-cell mask, six selected cells
became separated and two released cells became bearing: left runner cell 1
and right runner cell 7. This eight-cell change must be explicitly carried
in any next proposal; a convergence flag cannot replace complementarity.

The source-bound screen is
`current-springa-a12-forward-selected-floor-screen-attempt01/screen.json`.
Parent verified its source pins and separately recovered SPR1026's positive
force at every increment. Fresh work is bounded to a left-case input
proposal from that case's own ten-cell diagnostic, the BG003 asymmetric-action
applicability check, and a representation-only scientific-zero U-token proof.
The zero-token investigation must preserve nonzero-U and all-RF intervals,
source/method guards and physical criteria. It cannot fix the forward mask's
real contact changes or justify accepting its corner forces.


### Independent forward native normal replay

`current-forward-floor-parent-interval-audit-attempt01/check.py` independently
parses the recorded native U/RF tokens, emitted node coordinates, and source
projection/normal bindings without importing any FEA recovery kernel. Its
`audit.json` passes all 700 cell/increment classifications, reproducing the
31 positive / 69 strictly separated / zero ambiguous pattern. It pins the
exact model/deck/DAT/screen and its own source. This strengthens the support
mismatch diagnosis only; it does not promote rejected forces or establish
any joint resistance or floor qualification.


### BG003 unequal-action method boundary and conditional references

`current-bg003-unequal-action-applicability-attempt01/` is complete and its
producer replay and parent independent Mode Is arithmetic pass. Current
NDS-2024 single/symmetric-double yield provisions and unequal-side-length
rules do not supply a complete resistance comparison for the observed
unequal, non-collinear three-member actions. The historical 2018 asymmetric
clause also assumed equivalent side-member loads. The four separate
outer-receiver bearing-mode reference ratios are 0.2754, 0.0313, 0.1533 and
0.0434, under the explicit DF-L G=0.50, full-shank quarter-inch, proposed
grain and conservative effective-length scenario. These are component
reference comparisons, not adjusted complete-joint DCRs or passes; they are
not summed. Coupled middle-member action, dowel bending across both planes,
axial/lateral interaction, group adjustment and splitting remain separate
unresolved checks. The current consolidated AWC errata was considered;
its sub-quarter-inch KD correction does not alter this quarter-inch term.
No original LEG/FLOOR-RUNNER resistance was reopened and geometry is unchanged.


### September 30: left and K12-right selected diagnostics terminal

Parent independently audited and froze the case-specific left and K12-right
10-bearing/90-released proposals. The left native execution is terminal with
return 0 in 51.83 seconds; strict response audit rejects inactive SPR1269,
`floor_base_post_center_right_2`. Parent source-bound diagnosis finds its
positive normal force rises from 0.9737118 N to 9.737118 N; its final closing
coordinate is 0.00007317606 mm ± 0.000000500005 mm. This is a real mask
mismatch, not a printed-zero ambiguity. K12-right similarly reached full
load with confirmed terminal return 0 in 52.33 seconds, but its strict audit
rejects inactive SPR1257. Both native packets contain exact terminal
assessments and withhold corner forces pending complete normal-state screens.
No physical corner failure is inferred and unchanged original bolt
resistance is not reopened.

The A1-rear 44-bearing/56-released input passed source-bound input checks and
is under parent-owned frozen readiness/execution. The forward 31-bearing
proposal is prepared from the explicit selected-stage screen projection,
which preserves both original all-bearing physics authority and its direct
rejected selected35 output lineage. It is not a transferred pass or force
source. Neither prepared input implies support compatibility or joint
acceptance. The six-case response envelope and sensitivities remain open.


### Owner clarification: corner replacements are the primary joint deliverable

BG001, BG003 and BG045 explicitly describe the left outer corner-block
assembly: post to exterior spine, spine/side/inner block, then inner block
to header. Its six bolts, eight lateral planes and six outside axial ties
are evaluated as one complete path, including contact/member bearing,
splitting, twelve washer seats and onward transfer. The 92 introduced
block-attachment axes remain separate from the twelve original LEG and
FLOOR-RUNNER arrangements. Unchanged original resistance calculations are
reused; no general requalification is opened. Any affected original check
must first identify its specific changed demand, geometry, receiver or
hardware. Historical case passes do not transfer to the revised frame.

The independently balanced a12-rear conditional response remains the sole
usable corner demand case: BG001 lateral resultants 301.657/335.061 N;
BG003 plane resultants 483.948/65.913 and 239.230/86.983 N; BG045
90.116/24.946 N. Maximum outer axial tie is 119.343 N. Existing component
references and full-annulus washer-pressure screens are retained; they do
not establish complete-joint acceptance. The exact BG003 resistance gap is
coupled unequal, non-collinear three-member dowel action; symmetric
double-shear ratings and summed independent plane capacities are inapplicable.

A1-rear and forward31 executions are now terminal, return zero, but their
forces remain withheld. A1's source-supported zero-U representation audit
clears its initial precision gate and then rejects inactive SPR1131. Both
the original and refined representation audits reject forward31's selected
SPR1026; a bounded full normal-history diagnosis is underway. These are
response compatibility exceptions, not physical corner failures. The next
left proposal is source-bound to its own diagnosed two-cell swap; parent
readiness and one serialized execution retain all frozen methods and criteria.

Minimum remaining evaluation dependencies are a compatible six-case corner
demand envelope and engagement/stiffness sensitivity, applicable coupled
BG003 resistance with bolt bending and axial/lateral interaction, and
member section/splitting/row/edge transfer and washer/hardware resistance
under explicit material, grain, shank and seat-support scenarios. No stock
or hardware inspection or fabrication permission is inferred. Panel work
is bounded to an actual corner receiver/load-transfer dependency.


### Latest left-load proposal: terminal, corner forces withheld

The source-bound left swapped10 proposal ran once under parent frozen
readiness: terminal return zero in 49.77 seconds, DAT SHA-256
`eeff478cf6c3a011da3330f8d7dd2cc8ad3a2020959a0ba8700520ed15bfa5bc`.
Both the original strict response audit and the independently documented
zero-U representation variant reject inactive SPR1302. The exact terminal
assessment is stored in `current-springa-selected-floor-a12-left-attempt02/`.
No corner forces are exported from this response. Follow-up is bounded to
support compatibility, not an automatic sequence of mask retries. This
does not infer physical failure, alter geometry or reopen original bolt
resistance. The usable corner-demand count remains one conditional case.


### September 30: six-case response register and K12-rear terminal exception

The [current six-case corner response register](current-six-case-corner-response-register-attempt01/README.md)
authenticates all six terminal executions and keeps the usable-demand count
at one conditional rear case. K12-rear's source-bound 16-bearing proposal
completed in 53.19 seconds, return zero; the validated zero-U representation
audit rejects inactive SPR1074. Exact model/deck/DAT and exception pins are
in its parent terminal assessment. No forces from that response are adopted.

The bounded forward31 diagnosis shows selected SPR1026 is strictly separated
at every increment, not interval-ambiguous: its full-load projected q is
about −0.02885715 mm, native table force zero. The observed 37-positive/
63-separated pattern is stable through seven increments and equals none
of the previous 35- or 31-cell patterns. It is not an adopted replacement
mask and does not trigger an automatic retry. A case-local reproducible
diagnosis is being recorded. Geometry, laws, criteria and unchanged original
LEG/FLOOR-RUNNER resistance remain preserved.


The forward31 diagnosis is now durable in
`current-springa-a12-forward-selected-floor-compatibility-diagnosis-attempt01/`;
its replay is byte-identical and parent independently rehashed all 40 source
pins. Exact displacement intervals and seven-state classifications confirm
the previously recorded compatibility exception. No new mask or force
adoption results from that diagnosis.


### Current actual-direction single-bolt lateral references

The [resultant-direction packet](current-corner-resultant-direction-single-shear-attempt01/README.md)
now evaluates the actual a12-rear lateral direction for both connected
members at each BG001 and BG045 bolt. It replaces the need to infer a
lateral comparison by combining separate coordinate components. Under the
existing smooth full-body quarter-inch, Fyb 45,000 psi, zero-gap, proposed
grain and Fe 5,600/4,450 psi endpoint scenarios, all six yield modes are
retained and Mode IV governs all four bolts. BG001 ratios are 0.42363 and
0.49082 against 712.070 and 682.661 N references. BG045 ratios are 0.22468
and 0.06230 against 401.080 and 400.416 N after the existing conditional
Ceg=0.67 once. They remain individual-bolt lateral reference comparisons,
not adjusted design DCRs, group/axial interaction checks or complete-joint
passes. BG003 remains a coupled unequal, non-collinear three-member problem.

Parent independently recomputed force norms, proposed grain angles,
Hankinson Fe interpolation, reduction angle and Mode IV arithmetic without
importing the yield helpers. The parent audit binds final screen SHA-256
`d3b1ce4448ea90929b6410424f0212d86b4caee5130bca7c93209e06ad5b3c10`.
The producer replay and its final checksum manifest pass. All four actual
axial tie vectors/magnitudes remain separate; no missing field is defaulted
to zero. Twelve original LEG/FLOOR-RUNNER arrangements remain out of scope.


### A1-rear now passes its conditional response and independent body sums

The source-bound A1-rear 46-bearing/54-released proposal ran once and is
terminal, return zero in 40.10 seconds. All seven increments through full
load pass the pinned zero-U response method's support, MPC, spring-law and
physical balance gates. The immutable auditor's CLI failed only while
serializing a NumPy boolean after mechanics checks had completed. The new
parent writer converts NumPy scalar types to native JSON types and reruns
the same unchanged audit; no native rerun, criterion or force change occurs.

Response SHA-256 is `257b5b743369fcc2242537b7ccfe81f2efba0a195ef044624d7b67da6a09678c`.
Parent independently summed all 50 physical bodies and global force/moment
resultants at every increment without importing the recovery balance kernel.
Maximum raw residuals are 0.0002213 N and 0.159621 Nmm, within the frozen
0.1 N/2 Nmm criteria. The exact parent terminal assessment permits this
conditional case's forces, not joint resistance or a historical pass.

There are now two usable conditional physical responses and one completed
signed corner export; A1's complete BG001/BG003/BG045 corner projection is
in progress. Four remaining load cases and whole-frame engagement/stiffness
sensitivity still require compatible audited responses. The twelve original
LEG/FLOOR-RUNNER resistance arrangements remain separately preserved.
