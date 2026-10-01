# Independent review: current-frame mesh source audit attempt 01

**Verdict: confirmed with scope limits.** The attempt01 finding is corroborated: for revision `led-clearance-2x6-runner-seated-blocks-v1`, the pinned sources contain a provenance-verified ordinary-joint patch mesh, not a full-frame mesh and not a complete frame-to-solver body, element, node, and DOF map. The patch's wood identities join to three of the 50 current full-frame members. The other 47 are uncovered by this mesh.

I reran the supplied `verify_source_pins.py` and `sha256sum -c SHA256SUMS`; both passed. Separately, I rehashed all 101 source-pin records and independently joined the attempt04 member manifest to the member-solids descriptor and on-disk STEP files by member ID, kind, path, byte size, STEP SHA-256, shape-summary SHA-256, and source-shape fingerprint. All 50 rows matched. I parsed the mesh deck's node block and each C3D10 element set and compared the actual IDs and connectivity-derived body node sets against `mesh.json`: all 19 body records, 57,643 element IDs, and 116,162 node IDs agreed, with no duplicate body IDs or unused deck nodes.

The 50 joined current members comprise 20 timbers, 24 candidate blocks, and six plywood panels. The patch contains three wood bodies—`bottom_center_right_cleat`, `base_rail_bottom_right`, and `base_principal_center_right`—plus 16 physical-metal bodies on four local bolt axes. Its remaining uncovered identities are 18 timbers, 23 candidate blocks, and six panels. The four local axes do not stand for the 92 candidate bolt axes or the 12 retained frame-bolt arrangements.

Patch-level port records cover 43 nodes each at the local rail and principal ports and provide a six-coordinate projection over each port's 129 translational components. Their control deck describes section-coordinate projection equations, not rigid port ties; the cleat remains free. These records and the local nut-coupling inputs are frozen inputs, not a full-frame DOF or load-transfer map and not a solver response. The full-frame adapter has eight null top-level solver maps and null solver IDs for all 50 body bindings. The 778-row mass/topology map declares `GEOMETRY_TOPOLOGY_MAP_ONLY_NO_REDUCED_DOF_OR_TRANSFER_MAP`. Six current load cases and their datums exist as revision-bound source contracts, but adapter `load_ids` remains null, so they do not supply full-frame solver loads or responses.

The historical `fea/results/current-frame-response.json` names `no-shoes-development`, says workspace geometry sources do not match, and sets `qualified_for_design` false. Its pinned native archive has the same legacy identity in the cycle-12 input and report, both also unqualified. These files do not establish results for the reviewed revision.

The audit's readiness, acceptance, solve, and release flags remain false. The patch mesh status is explicitly `VERIFIED_C3D10_CURRENT_PATCH_MESH_ONLY_NO_SOLVER`; its `accepted`, `solved`, and `native_solve_run` fields are false. This review verifies recorded provenance and mesh bookkeeping only. It does not rebuild CAD, remesh, invoke a solver, validate materials or contact, establish full-frame load transfer, or qualify a design.

## Reproduction

From the repository root:

```sh
python3 docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-frame-mesh-source-audit-attempt01/verify_source_pins.py
sha256sum -c docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-frame-mesh-source-audit-attempt01/SHA256SUMS
```

`review-record.json` records the independent checks, fail-closed state, scope limits, and source artifact hashes. `SHA256SUMS` covers this review packet's README and JSON record.
