# Current leg-response mechanism audit

The saved assembled-frame result has a mechanically explainable leg-joint moment. This independent code and free-body audit found no sign, bolt moment-arm, coordinate-transformation or explicit foot-clamp error that would justify discarding it. It does not establish an installed joint stiffness or a climber rating.

The audit uses the refined upper-left A12 case in [the current response report](current-frame-response.md): 150 lb multiplied by two vertically, plus 300 N rearward. It reads the saved forces and native final input; it does not rerun the solver or repeat the full repository tests.

## Independent arithmetic

Four bolt positions give a centroid of `(-1219.200, 984.612524, 1608.537416) mm`. Summing their actual forces on the left leg and taking cross products about that centroid gives:

- Force: `(-38.536, +513.096, -2031.292) N`.
- Moment: `(-219.923495, +14.745951, +6.926741) N·m`.

A second calculation uses only the saved floor resultant and the leg's own gravity. The floor contributes `(231.115290, -13.648043, -6.926740) N·m` about the bolt centroid; gravity contributes `(-11.191661, -1.097893, 0) N·m`. Their balancing joint moment is `(-219.923629, +14.745937, +6.926740) N·m`. The X-moment difference between the two independent sums is 0.000134 N·m, consistent with saved-output rounding.

The bolt group's squared in-plane radii sum to 7,400 mm². A separate rigid-group arithmetic check distributes the same resultant equally and superposes the in-plane moment contribution `F_i = F/4 + (M_x/J)(e_x × r_i)`. This gives a peak lateral bolt force of 1,845.8 N, compared with 1,816.1 N in the finite-element result. Their 1.6% difference shows that the peak is consistent with the compact pattern and its turning moment. This arithmetic check assumes equal lateral stiffness and rigid joined faces; it verifies the force scale, not connection resistance.

## Implementation inspected

- `current_response_model.directional_connector` constructs an orthonormal local axial/transverse basis. `current_response_run.physical_forces` applies its transpose to recover physical global forces. These transformations are mutually consistent.
- The bolt connector is placed at the common timber interface, including the modeled washer offset. Both members have independent interpolated displacement nodes there. Springs do not rigidly tie the two timber members together.
- `Structure.attachment` preserves affine geometry and rejects attachment stations outside the retained member length. Offsets through the timber thickness transmit the expected eccentricity.
- The foot uses four unilateral normal corner contacts and one conditional no-slip translational connection at the bevel center. It has no prescribed rotational clamp. Normal contacts can open, and an entirely lifted foot loses its tangential restraint.
- The level bevel uses a plane-section endpoint approximation. Its finite bearing width can transmit a contact moment; this differs from an ideal point hinge.

In the audited case, the left foot's normal center of pressure is at `y = 1490.349989 mm`, the rear edge of its actual `1345.668041–1490.349989 mm` footprint. This is the solved active state of the four-point contact idealization, not an imposed full-foot endpoint-pressure load. A point reaction at that edge is not a qualified finite physical pressure distribution: real bearing occupies finite area and can compress locally. No local pressure capacity is established by this audit. The moment cannot be removed merely by relabeling the foot or bolt group as a pin. An ideal-pin alternative would require a corresponding physical connection or support detail, followed by an assessment of that changed assembly; switching only the analytical boundary condition would not describe the current frame.

## Limits and consequence

The directional spring values remain published analogies, described in the [material basis](current-response-material-basis.md). The model does not represent bolt-hole clearance, initial seating slip, contact friction between the two timber faces, preload, or progressive wood embedment. These are limitations of the response idealization; this audit does not turn them into new owner testing prerequisites. The existing half/double connector-stiffness cases already show that the conditional bolt comparison remains above one within that evaluated range. Uniformly scaling all connections does not independently vary the leg joint's stiffness relative to the frame.

The appropriate next design work is a connection change assessed with the assembled model, or a specific substantiated revision to its joint law. Simply assigning zero joint moment, increasing steel grade while wood bearing governs, or treating a software test pass as a connection pass would not resolve the current finding. Preserve the original single-2x6 candidate and its evidence while evaluating any alternative.
