# Four top duties: same-side compact corner-block layout

Status: detached layout trial, not a native solve or fabrication release.
The proposed candidate replaces only the angle/SDS groups at
`clip_single_top_left_1`, `clip_single_top_right_2`,
`clip_split_top_center_left`, and `clip_split_top_center_right`. Historical
ML24Z/SDS geometry is unchanged. The other legacy duties remain present.

Each trial uses a solid 139.7 mm local-N block behind the top rail, in the
local-T band beside its original upright. The blocks use one common section:
139.7 mm along X, 57.15 mm along local T, and 139.7 mm along local N. Two
through-bolts cross the upright/block face, and two cross the rail/block face.
Nominal 1/4-in bolts, 7.5 mm bores, 25.4 mm washer disks, and 40 mm tool
cylinders are generic CAD envelopes, not selected retail hardware or
drilling sizes.

The script screens the four actual source members, contact faces, complete
bores, basic washer/tool envelopes, original timber and panels, all 66
modeled panel screw shafts, twelve retained frame-bolt shafts, and retained
legacy angle and SDS solids. It reports every intersection above the model's
1 mm³ threshold. The source panel, frame, and 66 panel-axis positions are
not moved. This detached PB02-source screen does not silently include the
other developmental corner blocks being studied in parallel; their mutual
clearance is another explicit integration gate.

Result: **ADVANCE_GEOMETRY_ONLY** for this detached source, with no modeled
obstructions. All four blocks contact both source members (7,888.847 mm²
upright and 19,421.082 mm² rail per station), and all sixteen generic
through-bores cross both intended hosts completely. The minimum nominal
block washer-to-edge ligament is 22.3 mm. Outer upright wood grip is
228.6 mm, center upright grip 177.8 mm, and each rail/block grip 95.25 mm;
these do not establish available bolt lengths. The proposed inventory removes
24 target SDS axes, retains 108 other legacy SDS axes and twelve frame-bolt
axes, and preserves all 66 panel screw axes. There is no common-block
exception at this nominal modeled level; this is not a tolerance or
resistance verdict.

Physical hold bodies and T-nuts, unused hold holes, hold-bolt protrusions,
LED bodies and wiring, panel screw heads/driver access, and frame-bolt
heads/nuts/tool access have no complete protected 3D solids in this screen.
Their clearance is **unverified**, not assumed to be zero-length or clear.
The generic block bolts also lack exact retail selection, joint resistance,
durability, tolerance, and assembly-order checks. These remain stop gates
before any drilling or build claim. Barrel-nut expansion is outside this
trial.

Run `uv run python -m scripts.simple_top_same_side_four` for the exact
station-by-station layout disposition and collision quantities. The trial's
`ADVANCE_GEOMETRY_ONLY`, if reached, means only the modeled layout checks
passed; it does not waive the explicit unverified gates.
