# Design recommendation and next decision gates

Research/decision checkpoint, 2026-09-06. **Develop the untied 2×8-foot100
candidate next; do not build or climb it from the current provisional schedule.**
The evidence now supports a development choice and a finite next-work plan,
not an assertion that this is the lightest, cheapest or structurally sufficient
final assembly. Original alternatives remain available and unchanged.

Scope remains one climber, 250 lb intended maximum, with 150/200 lb comparisons
and 300 lb sensitivity—not certified ratings. No anchors, crash-pad support,
unmeasured ballast or assumed room clearance is credited.

## Disposition of the alternatives

| Candidate | Decision now | Evidence and reason to reconsider |
| --- | --- | --- |
| Original plywood frame | Preserve as reference; do not switch back solely for stiffness | Its sampled downward displacement was 0.36846 mm under the equal-property, fixed-floor 1.2 kN comparison. That does not establish real panel, glue, connection or floor resistance. Reconsider only with a feasible product-based construction case, not the displacement number alone. |
| Unextended and +50 mm shallow 2×8 | Preserve, not preferred | The +50 mm variant misses two cases of the stated moment screen; its minimum factor is 1.3947 against 1.5. |
| **Untied 2×8-foot100** | **Selected development baseline** | The +100 mm extension is the smallest tested passing extension, not a proven minimum. Its sampled downward displacement is 0.84622 mm on the finer bulk mesh. Retain until a defined mechanism or product constraint warrants a change. |
| +150/+200 mm shallow 2×8 extensions | Preserve as additional-reach contingencies | The current 96-case moment-only sweep does not establish a need to extend beyond +100 mm. A changed applicable load envelope could reopen that choice. |
| 2×10 and 2×12 | Preserve as contingencies, not upgrades selected now | Sampled downward displacements are 0.54483 and 0.38900 mm. No adopted serviceability limit or product-specific rim-resistance check establishes a need for deeper rims. |
| Z=100 and Z=275 side-tied variants | Preserve, but do not add ties solely for stiffness or tipping | Sampled fixed-floor displacement improves only 0.22–0.34%; added timber improves the rigid-body moment screen without enlarging the support polygon. Investigate Z=275 first for its connection layout if an audited unanchored comparison shows a useful spreading/slip benefit. |

These displacement figures are sampled at five loaded nodes in **different
whole-candidate geometries**, using isotropic equal properties, perfectly
bonded timber and fixed floor nodes without gravity. They are not peak stresses,
material-capacity rankings or direct predictions of unanchored board motion.
See [physical footprint comparisons](physical-footprint-results.md) and
[side-tie comparisons](tied-base-comparison.md) for original sources and limits.

The +100 mm moment screen has two distinct inventories: the drilled
timber-plus-angle case gives minimum factor 1.8138, while the undrilled
timber-only baseline gives 1.7143. Do not exchange their masses or treat either
96-case sensitivity sweep as a validated dynamic envelope. Both legacy
board-normal cases still require uplift in their separate screen. They remain
visible adverse cases, not discarded results.

## What should change before another construction iteration

**Legs:** prefer identified structural panels with a documented qualified
lamination process for the requested two-sheet construction. The actual-leg
study found 3.9223× the out-of-plane compliance without composite action
under even sharing, versus less than 0.04% in-plane change. This makes the
lamination/sharing/restraint assumption consequential; it does not quantify
strength loss or buckling resistance. If qualified lamination is impractical,
develop the separate mechanically connected, no-adhesive-credit route. If its
load introduction and lateral restraints cannot be made credible, evaluate a
separately designed factory-engineered leg with permitted cuts and holes.
[Actual-leg evidence](../fea/results/independent_leg_response/README.md).

**Backing joints:** replace the assumption that a generic front screw plus
the current rear angle is an adequate connection design. The screened
SDS/SDWS products do not fit the proposed same-envelope side-grain block's
required distances. Both tested block enlargements intersect every existing
rear angle. Produce one complete block/angle/bolt/front-fastener layout rather
than changing grain direction or block size alone. A suitable smaller-fastener
system or an applicable clip detail remains possible; none is selected by the
current fit screen. [Rib/batten evidence](rib-batten-detail.md).

**Materials:** identify the offered structural panels, lumber grade/species,
hardware and bonding process before assigning resistance. Retain the C-3 birch
reference, but do not treat appearance grade or E=7000 MPa as its structural
qualification. Supplier examples show why the scalar isotropic model is not
automatically conservative in shear. [Material evidence and procurement
packet](material-selection-recommendation.md).

## The next five steps, and what would change the recommendation

