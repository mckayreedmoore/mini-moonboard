# Compact four-bolt joint geometry preparation

This intermediate package extracts the actual zero-extension 2×6 spread leg
and its complete drilled rim from `leg_hardware_trial`. There is no crop: all
physical wood edges and existing machining remain unchanged. The four upper
bolt axes and their 11.1125 mm wood bores are retained in global coordinates.
The rest of the frame is omitted, without inventing remote restraints.

```sh
uv run python -m fea.compact_leg_joint_geometry --side left --output fea/generated/compact-joint-left
uv run pytest -q tests/test_compact_leg_joint_geometry.py
```

Each side exports 26 separate STEP bodies: two wood members, four integral
head/shaft bolt envelopes, four nuts and sixteen individual washers. Only each
bolt's integral head and shaft are fused. Nuts are not locked to shafts and
washers are not bonded together. The manifest records all four stacks, actual
planar adjacencies, wood grain axes, source snapshots and hashes, and hashes of
the complete original wood-part STEP files. Existing output directories are
rejected rather than overwritten. Source CAD face indices are not mesh labels.

**This is not solver-ready physical hardware geometry.** It deliberately
preserves the current trial's clearance envelopes, including an enlarged smooth
shaft and cylindrical head/nut outlines. Catalog body diameter, head/nut bearing
faces, fillets/chamfers and thread/runout geometry must be explicitly replaced
or idealized before a genuine joint contact solve. Full-body length does not
span all the wood merely because a smooth cylinder does: actual threaded/root
bearing in the stack remains unresolved. The smooth nut bore supplies no axial
thread retention. Washer dimensions are the trial's selected envelope case,
not measured stock; every washer remains an independent body.

The manifest lists these required replacements. No material properties,
contact law, friction, preload, applied loads, boundary conditions, mesh,
solver result or strength acceptance is assigned. Full-member extraction is
the shortest reusable preparation here; the old rigid-pin/leg-only coupon
does not represent this joint and is not reused as its mechanical model.

The [left-side preparation archive](../fea/results/compact-leg-joint-left-v1.tar.gz)
contains the 26 STEP bodies, geometry manifest and source snapshots. Both-side
geometry/export tests pass; this archived extraction is the left side only.

For a future displacement-driven submodel, the fixed-floor leg archives lack
the full rim-interface displacement field. Do not invent those displacements
or simultaneously impose connector forces and connector displacement jumps.
The pending compact floor-contact model requests the complete nodal field; if
it finishes and passes the applicable audits, evaluate using its remote rim
and foot fields. Otherwise obtain an output-expanded parent run with unchanged
mechanics. Either route still requires explicit remote-interface ownership,
body loads and a separate hardware contact idealization.

Verification: six preparation/export tests passed (25.00 s), covering both
sides, unchanged original members, four actual bores per member, separate
washer stacks, planar adjacency, source tamper rejection and exclusive STEP
exports with source/original-part hashes. Ruff passed. No native solve ran.
