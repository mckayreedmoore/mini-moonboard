# PB-02: one rectangular side-cleat header/post trial

**Nominal geometry clears; the displaced header/right-post duty remains open.**
This is one alternative to the front Y-bolt and recessed/deep-header failures
for `clip_split_header_center_right`. It inherits the right-only shifted-post
and link-edge pose. It does not address `clip_split_base_center_right`, select
hardware, establish strength, or release drilling.

## Single pose

Keep the original full-length header at X=−1219.2…1219.2,
Y=−175.7…−36, Z=238.9…277 mm: its 38.1-mm Z depth and front kicker
contact face are unchanged. Keep the right post at X=88.75…177.65,
Y=−175.7…−86.8, Z=0…238.9 mm, and the inherited backer, rear cleat,
upright-side cleat, post/link/upright bolts, climbing surface, both inner
kicker edges, and all 66 fixed panel/kicker screw axes.

Place **one solid rectangular cleat** immediately beside the post and below
the header: X=177.65…266.55, Y=−175.7…−86.8, Z=110…238.9 mm.
Assume its grain runs in Z. Its left face contacts the post; its flat top
contacts the header underside. This is a full-section block, with no
bracket, half-lap, recess, or second cleat. Nominal stock dimensions are
88.9 × 88.9 × 128.9 mm; an actual one-piece blank and grain orientation
would need checking.

Two illustrative ordinary 1/4-in (6.35-mm) through-bolts carry the proposed
serial route, with metal nuts and washers:

| Joint | Bore center and full span (mm) | Intended wood |
| --- | --- | --- |
| Post → cleat | Y=−150, Z=160; X=88.75…266.55 | 88.9-mm post + 88.9-mm cleat |
| Cleat → header | X=222.1, Y=−130; Z=110…277 | 128.9-mm cleat + 38.1-mm header |

