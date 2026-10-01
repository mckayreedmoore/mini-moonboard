# MVP acceleration reassessment

This is an independent analysis and next-work recommendation following the
owner's request to reassess the route to MVP. It concerns
`compact-floor-flush-wood-joints-development`, reviewed revision
`led-clearance-2x6-runner-seated-blocks-v1`. It changes no geometry, selected
candidate, criterion disposition, native-run reservation or release flag.

**Current joint priority (owner correction, September 29, 2026):** investigate
current bolted timber/block connections using explicit conditional joint loads
where signed frame demands are unavailable. Preserve completed panel work; the
[bounded applicability comparison](prior-panel-applicability-bounded-2026-09-29.md)
identifies the changed screw stations and receivers. Complete panel qualification
is not a blanket prerequisite for these conditional joint calculations. Existing
geometry and native-run controls remain unchanged.

**Current operations (September 29, 2026):** use the
[current Luna Max checkpoint](LUNA-MAX-COORDINATOR-CURRENT-CHECKPOINT-2026-09-29.md)
and [status/work order](LUNA-MAX-COORDINATOR-STATUS-AND-WORK-ORDER-2026-09-29.md)
for the bounded evidence sequence and T09 disposition. The A/B comparison and
six-case demand register passed exact-hash cold review; the register finds no
path-complete member/joint demand subset. T09 mesh preparation and generation
are deferred. Reopen that work only if the integrated gate review identifies a
specific required mesh result unavailable through the planned reduced model
and code/product checks, followed by a separate parent decision. This notice
supersedes stale text below that describes the comparison/register as pending
or T09 as the next go/no-go; the full MVP-E endpoint remains unchanged.

## Decision

For the current execution checkpoint, use the [Luna Max checkpoint](LUNA-MAX-COORDINATOR-CURRENT-CHECKPOINT-2026-09-29.md), [status/work order](LUNA-MAX-COORDINATOR-STATUS-AND-WORK-ORDER-2026-09-29.md), [coordinator handoff](COORDINATOR-HANDOFF.md), and [next-stage plan](NEXT-COORDINATOR-PLAN.md), together with the cold-reviewed [Option A/B comparison](option-ab-method-selection-2026-09-29.md) and [demand register](demand-coverage-register-2026-09-29.md). The comparison recommends the conventional whole-frame static-demand/code-check route as the MVP architecture; no accepted member or joint demand subset exists in current evidence. T09 remains deferred under the current status. Root retains any later readiness/run decision. No native run is authorized by these documents.

Pursue conventional global static demands with code-based connection checks
and narrowly targeted local models. The complete six-case demand table stays
gated on a defensible floor support law, the beam model's member-weight
distribution, the panel withdrawal tension path, and complete receiver-to-
frame paths. The c11 solid builder already distributes its 50 member/panel
self-weights; that does not establish beam bending demands. Its 586 hardware
gravity sources are mapped into receiver-body wrenches, but their actual
mechanical transfer and force split remain unproven. Until paths and response
are validated, treat the six-case resultants and geometry as inputs/preflight,
not partial member or joint demands. A new solver-instrumentation coupon is
not that result.

The complete MVP-E endpoint remains the conditional engineering and shop
package defined in the [completion handoff](../../luna-max-completion-handoff.md).
This packet is progress toward that endpoint, not a replacement definition or
a completed engineering evaluation. The separate selected bracketed candidate
retains its own limited evidence; its passes do not transfer to the wood joints.

## What the reassessment found

The September 29 status report records no accepted ordinary-joint response
and all 47 criteria pending. Ten serialized a12-rear zero-gap diagnostics
c00–c09 preceded c10. The narrow v2 c09 predecessor gate passes independent
review and parent checks, but c09's saved audit remains false and its nine
contact-sign exceptions remain. The c10 r2 packet was frozen at
`bbaa8929b5c28c853a35e65ce12a91c82faaf1ad2129c9424c9ff385633ab226` and run
once to terminal exit 0; its three contact-complementarity exceptions remain
in the [coordinator handoff](COORDINATOR-HANDOFF.md), and its one-run cap is
spent.

