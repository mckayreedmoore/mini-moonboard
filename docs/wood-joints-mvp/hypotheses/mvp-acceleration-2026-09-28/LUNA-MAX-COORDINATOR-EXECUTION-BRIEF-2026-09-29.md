# Luna Max coordinator execution brief — 2026-09-29

This is a compact continuation brief for a fresh Luna Max coordinator on
`compact-floor-flush-wood-joints-development`, revision
`led-clearance-2x6-runner-seated-blocks-v1`. It organizes the next analysis
work; it does not authorize a mesh launch, solver run, candidate change,
fabrication, drilling, or climbing use. The controlling current status remains
the [root continuation note](root-continuation-note-2026-09-29.md), SHA-256
`60501849cdfb156c09e74ad6eff5cb9161180af2f0ef93fedeab5b0a312006d3`.

## Outcome to pursue

Complete a reproducible, source-bound six-case member/joint demand assessment
for this reviewed revision, with applicable resistance screens and an explicit
exception list. Do not treat solver convergence or a mesh as acceptance. The
MVP architecture comparison selected the conventional whole-frame response
plus code/product checks (Option B); the exact-hash reviewed demand register
found no path-complete member or joint demand subset in current evidence.

The immediate work is staged. First close a bounded geometry-only mesh gate
if its method preflight passes. In parallel, resolve the four separate
load-path gates below. Then freeze complete response inputs, validate the
specific methods on small known-answer models, and return the readiness
decision to the parent. The parent retains the exact freeze, readiness,
execution budget and authorization, serialized native runs, and final
validation.

## Verified checkpoint

- The current source packet contains 50 unique, one-solid STEP bodies: 20
  timber members, six panels/kickers, and 24 candidate blocks. The manifest,
  member bundle, and source audit agree on every ID, path, file size, SHA-256,
  summary hash, and shape fingerprint. The source audit verifier passes 101
  pins and 50 joins.
- The old patch mesh covers only 3 of these 50 current members; 47 identities
  are absent, and all full-frame solver mappings remain null. A successful
  geometry mesh would close only identity/geometry/discretization evidence.
- Gmsh 4.12.1 CLI and the pinned Docker image were reported available and
  rechecked by the parent. The Python API/module is not installed in the
  current shell. The exact-version source review is
  [mesh-method review attempt01](../evaluation-resume-2026-09-24/current-frame-mesh-method-review-attempt01/README.md),
  SHA-256 `1e0710a2dec697beda7c5aa2d8514b572adf5046a70422e0c0ae14c77e67dfe6`.
  It pins the official Gmsh 4.12.1 source archive and relevant API/example
  files; it confirms method availability but not a usable local Python
  runtime. The environment record is
  [attempt02](../evaluation-resume-2026-09-24/current-frame-mesh-preparation-environment-attempt02/README.md),
  SHA-256 `477a1c30bdca538ab63aac00d7c635f836cd86afc68b016e1eaf714de580c0ed`.
- c11 is an equilibrated `a12-rear` linear branch, not an accepted response:
  six compression-only contact checks fail (four active separations/tension,
  two inactive penetrations). Its one-run cap is spent; do not derive c12 or
  transfer any c11 contact, floor, member, or connector forces as demands.
- The A/B comparison, feasibility plan, and demand register passed
  exact-hash Luna Max reviews. The register is closed; do not recreate it.
  All 47 MVP-E criteria remain pending.

## Work sequence for the coordinator

1. **T09 method preflight — prepare, do not launch or mesh.** Read the root note,
   reviewed receipts, A/B comparison, demand register, and source-audit
   packet. Prepare an append-only T09 attempt plan with the exact 50 input
   identities and hashes. Pin the actual Gmsh executable/API route, OCC
   version, code hash, units, import and mesh options, element order, target
   size, and quality metrics before a full run. Prepare, but do not execute, a
   known-answer test plan using a small analytic solid and one representative
   source solid. It must check one imported volume, identity retention,
   expected bounds/centroid/volume, positive elements, and reproducible
   element extraction, with numerical tolerances and quality stop thresholds
   declared in advance. The exact 4.12.1 Python binding is currently absent;
   pin and review a usable API package or specify a CLI-only workflow. If the
   route or criteria cannot be made reproducible, report the blocker; do not
   silently switch tools or loosen thresholds.
2. **Parent smoke-test go/no-go.** Return the method review and test plan to
   the parent. The current continuation note authorizes no mesh generation.
   Only an explicit parent go/no-go may run the analytic/representative
   known-answer mesh test. A passing smoke test establishes only that the
   selected mesh route and checks work on those test solids.