Both bolts exit on X or Z faces. No nut, washer, or tool is placed at the
installed kicker front Y face. The old two post/rear-cleat bolts remain at
X=140, Z=110/190; this trial does not remove or relocate them. The
illustrative 7.30-mm bore is 0.95 mm over the nominal bolt diameter, within
the [official 2024 NDS Chapter 12, §12.1.3.2](https://awc.org/wp-content/uploads/2026/08/AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-%E2%80%93-Dowel-type-fasteners.pdf) bolt-hole
interval. It is an occupied geometry envelope, not a shop bit callout.

## Nominal checks

Both complete bores are received 100% by their named pair of members. The
new cleat has no positive-volume overlap with other modeled wood. Neither
new bore intersects other wood, the other new bore, the inherited four
post/link/upright bores, or any of the 48 panel and 18 kicker screw
envelopes. The new X- and Z-axis bores have 20 mm between axes and 12.7 mm
between illustrative bore walls. The new post X-bore and inherited Y-bore
at Z=190 have 30 mm between axes and 22.7 mm between bore walls. The cleat
itself also misses all
66 fixed screw envelopes. Each of four illustrative 20-mm-diameter washer
disks has full modeled wood bearing; four 10-mm-radius × 5-mm outward
hardware cylinders and four 20-mm-radius × 20-mm straight outward tool
cylinders miss modeled wood and fixed screw envelopes. In particular, the
vertical bolt's upper and lower seats and the transverse bolt's left and
right seats do not require the blocked kicker front face.

Both inner kicker edges retain direct support. The four fixed center kicker
screws retain full modeled receiver portions. All ten `kicker_header_*`
axes retain their original 0.7125 modeled shaft fraction in the header,
unlike the recessed-header trials. The other 52 fixed axes are unchanged;
the new wood and bores have been screened against all 66, but their
connection strengths have not been requalified. Existing baseline
connections are inherited as geometry, not accepted as a complete assembly.

## Conditional 2024 NDS placement and mechanical gate

For D=6.35 mm, [official 2024 NDS Chapter 12, Tables 12.5.1A–C](https://awc.org/wp-content/uploads/2026/08/AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-%E2%80%93-Dowel-type-fasteners.pdf)
placement markers are 4D=25.4 mm at a perpendicular-to-grain loaded edge,
1.5D=9.525 mm at an unloaded edge, and 7D=44.45 mm at a softwood loaded
end under tension parallel to grain for the full end-distance factor. Actual
load direction, grain and loaded-edge classification, and member role must
be established before applying these as requirements.

| Centerline distance | Nominal mm | Conditional observation |
| --- | ---: | --- |
| Post bolt, post and cleat Y edges | 25.7 / 63.2 | Rear side only 0.3 over 4D |
| Post bolt, post Z ends | 160 / 78.9 | Both over 7D if applicable |
| Post bolt, cleat Z ends | 50 / 78.9 | Both over 7D if applicable |
| Vertical bolt, cleat X edges | 44.45 / 44.45 | Both over 4D marker |
| Vertical bolt, cleat Y edges | 45.7 / 43.2 | Both over 4D marker |
| Vertical bolt, header Y edges | 45.7 / 94 | Both over 4D marker |
| Vertical bolt, header grain-X ends | 1441.3 / 997.1 | Remote from ends |

The transverse post bolt crosses side grain in both vertical-grain members.
The inherited Y-axis post bolt at Z=190 is **collision-clear only** relative
to the new X-axis post bolt. Their 30-mm spacing and 22.7-mm bore-wall gap,
and the 12.7-mm gap between the two new bores, do not establish applicable
NDS bolt spacing, group action, net section, cross-grain tension, or
splitting resistance. This is not an accepted complete post connection.
The vertical cleat/header bolt crosses the header grain but runs **along the
cleat grain and enters its end grain**. The tabulated edge/end distances
alone do not qualify its end-grain dowel bearing, splitting, axial tension,
washer bearing, or combined loading. Signed forces and eccentricity at both
interfaces are missing. A single bolt at each contact face also has no
demonstrated moment path; face contact or unverified friction cannot be
counted as one. The complete NDS lateral/end-grain treatment, net sections,
local bearing, bolt bending/yield, and connection strength are therefore
open. The previous clip's proxy forces are not demands for these bolts.

## Conditional vertical-bolt stack

The vertical bolt has 167 mm (6.575 in) of nominal wood grip. With an
illustrative *combined* 0.13 in for two washers, a 0.25-in nut, and the nut
above the header, the arithmetic is:

| Under-head length | Tip past nut | Top face to tip | Stack issue |
| --- | ---: | ---: | --- |
| 7 in | 1.148 mm (0.0452 in) | 9.149 mm | 0.122 mm short of even a provisional 0.05-in complete thread past nut |
| 8 in | 26.548 mm (1.0452 in) | 34.549 mm | Tip projects 14.549 mm beyond the original 20-mm top tool cylinder |

The 8-in top-shaft envelope, illustrative washer/nut cylinder, and extended
34.549-mm straight tool cylinder have no positive-volume collision with
modeled wood, installed panel/kicker solids, or fixed screw envelopes. This
does not establish wrench swing, tool reach, panel assembly access, or a
selected stack. For an *illustrative* 8-in bolt with only 1 in of threads
starting 7.00 in from the head, the nut bearing plane at 6.7048 in falls
0.2952 in before full thread; that pattern cannot clamp this nominal grip
and washer stack. A different long-thread pattern could change the result.
The [single-piece Everbilt 800696 8-in
listing](https://www.homedepot.com/p/204281626) and
[single-piece Everbilt 807396 7-in
listing](https://www.homedepot.com/p/204281599) each describe 6-in thread
length. The hypothetical 1-in-thread pattern above is **not** a claim about
either SKU. [Prime-Line 9058802](https://www.primelineparts.com/hex-bolts-1-4-in-20-x-7-in-a307-grade-a-zinc-plated-steel-10-pack/)
is another nominal 7-in retail lead. Delivered thread root/start, usable
shank, nut engagement, and stack fit remain unverified. No bolt is selected;
the post X-bolt stack is also unresolved.

**Disposition:** a bounded, nominal geometric lead only. Shifting the post
bolt from Z=170 to 160 raises the inherited upper-post-bolt axis spacing
from 20 to 30 mm while retaining 50 mm at the cleat's lower grain end.
Moving its Y from −150 to −140 would raise rear-Y edge distance from 25.7
to 35.7 mm, but the left 20-mm-radius straight tool then intersects the
backer by 1,760.56 mm³. That move also leaves only 2.7 mm between the two
new bore walls. Bores, screws, washer seats, and shorter hardware envelopes
still clear. Keep Y=−150. Its 0.3-mm conditional rear-Y 4D
reserve and modeled straight-cylinder access have no tolerance allowance.
Actual wood size, end-grain condition, hardware stack, shank/thread grip,
bolt length, washer/nut dimensions, wrench swing, assembly order, and
removal access require physical verification. No fabrication, cut, drill
coordinate, rating, or selected header/right-post load path follows.

Reproduce with `.venv/bin/python scripts/simple_center_header_post_side_cleat_probe.py`,
`.venv/bin/python -m pytest -q
tests/test_simple_center_header_post_side_cleat_probe.py`, and
`.venv/bin/ruff check scripts/simple_center_header_post_side_cleat_probe.py
tests/test_simple_center_header_post_side_cleat_probe.py`.