The c10-to-c11 read-only calculation found one unique 511-group transition
with zero ambiguity and no repeat across c00–c10. It changed the three c10
exception states, but did not close the branch. c11 r1 was frozen at
`1633e79900afd194ece79c7463a7b383a11bb96920e7449e6a25c528e933b8e2`, passed
independent exact-freeze review (14/14), and consumed its one parent-authorized
run. The independent postrun audit
(`0c6c7b8601a8b15cd46901c912934483b5da14babb84380a9301c0730cdb18ed`, 15/15)
confirmed global/body equilibrium, MPC, ties and RF recovery, but six
compression-only contact failures remain. Numerical checks and mechanical
acceptance are false; c11's one-run cap is spent. The bounded, read-only
reassessment of all six failures is recorded in
[c11-method-model-reassessment](c11-method-model-reassessment-2026-09-29.md).
It supersedes the initial native-CalculiX contact-coupon recommendation:
stock 2.23 cannot represent ideal no-slip only while bearing without an
unsupported friction coefficient. Option A therefore replaces the current
finite paired floor `SPRING2` tangents with ideal conditional constraints and
requires a new analysis revision, exact freeze, initial/re-engagement tangent
references, and a separate method check. c11 floor tangents and their demands
do not transfer. Do not derive or run c12, or advance to the radial fixture or
source-clearance work under the current plan.

The independent [coordinator handoff review](COORDINATOR-HANDOFF-REVIEW.md)
and the completed [Option A/B comparison](option-ab-method-selection-2026-09-29.md)
identify separate blockers: conditional no-slip floor support; six outward
panel-normal loads of 1.20–1.66 kN with unsupported Hillman 42605 withdrawal
stiffness and resistance; incomplete receiver-to-frame paths; and beam-model
self-weight distribution needed to recover internal bending. The later c11
source map assigns hardware gravity wrenches and distributed solid-body
self-weight, but does not validate physical stiffness, load sharing, or beam
section actions. The
[panel-withdrawal preflight](panel-withdrawal-preflight.md) details that
missing load path. No single contact-method fix clears these blockers. The
[new feasibility plan](next-gate-feasibility-plan-2026-09-29.md),
[coordinator handoff](COORDINATOR-HANDOFF.md), and
[next coordinator plan](NEXT-COORDINATOR-PLAN.md) contain the current gates.
Earlier solver defects remain recorded; another general solver port is not
the next task.

The owner's [recorded architecture guidance](../../next-mvp-plan.md#owner-mechanics-architecture-guidance-september-27)
already calls for economical whole-frame demands, justified connection-family
models, and detailed solids for unresolved mechanisms. It does not require a
dense three-dimensional model of every timber, nut and washer. The existing
six applied cases are equivalent static loads, including the recorded 250 lb
times two force basis, horizontal components, patch and hold standoff. They
do not supply an impact history. A numerical static load ramp must not be
presented as a measured physical transient.

Some stated blockers concern the selected method rather than the physical
structure: the exact full-frame tetrahedral mesher, curved contact-pressure
output and inertial nut-map behavior. A static reduced model can avoid those
specific dependencies. Other blockers remain real: connection engagement,
frame mechanisms, bolt forces and moments, wood splitting and bearing,
washer behavior, panel/screw transfer and the center-kicker support paths.

## Work completed in this packet

The owner subsequently directed starting this route with Luna/max agents.
The [reduced static assembly preparation](reduced-static-attempt01/README.md)
contains the first current-model implementation and its explicit remaining
connection/response work. Its external-load table is not a joint-demand result.

### Current geometry groups

[The bolt inventory](bolt-groups/README.md) reconciles all 92 candidate axes
into 46 geometric groups, with two axes per group: 44 groups have two receivers
and two groups have three. The twelve retained frame bolts remain separately
identified. Group membership, member-grain proposals, axis directions and
spacing projections can now feed a connection calculation. This removes an
inventory gap; it does not establish a load-aligned NDS row or load sharing.

