# PB06 center bottom-rail pair: detached full-section trial

Decision: **REVISE**, not a drilling or structural release. This is a
two-station geometry trial against the PB06 ten-block model, not a replacement
in the native model. Both legacy ML24Z/SDS duties remain present.

The two target stations are `clip_horizontal_bottom_left_2` and
`clip_horizontal_bottom_right_1`. Their actual members are the left/right
center principals and bottom rails. The trial borrows the ordinary full-section
139.7 × 57.15 × 300 mm timber cleat topology and four generic 6.35 mm
through-bolt axes per station from the PB03 family; there is no half-lap,
custom steel, or structural wood screw in the proposed replacement. Generic
washer, nut, and 40 mm tool envelopes are diagnostic, not purchased hardware.

The bounded screen checks both finished host members, the candidate cleats,
nominal bolt shafts and bores, modeled washer/nut seats, outward tool paths,
all ten existing PB06 blocks, the 66 fixed panel/kicker axes, 12 original frame
bolts, and the other retained legacy hardware. The first run found no
candidate-feature intersection with those protected axes or ten blocks, and
the panel/tool envelopes were clear. It did find two binding problems:

- The second rail bore at **each** station does not fully traverse both
  intended wood members in the actual CAD solids. A nominal axis cannot be
  treated as a usable drilled joint until this is corrected.
- The right candidate cleat intersects the existing `upright_side_cleat` by
  about 8.9 mm³. Tiny does not mean ignorable for a cut/drill plan.

The script also reports signed projected end/edge margins for both hosts and
cleats against a **conditional** 4D (25.4 mm) screening target, and checks a
25.4 mm nominal washer seat by projection. Those projections do not resolve
angled cut-edge distance, delivered bolt shank/thread geometry, washer grade,
wood bearing/yield modes, group action, or complete joint resistance. The
40 mm tool cylinders are a modeled removable-panel access check, not proof of
an installation sequence. Next trial should move the second rail axes inward
and remove the right-cleat interference while leaving the panel/kicker axes
and existing frame bolts fixed.

Reproduce with `python -m scripts.simple_pb06_horizontal_bottom_pair` in the
repository virtual environment. No drilling, cutting, purchase, fabrication,
or load rating follows from this trial.