1. **Resolve applicable loading and intended-use boundaries.** Keep the sourced
   1.2 kN comparison, static-weight cases and exploratory dynamics distinct.
   Decide the applicability of the adverse normal directions, top/side-edge use
   and hold projections with the load-basis review. If the normal cases are
   required, the present footprint does not pass its own screen: evaluate a
   changed support arrangement, not deeper rims or floating ties as a cure.
   [Load/contact basis](load-contact-basis.md).
2. **Choose an obtainable leg/material route and specify one complete backing
   joint.** Obtain product data and an auditable lamination or mechanical
   connection specification. Check every rib station, bore/head/tool envelope,
   edge/end distance, panel screw and wiring relief. Switch that detail or leg
   route when its product rules, geometry or required behavior cannot be met;
   do not compensate with an unrelated member-size change.
3. **Qualify the unanchored contact model for the next question.** The 0.0625
   MORTAR run passes the unchanged global endpoint diagnostics, but local
   contact and actual floor behavior remain unresolved. Resolve local
   admissibility and relevant mesh/history sensitivity before relying on
   individual foot slip/opening or joint demands. Do not continue an indefinite
   increment search merely to make an already small residual smaller.
   [Contact refinement](full-frame-increment-refinement.md).
4. **Run a bounded load-path discriminator.** Compare the untied baseline and
   the Z=275 tie candidate, retaining Z=100 as a reference where useful. Include
   central and separate A12/K12 physical load patches, declared friction
   sensitivities and hold moments. Adopt ties only for a meaningful benefit
   beyond numerical sensitivity that their actual joints can supply. Persistent
   global sliding/tipping calls for a support/floor redesign; asymmetric or
   lateral leg behavior calls for a corresponding restraint/connection change.
5. **Compare product-based member and joint demand with resistance.** Qualify
   curved-section/interface demand extraction; check panels/inserts, legs,
   rims, connections and stability with their real material axes and details.
   Increase rim depth only if rim resistance or an agreed deflection limit
   governs. Follow the selected design with qualified review and a controlled
   physical verification plan before construction/use release.

These are defined next steps, not a claim that the incomplete connection,
contact or material work has already been done. The next numerical run should
answer one of these decisions; another generic bulk stiffness comparison alone
would not resolve the present design uncertainties.

## Evidence and completion boundary

The [decision status ledger](design-decision-status.md) retains the detailed
requirements and unresolved work. Original CAD/results, adverse outcomes and
new alternatives are separately named. Numerical controls, mesh/fixture
preflights and raw-output replay support the limited claims above; successful
solver termination alone is not used as acceptance. Source research separates
normative scope, manufacturer limitations and project assumptions.

This document closes the **research-to-development-recommendation decision**:
which candidate to develop, what to change next, why, and when to switch.
It does not close construction drawings, product selection, structural
validation or permission to climb. Those remain explicit downstream work,
rather than being silently relabeled as completed audits.

### Completion audit of the requested research objective

| Requirement | Evidence inspected and conclusion |
| --- | --- |
| Clear recommendation about which design to use or switch to | The alternative table selects untied 2×8-foot100 for development and gives mechanism-specific reasons and switch conditions. It does not select a construction-ready assembly. |
| Clear next steps | The five gates above identify load applicability, leg/material and joint choices, contact verification, the unanchored comparison, and product-based checks in decision order. |
| Preserve the original alternatives while testing new ideas | Original plywood/2×8/2×10/2×12 references and raw evidence remain separate from foot extensions, side ties and independent-ply studies. Source/geometry/result replay checks passed in the full suite. |
| Research whether assumptions are reasonable | The linked load, material, contact and joint studies distinguish sourced scope from exploratory inputs. Manufacturer checks identify concrete limitations; unsupported properties and adverse load cases are retained rather than declared acceptable. |
| Test and evaluate the claims, not just obtain solver completion | Analytical controls, actual-CAD preflights, mesh comparisons, global and per-ply equilibrium/energy audits, and archived-output replay support the stated numerical conclusions. Independent review checked the synthesis and primary material documents without finding substantial remaining errors. |

Final local verification on 2026-09-06: `uv run pytest -q` completed with
**456 passed, 1 skipped** in 435.54 seconds. The skipped Gmsh-dependent
`test_published_raw_equilibrium_replay_when_gmsh_is_available` was then run in
the existing `mini-moonboard-fea:box-v1` Docker environment and **passed**.
`uv run ruff check .` and `git diff --check` also passed. The full suite checks
repository behavior and evidence consistency; it is not physical validation
of the proposed structure. The available independent reviews are documented
with their limits; no fresh three-agent protocol or professional structural
sign-off is claimed.
