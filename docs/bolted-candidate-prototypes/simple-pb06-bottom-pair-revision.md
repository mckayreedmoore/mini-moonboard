# PB06 bottom-center pair: bounded relocation

Decision: **REVISE**. This is a detached geometry screen, not a native PB06
change or a drilling release. The two original ML24Z/SDS duties remain in PB06.

The trial retains two full-section 139.7 × 57.15 mm timber cleats and eight
generic 6.35 mm through-bolt axes. It moves the second rail row from 110 to
95 mm from each butt and shortens each cleat's grain length from 300 to 295 mm.
Neither change resolves both original problems: the left second rail bore
still fails full-depth intersection with its intended wood, and the right cleat
still touches `upright_side_cleat`. A direct right-rail bore sweep confirms its
95 mm position is complete, so the failed pair gate identifies the left bore.
The side-cleat overlap lies near the
front/top edge of the block, not at the shortened end; a 5 mm length trim is
therefore ineffective. The complete result, including exact per-station
constraints, is reproducible with
`python -m scripts.simple_pb06_bottom_pair_revision` in the project venv.

The minimum signed projected host/cleat margin is 28.575 mm, above the
conditional 25.4 mm (4D) target; nominal 25.4 mm washer seating passes by
projection. Generic stack envelopes and 40 mm outward tool paths are reported
by the screen, but overall clearance still fails on the block intersection.
These are geometry
checks only. Purchased stock-length shafts, delivered shank/thread geometry,
washer/nut specifications, cut-edge distance, and complete joint resistance
are not verified. The source-bound screen retains all ten PB06 blocks, 66
panel/kicker axes, 12 original frame bolts, and the target legacy SDS axes.

No fabrication, drilling, purchasing, or structural rating follows from this
trial. The compact rail detail has priority over another bottom-pair variant.
