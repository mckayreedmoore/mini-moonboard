# PB03 service-rail geometry core

Status at `1b027d13`: **geometry gates pass; development only.** The PB03
adapter replaces these eight historical angle duties:

- `clip_horizontal_lower_left_2`;
- `clip_horizontal_lower_right_1`;
- `clip_horizontal_lower_left_1`; and
- `clip_horizontal_lower_right_2`;
- `clip_horizontal_upper_left_1`; and
- `clip_horizontal_upper_right_2`;
- `clip_horizontal_bottom_left_1`; and
- `clip_horizontal_bottom_right_2`.

The stations are constructed independently from their actual kerf-right
members. The right service rail is 3.175 mm shorter than the left; no mirrored
coordinate shortcut is used. The six outer stations join the lower, upper, and
bottom rails to `base_side_left` and `base_side_right` at their coincident
physical butt faces. Each station receives one 300 mm solid timber corner block
and four complete generic through-bolt stack envelopes. The outer upright
stacks have a 228.6 mm illustrative wood grip; the outer rail stacks have a
95.25 mm illustrative wood grip. The upper rail bores use a 125 mm offset to
clear the lower-pair hardware and tool paths. Each upper block has 86.9 mm of
actual-shape clearance from the lower block on the same side.

The bottom-outer pair uses an 80.159 mm rail bore offset and was screened
against all 66 fixed panel/kicker axes. Each bottom block has 1018 mm nearest
clearance to an existing PB03 block.

The screen checks block contact, full 7.5 mm bore occupancy, finished panels,
unrelated timber, all 66 fixed panel/kicker axes, every bore pair, every stack
component, and outward tool paths. It removes exactly eight legacy angles and 48
SDS axes. Current partial-frame inventory is:

- 14 legacy angle stations;
- 84 legacy SDS axes;
- eight PB03 timber blocks;
- 32 PB03 through-bolt stack envelopes;
- 194 total connections; and
- 44 bolt-kind connections.

The live V4 viewer is current with this inventory. It hides the eight replaced
angle solids and their 48 SDS visuals, and shows all eight actual 300 mm blocks
and all 32 five-component stack envelopes. PB02 remains unchanged at ten bores,
ten stacks, one outward-shifted center support, both supported inner kicker
edges, and geometry fingerprint
`4ef3ff0376b4c49142c8a1bc347270da024852e4554cfc4e549b6cafab63dccb`.

The 228.6 mm outer grip is a geometric stack input, not a selected bolt length.
Exact retail bolts, washers, nuts, threads, orientations, and tolerances remain
unresolved. No resistance result has been transferred to the PB03 service-rail
stations. No drilling instruction, fabrication release, or structural acceptance follows
from this slice. Fourteen legacy stations remain, so this is not the final
frame.
