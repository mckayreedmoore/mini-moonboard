# PB-02 post to header: two bolts at each serial face

One bounded bolted solid-wood corner-block revision has a nominal collision fit and positive
conditional 4D/7D placement margins at the latest PB-02 tolerance pose. This
is a geometry result, not a joint rating or drilling instruction.

The probe tests six named variants: the reference block with trial second
bolts, a longer block, relocated pairs, a 5-mm-forward post pair, a balanced
header pair, and a shorter block intended to admit an ordinary 8-in bolt
stack. It does not optimize continuously. The principal-side block,
header, shifted right post, backer, other cleats, panel outlines, and all 66
fixed panel/kicker axes retain the tolerance-pose geometry.

The shortest fitting trial block is one rectangular piece, X=177.65…266.55,
Y=−175.7…−86.8, Z=95…238.9 mm (88.9 × 88.9 × 143.9 mm), with grain in Z.
Its lower face is 15 mm below the earlier reference block; its upper face still meets
the original header underside. Ordinary square cuts suffice. It has no
pocket, lap, or steel fitting.

| Serial face | Two full bore axes, global mm | Nominal wood grip |
| --- | --- | ---: |
| Post to block, X direction | Y=−145; Z=145 and 180; X=88.75…266.55 | 177.8 mm each |
| Block to header, Z direction | X=208.35 and 235.85; Y=−130; Z=95…277 | 182 mm each |

The first post/block bolt moves from Y=−150/Z=160 to Y=−145/Z=145 mm; the
first block/header bolt moves from X=222.1 to 208.35 mm. The other bolt
centers also change. These are **changed bolts**, not inherited
acceptance. The probe rebuilds and checks their full bores and exposed-end
envelopes together with both second bolts and all six otherwise inherited
bores. The post-low/high, upright, link, header/principal-block, and
principal-block/principal axes remain at the tolerance pose. There are ten
full intended bores in this screen.

The post pair has 35 mm center spacing (+9.6 mm over conditional 4D). The
balanced vertical pair has 27.5 mm spacing (**+2.1 mm** over 4D). All measured
box-boundary 4D transverse and 7D grain-end markers are positive. The
tightest conditional edge/end reserve is **+5.3 mm**: the post bolts have
30.7 mm to the post rear Y edge, and the first vertical bolt has 30.7 mm
to the block left X edge, each against 4D=25.4 mm. The lower post bolt
has 50 mm to the new block bottom (+5.55 mm over 7D=44.45 mm); the upper
has 58.9 mm to the post/block top grain ends (+14.45 mm).
The earlier relocated-pairs variant had only +0.3 mm minimum; moving only
the post pair forward raised that to +1.95 mm. The balanced trial improves
edge/end reserve but narrows its vertical bolt-pitch reserve. Raising the
block bottom from Z=75 to 95 mm and moving the lower post bolt to Z=145
retains the same 5.3-mm minimum edge/end marker while shortening both
vertical grips by 20 mm. These are
nominal distances without a demonstrated cut, drill, or stock tolerance
budget. The header's grain-X ends are remote;
the principal's oblique grain/end remains unclassified.

The passing CAD screen reports full intended reception for all ten bores,
full bearing for 20 modeled washer disks, and no positive-volume wood/wood,
wood/screw, unintended bore/wood, bore/bore, bore/screw, washer/wood,
washer/screw, exposed hardware, or socket-body collision. The socket body is
the documented 7.8486 mm radius × 24.511 mm length envelope. Straight
insertion is checked from both ends of every bore with the 3.65 mm bore
radius and an illustrative 35 mm extra length; each has at least one clear
direction. The two new X bolts insert from the block's right face; both new
vertical bolts have clear modeled directions from either end. Other-bolt
hardware is included in the insertion screen. The fixed 48 panel and 18
kicker axes remain clear; both inner kicker edges remain supported. The
unchanged tolerance-pose screen supplies their receiver checks.

The 182 mm vertical wood grip leaves **21.2 mm** on a nominal 8-in
(203.2-mm) bolt before washers, nut, tip and thread requirements. That is
only a length arithmetic lead; no exact 8-in SKU stack is selected. The
earlier 202-mm grip left just 1.2 mm and cannot use an 8-in stack under
ordinary washer/nut allowance assumptions.
The 35 mm insertion extension is only a geometric allowance. Delivered bolt
length, thread start, washers, nut engagement,
actual insertion order, socket drive and swing, and installed access need a
separate hardware check. The 5.3-mm minimum edge/end and 2.1-mm bolt-pitch
reserves have not been propagated through cut/drill, bore-size, or delivered
stock variation. The corner block's two vertical bores run along its
grain and the contact faces' force/moment paths, net section, splitting,
bearing, bolt group action, and full joint resistance have not been solved.
Conditional 4D/7D comparisons are placement markers, not an NDS verdict.
No native solve, strength claim, fabrication or drilling release follows.

Run `.venv/bin/python scripts/simple_center_post_header_two_bolt_probe.py`.
Run the focused check with `.venv/bin/python -m pytest -q
tests/test_simple_center_post_header_two_bolt_probe.py` and lint the two new
Python files with `.venv/bin/ruff check`.
