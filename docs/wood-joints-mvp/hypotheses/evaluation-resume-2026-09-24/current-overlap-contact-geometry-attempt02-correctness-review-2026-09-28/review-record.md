# Attempt02 overlap-contact geometry adapter: correctness review

Review date: 2026-09-28  
Subject: `scripts/wood_joint_wj08_overlap_contact_geometry_attempt02.py` and the frozen `current-overlap-contact-geometry-evidence-attempt02` packet  
Candidate/revision: `compact-floor-flush-wood-joints-development` / `led-clearance-2x6-runner-seated-blocks-v1`  
Verdict: **one non-blocking finding for the current frozen snapshot**. The packet reproduces, its current geometry claims remain bounded, and `overlap_contact` remains pending. The adapter has a false-rejection at the upstream classifier's numerical thresholds that should be corrected before reusing it with another geometry graph.

## Checks performed

- Ran `.venv/bin/python -m scripts.wood_joint_wj08_overlap_contact_geometry_attempt02 --verify`: **PASS_GEOMETRY_ONLY_CRITERION_PENDING**.
- Ran `sha256sum -c SHA256SUMS` from the frozen packet directory: **PASS, 3/3**.
- Read the pinned contact-graph and receiver-screen producers and compared their classification thresholds with attempt02's consistency checks.
- Probed two threshold-boundary graph copies in memory; no source, test, packet, queue, status, or goal files were changed.

## Scope boundary

The evidence stays a partial 50-node member/panel geometry inventory. It excludes connectors and fasteners, retains six unresolved pairs, and establishes no face ownership, contact law, active contact, force transfer, capacity, case response, or acceptance. I found no current frozen-output discrepancy and no claim-boundary promotion.

## Finding

### F-01 — Exact-zero checks reject states allowed by the pinned upstream geometry tolerance

Severity: **low for this frozen packet; actionable before a successor graph is consumed**. In `scripts/wood_joint_wj08_overlap_contact_geometry_attempt02.py:131-132` and `:163-165`, the finite-touch and zero-area/unresolved branches require `common_volume_mm3 == 0`; the unresolved branch also requires `finite_shared_planar_face_area_mm2 == 0` at `:163-164`.

The pinned upstream classifier in `scripts/wood_joint_current_receiver_screen.py:358-372` calls an overlap positive-volume only when `overlap > 1e-6 mm³`, and calls a shared planar area finite only when `shared_area > 1e-6 mm²`. Consequently, a graph row can validly remain `finite_planar_face_contact` with common volume up to and including `1e-6 mm³`, or remain `zero_area_touch_or_unresolved_contact` with shared planar area up to and including `1e-6 mm²`. The graph producer preserves those measured values in `scripts/wood_joint_current_contact_graph.py:510-524`; attempt02's exact-zero checks reject such tolerance-classified rows.

I confirmed the false rejection with in-memory copies of the pinned graph: setting an unresolved row's shared area to `5e-7 mm²` yields `Zero-area/unresolved pair has contradictory exact geometry fields`; setting a finite-touch row's common volume to `5e-7 mm³` yields `Finite-touch pair has contradictory exact geometry fields`. Both values remain within the upstream classification thresholds. The current six unresolved rows have zero shared area and zero common volume, so the frozen evidence and its reported classifications are unaffected.

Change the consistency checks to mirror the pinned producer's tolerances: allow unresolved shared area at or below `1e-6 mm²` and touch/unresolved common volume at or below `1e-6 mm³`, while continuing to reject values above those thresholds and inconsistent distances/states. Add focused boundary probes if the adapter is revised.