3. **Parent all-50 go/no-go.** After the smoke result passes independent
   review, return the exact proposed full-run freeze for a separate parent
   decision. Only after that authorization may a worker mesh all 50 pinned
   solids. Keep bodies separate; never merge nodes or infer a joint.
   Return member-to-solid/element/node ownership maps, per-body geometry and
   quality summaries, and checksums for every output. Any identity,
   geometry, or quality failure stops the mesh-only attempt. No structural
   conclusion follows from a pass.
4. **Close four load-path gates independently where possible.** Maintain a
   cited evidence table with source, reviewer, status, and decision effect for
   each:
   - **Floor:** conditional no-slip support while bearing is an unverified
     assumption. c11's finite paired tangent springs are not the proposed
     ideal conditional-stick law. No friction, anchor, or verified-floor claim.
   - **Panel withdrawal:** derive all six outward panel-normal resultants and
     identify applicable resistance/stiffness evidence for the specified
     Hillman 42605 axes. Do not transfer SPAX or another screw's values. If
     relevant evidence is unavailable, keep the panel withdrawal path blocked
     and identify a bounded design/evidence option; do not invent capacity.
   - **Receiver/hardware path:** map panel and accessory loads through
     mechanically supported receiver/backer/carrier connections, including
     stiffness and force sharing. Source-mapped gravity wrenches are not
     mechanical carriers; record unresolved center-kicker/bearing paths.
   - **Beam self-weight:** derive distributed line loads for the beam/member
     response and verify section-force recovery. c11's solid-body gravity
     balance does not establish beam bending actions.
5. **Complete-input freeze gate.** Before any full-frame response, bind every
   member and panel to geometry, material/property axes, panel layup, section,
   connection/hardware law and receiver path, support model, own-weight and
   hardware loads, and each of the six exact load cases. Resolve solver body,
   set, and load mappings. Require per-case global and per-body equilibrium,
   and relevant known-answer checks for load distribution, contact/connection
   behavior, and output recovery. Obtain an independent exact-hash input/method
   review. List each missing or unsupported input explicitly; do not mark
   readiness true by inference.
6. **Return to parent for readiness.** The coordinator can prepare and review
   evidence, but the parent alone decides readiness, reserves the serialized
   run budget, authorizes native execution, and validates final six-case
   outputs. On a ready input freeze, the planned result is signed member
   `N, Vy, Vz, T, My, Mz`/deflection and joint demand envelopes per case,
   resistance screens, equilibrium checks, sensitivities, and exceptions.
   If a gate cannot be closed, return concrete missing evidence or a bounded
   required design change instead of running an incomplete case.

## Guardrails and stop conditions

Preserve the reviewed geometry, all previous candidates, source freezes,
false results, and other agents' working changes. Do not modify the selected
baseline or infer acceptance from historical passes. No c12, radial fixture,
source-clearance pilot, T02 coupon, solver substitution, geometry redesign,
physical inspection, floor test, or fabrication belongs to this brief. Stop
on contradictory instructions, a missing load path, an incompatible
delivered part, a failed adopted criterion, a source-hash mismatch, or a
known-answer/quality failure; report the affected operation and evidence.

## Source records

- [Root continuation note](root-continuation-note-2026-09-29.md)
- [Next coordinator plan](NEXT-COORDINATOR-PLAN.md)
- [Reviewed Option A/B comparison](option-ab-method-selection-2026-09-29.md),
  SHA-256 `d73dc9b2583c88b64fab4a8e61b1910dfbdb2881cc6dde629b30911a5425c76a`
- [Closed demand register](demand-coverage-register-2026-09-29.md), SHA-256
  `d745ca62f2fa66bf671227ed2089da8568d4237ae5e5a6180db773885f231072`
- [50-body mesh source audit](../evaluation-resume-2026-09-24/current-frame-mesh-source-audit-attempt01/README.md),
  SHA-256 `e323692e6a45a5c35a2c11567dd5da1a513bb90599b3df7abdcf1b938aac0410`
- [Current mesh environment observations](../evaluation-resume-2026-09-24/current-frame-mesh-preparation-environment-attempt02/environment-observations.json),
  SHA-256 `b4c8d6a021010e49b25e4b07e5e43893be6480cc44f4e024002e226ccb7420d1`
- [Exact Gmsh 4.12.1 method/source review](../evaluation-resume-2026-09-24/current-frame-mesh-method-review-attempt01/README.md),
  SHA-256 `1e0710a2dec697beda7c5aa2d8514b572adf5046a70422e0c0ae14c77e67dfe6`
