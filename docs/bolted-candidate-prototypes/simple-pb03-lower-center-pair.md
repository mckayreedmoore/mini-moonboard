# PB03 first lower-center pair

Status: **geometry gates pass; development only.** Commit `f8ca163` replaces
these two historical angle duties in the PB03 adapter:

- `clip_horizontal_lower_left_2`;
- `clip_horizontal_lower_right_1`.

The stations are constructed independently from their actual kerf-right
members. The right service rail is 3.175 mm shorter than the left; no mirrored
coordinate shortcut is used. Each station receives one 300 mm solid timber
corner block and four complete generic through-bolt stack envelopes.

The screen checks block contact, full 7.5 mm bore occupancy, finished panels,
unrelated timber, all 66 fixed panel/kicker axes, every bore pair, every stack
component, and outward tool paths. It removes exactly two legacy angles and 12
SDS axes. Current partial-frame inventory is:

- 20 legacy angle stations;
- 120 legacy SDS axes;
- two PB03 timber blocks;
- eight PB03 through-bolt stack envelopes.

The V4 viewer hides the two replaced angle solids and their 12 SDS visuals. It
shows both actual 300 mm blocks and all eight five-component stack envelopes.
PB02 remains unchanged at ten bores, ten stacks, one outward-shifted center
support, both supported inner kicker edges, and geometry fingerprint
`4ef3ff0376b4c49142c8a1bc347270da024852e4554cfc4e549b6cafab63dccb`.

No exact retail bolt, washer, nut, thread, orientation, tolerance, resistance,
drilling instruction, fabrication release, or structural acceptance follows
from this slice. Twenty legacy stations remain, so this is not the final frame.
