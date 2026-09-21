# PB05 outer rail-bolt placement trial

This is a detached geometry and fixed-action sensitivity trial, not a drilling or
fabrication release. The source remains PB05's authenticated A12-forward report.
The six outer blocks remain 95.25 × 57.15 × 300 mm, with no pockets. The two
center stations, 66 panel/kicker screw axes, 12 original frame-bolt axes, and
14 legacy SDS duties remain unchanged.

The six first outer rail bolts currently sit 25 mm from the rail butt. Their
signed unloaded rail-end distance is 25 mm, below the 4D = 25.4 mm check. The
same bolts have a 25 mm loaded block edge, below the 4D = 25.4 mm check.
At both upper-outer stations there is another independent miss: the first
rail bolt's loaded block grain-end distance is 35.709 mm, below the
7D = 44.45 mm check. An X-only shift cannot cure that N-direction miss.

The bounded paired trial moves outer rail X offsets from `(25, 70)` to
`(26, 70)` mm, and moves only the upper-outer rail N row from 35.709 to
45 mm. It changes neither the upright bolts nor any source model. Under the
*old* A12 actions and signs, the expected tightest center-distance margins
are 0.6 mm at the rail end and block edge, and 0.55 mm at the upper block
grain end. These margins are not drilling tolerances. Moving holes changes
load sharing, so the old forces cannot be adopted as the revised demands.

The detached trial returned `ADVANCE_TO_NEW_NATIVE_SOLVE`: all 12 outer rail
bolts pass the signed end/edge check under the *old* A12 action directions,
and the exact geometry screen found no blocking intersection. Both focused
tests passed. Run `uv run pytest -q tests/test_simple_pb05_outer_rail_revision.py`
to reproduce the check. The screen covers the
existing full nominal 8-in upright and 5-in rail shafts, generic nut and
washer envelopes, 40-mm tool paths, block/rail/panel/frame intersections,
the other stations, and the retained inventory. The rail stack still lacks
SKU-controlled retail qualification. Regardless of this geometry result,
new native cases and complete joint checks are required. No drilling,
fabrication, or structural release follows from this trial.