Twelve header axes are parallel to one receiver's proposed grain and
perpendicular to the other's. The existing lateral-yield helper excludes
that case, but helper scope must not be mistaken for a code prohibition.
NDS-2024 has an end-grain lateral-fastener route in sections 12.3.3.4 and
12.5.2.2. Apply its bearing-property and end-grain adjustments with the correct
member roles before calculating those axes; they are not automatically a new
three-dimensional strength-research problem. The two three-member groups need
their own physical stack and single/double-shear applicability checks.

For an ordinary four-bolt cleat, the rail pair and principal pair are two
interfaces along the transfer path through the block. Four individual bolt
values cannot simply be added into one joint capacity. The direct timber butt
seat is a separate compression path, and moments introduce additional demands.

### Reusable single-bolt calculation

[The preliminary calculation packet](nds-screen/README.md) reuses the existing
TR12 helper for four explicit quarter-inch smooth-body bolt scenarios. With
the stated wood, bearing-length and 45,000 psi bolt bending-yield assumptions,
individual reference values range from 568 to 796 N before group, geometry,
service or other applicable adjustments. This supplies no actual joint demand
or accepted capacity. The twelve end-grain-axis cases remain separate from
these perpendicular-axis calculations.

The producer checks all six published rounded modes of the existing TR12
benchmark and independently checks the NDS mode IV closed-form expression
against every scenario. It records assumptions, source and helper hashes,
and exclusions rather than treating unspecified hardware as qualified.

### Necessary whole-board equilibrium

[The reproducible screen](global_equilibrium_screen.py) uses the exact STEP
floor faces of eight existing timber members, the current applied load points
and the existing 778-row mass-centroid record. Source hashes, STEP volumes,
aggregate mass, force/moment units and load-reference shifts are checked.
No new connector-to-floor support is introduced. The two kicker-panel bottom
faces lie inside this footprint hull and receive no support credit here.

The recorded CAD/density estimate is 224.421 kg with center of mass
(-1.645, 697.858, 1033.609) mm. Under that estimate all six cases have a
required floor-normal center of pressure inside the support hull. The governing
rearward cases have 379.138 mm minimum hull-edge margin. At the same fixed
centroid, the minimum assembly mass for those cases is 42.831 kg. Even the
quarter-mass sensitivity (56.105 kg) has 44.204 mm margin in those two cases.
Results are in [global-equilibrium.json](global-equilibrium.json).

An independent Luna/max reviewer recomputed the hull using a separate
monotone-chain construction and recomputed moments and mass thresholds from
the source files without importing the producer. The results agree. A separate
analytic eccentric-force self-check verifies the sign convention.

This is only a necessary global equilibrium condition. Intact internal load
transfer is assumed. It does not establish frame stability, compatible foot
reactions, local uplift, bearing, sliding, yaw resistance or a floor rating.
Mass is modeled, not weighed. Uniform mass scaling retains the same center of
mass and is not a guaranteed material bound. The unlocated 25 kg equipment
allowance is excluded. The existing no-slip assumption remains unverified.

## Options considered

| Route | Value and limitation | Decision |
|---|---|---|
| Continue complete solid/contact solver development | Can answer detailed contact questions, but the next coupon still supplies no joint or frame result. | Keep existing evidence; make new instrumentation depend on a specific missing design result. |
| Start another general or commercial FEA package | May improve meshing/contact convenience; still needs the same load paths, material specification and wood resistance checks. Adds another translation and validation effort. | Do not start another wholesale port. |
| Conventional static frame model plus NDS/APA checks | Reuses current geometry, load cases and established component methods; isolates the few mechanisms that need detailed analysis. | Selected route for acceleration. |
| Targeted connection consultation or test planning | Can answer a sharply defined unsupported connection question without commissioning a complete software project. A test program needs an interpretation of strength and variability. | Optional escalation for a named unresolved mode; no blanket new sign-off gate or physical work is introduced. |
| Return to the selected bracketed design | Already has its own six-case/36-check conditional evidence, but also recorded limitations and different structural disassembly behavior. | Fastest alternative only if the owner changes the removable-bolt objective; not selected here. |

## Concrete next work

