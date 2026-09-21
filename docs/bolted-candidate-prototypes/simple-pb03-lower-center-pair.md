# PB03 lower-service core

Status: **geometry gates pass; development only.** Commits `f8ca163` and
`74fba89` replace these four historical angle duties in the PB03 adapter:

- `clip_horizontal_lower_left_2`;
- `clip_horizontal_lower_right_1`;
- `clip_horizontal_lower_left_1`; and
- `clip_horizontal_lower_right_2`.

The stations are constructed independently from their actual kerf-right
members. The right service rail is 3.175 mm shorter than the left; no mirrored
coordinate shortcut is used. The outer pair joins the lower service rails to
`base_side_left` and `base_side_right` at their coincident physical butt faces.
Each of the four stations receives one 300 mm solid timber corner block and
four complete generic through-bolt stack envelopes. The outer upright stacks
have a 228.6 mm illustrative wood grip; the outer rail stacks have a 95.25 mm
illustrative wood grip.

The screen checks block contact, full 7.5 mm bore occupancy, finished panels,
unrelated timber, all 66 fixed panel/kicker axes, every bore pair, every stack
component, and outward tool paths. It removes exactly four legacy angles and 24
SDS axes. Current partial-frame inventory is:

- 18 legacy angle stations;
- 108 legacy SDS axes;
- four PB03 timber blocks;
- 16 PB03 through-bolt stack envelopes.

The V4 viewer hides the four replaced angle solids and their 24 SDS visuals. It
shows all four actual 300 mm blocks and all 16 five-component stack envelopes.
PB02 remains unchanged at ten bores, ten stacks, one outward-shifted center
support, both supported inner kicker edges, and geometry fingerprint
`4ef3ff0376b4c49142c8a1bc347270da024852e4554cfc4e549b6cafab63dccb`.

The 228.6 mm outer grip is a geometric stack input, not a selected bolt length.
Exact retail bolts, washers, nuts, threads, orientations, and tolerances remain
unresolved. No resistance result has been transferred to the outer pair. No
drilling instruction, fabrication release, or structural acceptance follows
from this slice. Eighteen legacy stations remain, so this is not the final
frame.
