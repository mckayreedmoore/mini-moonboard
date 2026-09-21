# PB-02 post/header vertical pair: ordinary-retail axial stack screen

Status: **202-mm wood grip rejects a nominal 8-in bolt in this stack;
182-mm grip conditionally fits the inspected 8-in leads. No bolt, purchase,
strength result, or drilling is selected.** Each of the two vertical axes in
the [two-bolt block probe](simple-center-post-header-two-bolt-probe.md) has the
same wood-only grip. Its `shorter_8in_trial` independently screens the
182-mm grip as **nominal CAD geometry** with all protected screw axes; that
does not verify purchased dimensions, installation, or joint strength.

## Public source facts, checked 2026-09-20

Only public Home Depot/Lowe's listings and their manufacturer responses were
searched. [Home Depot Everbilt 800696, 1/4-20 × 8-in hex bolt][everbilt]
is an ordinary single-bolt lead. Its listing reports **6 in of thread**;
the 6-in statement also appears in a [Home Depot supplier Q&A for the
corresponding 25-pack][everbilt-qa]. The product page does not give a
controlled first complete thread or under-head delivered length.
[Home Depot Prime-Line 9058821, 1/4-20 × 8-in
hex bolt][prime] is a 10-pack; its manufacturer answers on that retailer
page report **1 in of thread**. Neither thread-length statement establishes
complete usable thread at the inferred axial start. The Lowe's
[Hillman 490687 1/4-in washer][washer] lists **1/16-in thickness** and
5/8-in OD. The Lowe's [Hillman 490622 1/4-20 nut][nut] lists thread size,
but no usable nut height was found. These listings do not prove washer
bearing capacity, nut engagement, or delivered dimensional tolerances.

The bounded retailer search for ordinary 1/4-20 hex bolts at 9, 10 and
12 in did not establish a specific Lowe's/Home Depot lead with both length
and usable thread placement. That is a search limit, not proof no such bolt
exists. Threaded rod, lag screws, other diameters and custom steel are not
substitutes in this screen.

## Assumptions and limiting planes

The [reproduction script](../../scripts/simple_center_post_header_8in_stack_screen.py)
reuses [`evaluate_grip_interval`](../../scripts/simple_pb01_thread_stack_screen.py).
It takes length from the underside of the head. For **sensitivity only**, it
uses wood grip ±0.05 in, one washer each side at 0.050–0.075 in, nut height
0.20–0.25 in, and 0.25 in of required nominal tip beyond the nut. These are
neither product tolerances nor an installation rule. The nominal 1/16-in
washer falls inside the assumed interval. Thin washers and minimum grip give
the limiting nut-side bearing plane; thick washers, maximum grip and tallest
nut give the limiting projection. An inferred 2.0-in thread start for the
Everbilt and 7.0-in start for Prime-Line assumes their published thread
lengths end at the nominal tip. Neither is a verified first usable thread.

| Wood grip | 8-in tip margin at worst assumed stack | Seat margin, Everbilt / Prime-Line | Axial result |
| --- | ---: | ---: | --- |
| 202 mm (7.952756 in) | **−0.652756 in** (−16.58 mm) | +6.002756 / +1.002756 in | Fails length even before delivered variation |
| 182 mm (7.165354 in) | **+0.134646 in** (+3.42 mm) | +5.215354 / +0.215354 in | Passes assumed axial interval only |

For 202 mm, nominal 8 in exceeds bare wood by just **1.2 mm**. The assumed
worst stack needs **8.652756 in** under the head before any delivered-length
allowance. At minimum assumed grip and thin washers, the nut bearing plane
is already **8.002756 in**, beyond the nominal 8-in tip. The positive
thread-start comparison for that row cannot represent a seatable nut.
The length threshold is necessary, not a longer-bolt answer.
With the same hypothetical last **1 in** threaded, a 9-in bolt starts thread
at 8.0 in and has only **+0.002756 in** seating margin at minimum grip and
thin washers; a 10-in bolt starts at 9.0 in and has **−0.997244 in** seating
margin. These 9/10-in cases are patterns, **not identified retail products**.
A longer bolt needs both sufficient projection and usable thread starting no
later than the minimum-grip nut bearing plane, **8.002756 in** here. A
different verified thread length could change that outcome.

The 182-mm result leaves +3.42 mm of nominal sensitivity margin at the tip,
but the model assumes usable thread through the nominal tip and omits bolt
length tolerance, tip chamfer, thread runout, nut chamfer, washer compression,
and delivered wood variation beyond the stated interval. Actual shank and
root occupancy through the block/header shear planes are unverified.
No strength, group action, purchased-stack acceptance, or drilling conclusion
follows. Run `.venv/bin/python -m
scripts.simple_center_post_header_8in_stack_screen` to reproduce the values.

[everbilt]: https://www.homedepot.com/p/204281626
[everbilt-qa]: https://www.homedepot.com/p/questions/1-4-in-20-x-8-in-Zinc-Plated-Hex-Bolt-25-Pack-800690/204281625/2
[prime]: https://www.homedepot.com/p/310465152
[washer]: https://www.lowes.com/pd/Hillman-1-4-in-Zinc-plated-Standard-Flat-Washer-16-Count/3035987
[nut]: https://www.lowes.com/pd/Hillman-1-4-in-x-20-Zinc-Plated-Steel-Hex-Nut/1001265718
