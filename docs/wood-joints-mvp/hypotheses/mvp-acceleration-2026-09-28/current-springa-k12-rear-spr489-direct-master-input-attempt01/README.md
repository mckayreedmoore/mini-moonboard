# K12-rear SPR489 direct-master input candidate

This input-only packet replaces only the two SPR489 q-carrier equations for
node 19800, DOFs 2 and 3. It derives the source scalar from the actual
twenty-node C3D20 interpolation rows for the two recorded owners, then maps
that scalar onto the unchanged carrier axis. The original projection points,
their source equations and the complete source inventory remain in the model
as provenance. The physical geometry, all source loads, carrier laws and
stiffnesses, 23/77 floor mask, and all other equations/cards are preserved.

The direct scalar equation is `q = p_second - p_first`, with each `p` the
normal projection of the weighted C3D20 master displacements. The emitted
carrier rows implement `Q_y = n_y*q` and `Q_z = n_z*q`; because the source
normal has `n_x=0` and unit length, the unchanged 100 mm SPRINGA axis gives
the same scalar extension. The actual serialized unit-force transfer from
those two rows is audited against the recorded first-owner `+n` and
second-owner `-n` force and source-point moment in `input-audit.json`.

The same 80-master scalar linear functional appears in the previously
validated direct-scalar known-answer coupon. This packet does not run CCX and
does not adopt forces or qualify the floor branch. The strict existing 711
response method needs the narrow SPR489-only source-coordinate path recorded
in `input-audit.json`: recover `source_q` and its output-token radius from the
direct physical-master functional. Preserve every other DAT, geometric SPRINGA
table, endpoint RF, action/reaction, floor, source-load, owner-wrench and
connector check.

The candidate model remains `frame_ready_for_native_run=false` and has no
mechanical-acceptance or force-adoption claim. See `deck-diff.patch` for the
two exact input-card changes and `source-pins.json` for its frozen sources.