1. **Specify the analysis inputs.** Use the existing DF-L design scenario,
   declared grain directions and a source-supported bolt bending-yield basis.
   Define required bearing/shank/thread geometry, nut and washer dimensions as
   design requirements; separately establish that purchasable parts can meet
   them. Receiving measurements remain later observations. For panels, use
   grade/performance-based properties where the material specification and
   model permit it. Do not invent product identity or transfer another screw's
   values to the purchased Hillman screws.
2. **Screen the exceptions first.** Resolve the twelve end-grain-axis cases,
   the two three-member groups, washer support, and the center-kicker support
   paths. Use the inventory to name each affected physical interface. A
   missing path or failed applicable check produces a specific finding before
   any geometry change; it is not a reason for another ordinary-joint coupon.
3. **Build current static demands.** Reuse existing frame-model infrastructure
   and source geometry. Represent long members with appropriate structural
   elements, panels and their actual attachments, and finite connection
   stiffness at the actual eccentric locations. Include clearance/seating,
   tension/compression asymmetry and supported contact where they affect the
   result. Retain the no-slip/no-anchor floor basis. Check global and individual
   free-body force/moment closure, internal mechanisms, displacements, and
   changes in load sharing across physically justified stiffness scenarios.
   Rigid and pinned endpoints are not automatically conservative bounds.
4. **Use standard resistance calculations.** Apply per-fastener yield, group
   action, geometry/service adjustments, bolt axial/lateral interaction, wood
   splitting/tear-out/net sections, washer support and connector/member checks
   to concurrent signed demands. AWC's calculator can independently check
   eligible per-fastener results. It does not qualify the complete corner block.
5. **Escalate only unresolved mechanics.** Retain stock Code_Aster 17.4 for
   local behavior requiring more detail. Its existing body-restricted force
   recovery provides a bounded resultant route; do not make full curved
   pressure reconstruction a universal prerequisite for force-based bolt
   design. Where a seat's actual compressed area or opening controls a check,
   keep that area question explicit and resolve that local model. Validate any
   newly consumed discrete/spring behavior on a small known-answer example.
6. **Finish the same MVP-E gates.** Map each inherited criterion to the new
   representation and document equivalence or a justified method revision;
   do not silently mark mesh-specific checks passed or delete physical duties.
   Complete hardware fit, removal, costs, instructions and independent review.

The next milestone is a decision-useful current six-case demand/exception
table. If its results depend strongly on an unsupported joint law, focus work
on that law. If it identifies a mechanism or failed geometry/resistance check,
report the named change needed. Neither outcome justifies an open-ended return
to generic solver instrumentation. No credible final completion date follows
from the screens completed here.

## Primary online references

- [AWC Connection Calculator](https://awc.org/resources/connection-calculator/)
  supplies eligible individual-fastener calculations under NDS-2024.
- [NDS-2024 Chapter 12](https://awc.org/wp-content/uploads/2026/08/AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-%E2%80%93-Dowel-type-fasteners.pdf)
  supplies the dowel-type lateral-yield and end-grain provisions. Its applicability
  is separate from the current repository helper's intentionally narrow scope.
- [APA Panel Design Specification](https://www.apawood.org/guides-tools-training/technical-document-library/technical-guides/panel-design-specification/)
  gives design properties and methods for qualifying structural-panel classes.
  This creates a possible equivalent-panel route; it does not identify the
  owner's particular sheets or automatically supply every shell constant.
- [Code_Aster v17 discrete-element examples](https://code-aster.org/doc/v17/manuals/man_u/u2/u2.02.03/Exemples.html)
  include a bolted assembly with discrete bolt elements. The
  [discrete-law guidance](https://code-aster.org/doc/v17/manuals/man_u/u2/u2.02.03/Affectation_des_proprietes_des_discrets.html)
  distinguishes penalty contact from physically meaningful connector stiffness.
  These are available modeling tools, not a calibrated law for this timber joint.

## Reproduction

From the repository root:

```sh
.venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/global_equilibrium_screen.py
python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/bolt-groups/produce.py --verify
python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/nds-screen/produce.py --verify
```
