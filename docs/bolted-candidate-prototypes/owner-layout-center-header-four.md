# Four direct center-header corner duties at approved post X ±180 mm

Status: detached owner-layout trial only. The original 38.1 mm-wide center
posts move to X −199.05…−160.95 and 160.95…199.05 mm. Two separate
88.9 mm kicker backers retain the four fixed center kicker screw receivers
and inner panel-edge support. No backer-to-frame attachment or structural
backer capacity is asserted.

The four historical duties are `clip_split_header_center_left/right`
(header to moved post) and `clip_split_base_center_left/right` (header to
original principal). The candidate creates a direct two-bolt-per-face
corner block for each duty on the original bracket's outward X side.
It removes only those four angle/SDS groups from the proposed connection
set; the historical source remains unchanged. Neither duty routes through
the PB02 rear return, link, or backer.

The lower post blocks occupy Z 99.2…238.9 mm beside each moved post.
The upper principal blocks occupy Z 277…416.7 mm and a rear Y band
−175.7…−114 mm, chosen to avoid silently cutting the original bottom
rails. All four use 139.7 mm X projection. Nominal 1/4-in shafts,
7.5 mm bores, 25.4 mm washers, and 40 mm tool cylinders are generic
layout envelopes, not purchased hardware or drilling instructions.

The screen checks both actual host/header contact faces, complete bore
coverage, unrelated timber and other trial blocks, retained legacy
angles/SDS, and the shared protected finite solids: 142 T-nuts, 142
provisional 50.8 mm rearward hold-hole/protrusion envelopes, 132 lights,
131 wire solids, 66 panel screw shafts, and twelve frame-bolt shafts.
The four fixed kicker center screws are intentional backer receivers,
not proposed structural fasteners. Other delivered hold-bolt lengths,
wiring bends, fastener heads, tolerances, and joint resistance remain
unverified. No native load campaign or fabrication release follows.
The source is the kerf-right width adapter, not the official-width panel
packet or PB02's right-only moved-post/rear-return geometry.

Focused CAD result: **LAYOUT_ONLY_CLEAR** for the revised bolt centers.
Each lower post block has 12,419.33 mm² nominal contact on both its post
and header. Each upper principal block has 5,809.90 mm² principal-side
contact and 8,619.49 mm² header contact. All sixteen core bores fully
cross their two intended hosts. The four target groups remove 24 proposed
SDS axes; 120 other legacy SDS axes, twelve frame-bolt axes, and all 66
panel/kicker axes remain. The finite protected screen reports no hits.
No owner exception is needed for this nominal layout pose.

The first bolt-center trial failed: the lower principal cross-bolt tool
entered the header and the adjacent installed head/washer/nut. Moving only
the trial bolt centers cleared those exact intersections. The revised
geometry is still tolerance-sensitive: selected nominal reserves are only
0.906 mm to the bottom-rail Y envelope, 0.700 mm between a principal
cross-bore and a header-bolt bore wall, about 0.901 mm between one vertical
tool and the other washer, 1.000 mm at a rear washer edge, and 3.000 mm
between the lower cross-bolt tool cylinder and the header. These are not
fabrication tolerances, certified hardware clearances, or NDS end-distance
results. The lower principal cross-bolt is only 23 mm vertically above
the principal's cut start; its grain/load-dependent end-distance check
remains open.

Run `uv run python -m scripts.owner_layout_center_header_four` for exact
intersections and disposition. Any reported conflict needs owner direction;
the script does not change an existing frame member to clear it.
