# PB-02 revised combined center: bounded stack and purchase-count screen

Status: **eight nominal axes have a conditional axial length basket; no hardware
selection, tool-access approval, strength finding, or drilling release.** This
sidecar applies only to the [shortened principal cleat and small-socket combined
pose](simple-center-combined-small-tool-probe.md), not the rejected
[original combined pose](simple-center-combined-cleats-probe.md). It counts the
four new and four inherited right-center 1/4-20 through-bolt axes. The 66
fixed panel/kicker screw axes are separate. No contact or purchase was made.

## CAD wood grips and axial interval

The [reproduction script](../../scripts/simple_center_small_tool_stack_cost.py)
reads all eight cylindrical bores from the current pose and checks each
cylinder's entire volume against its two intended CAD woods. Their bore
lengths are the **wood-only grips** below; the outward 5-mm hardware
envelopes, washer face disks and socket bodies do not add wood. Each axis is
one bolt with one nut and **two** provisional washers. Inch values are rounded
for display; the script uses the unrounded metric-to-inch conversion.

| Axis (new unless marked inherited) | Intended wood pair | CAD grip, mm (in) | Trial bolt | Worst seating / tip margin, in |
| --- | --- | ---: | ---: | ---: |
| `post_cleat` | shifted post + header/post cleat | 177.8 (7.0000) | 8 in | +5.050 / +0.300 |
| `cleat_header` | header/post cleat + header | 167 (6.5748) | 8 in | +4.625 / +0.725 |
| `header_cleat` | header + shortened principal cleat | **99.1 (3.9016)** | **5 in** | +3.702 / +0.398 |
| `cleat_principal` | principal cleat + principal | 109.05 (4.2933) | 5 in | +4.093 / **+0.0067** |
| `post_low` (inherited) | rear cleat + shifted post | 127 (5.0000) | 6 in | +4.800 / +0.300 |
| `post_high` (inherited) | rear cleat + shifted post | 127 (5.0000) | 6 in | +4.800 / +0.300 |
| `upright` (inherited) | principal + upright-side cleat | 127 (5.0000) | 6 in | +4.800 / +0.300 |
| `cleat_link` (inherited) | rear cleat + upright-side cleat | 94.9 (3.7362) | 5 in | +3.536 / +0.564 |

The existing [`evaluate_grip_interval`](../../scripts/simple_pb01_thread_stack_screen.py)
helper tests the **minimum** nut-side bearing plane against an assumed first
usable thread and the **maximum** plane against nut height and required tip
projection. Its formulas are `seat = grip_min + 2 washers − thread_start`
and `tip = bolt_length − (grip_max + 2 washers) − nut_max − projection`.
For this development screen alone, each CAD grip varies by **±0.05 in**;
each washer varies **0.050–0.075 in** around its listed 1/16-in nominal,
the nut height is **0.20–0.25 in**, and required tip beyond the nut is
**0.25 in**. The helper runs with the thinnest two washers for the seating
limit and the thickest two for the projection limit. The grip, washer and
nut intervals and tip rule are **assumed sensitivity ranges**, not published
SKU tolerances, measured dimensions or a fastening specification.
The 5- and 6-in fully threaded leads are given an **assumed** first usable
thread at 0.25 in under the head. The 8-in lead's listed 6-in thread length
implies a nominal 2.00-in start, used here only as an assumption about first
usable thread. No exact runout, usable final thread, bolt-length tolerance,
nut chamfer, washer variation or compression is included. The positive
seating margins for fully threaded bolts say little about root and wood
bearing. The helper assumes usable thread continues to the nominal tip.

The tightest axial result is `cleat_principal`: +0.0067 in (**0.17 mm**)
projection margin at maximum trial grip and 0.25-in nut height. A small
length, washer, nut or wood difference could reverse it. The original
combined pose's 141.1-mm `header_cleat` grip would give **−0.2551 in** tip
margin with its illustrated 6-in bolt under the *same* interval. Thus the
old four-6-in basket was only a nominal-span price illustration; it did not
pass this stack screen. A longer old-pose alternative is not priced here.

## Ordinary retail leads and what they establish

Public listings checked 2026-09-20. A listed size or price is a SKU fact;
the usable-thread starts and dimensional intervals above are study inputs.
Prices can vary by store and are neither a local quote nor stock confirmation.

| Lead | Published information used | Missing for an actual stack |
| --- | --- | --- |
| [Home Depot Everbilt 800676, 1/4-20 × 5-in zinc hex bolt](https://www.homedepot.com/p/204633308) | 5-in listing, $0.62 each; [retail source screen](simple-joint-retail-inputs.md) records “fully threaded” and A307 | First complete thread, delivered under-head length, root/shank, head and nut-side geometry |
| [Home Depot Everbilt 800686, 1/4-20 × 6-in zinc hex bolt](https://www.homedepot.com/p/204633312) | 6-in listing, $0.71 each; [original cost screen](simple-center-combined-cost-screen.md) records “fully threaded” | Same missing dimensions and thread-root bearing basis |
| [Home Depot Everbilt 800696, 1/4-20 × 8-in zinc hex bolt](https://www.homedepot.com/p/204281626) | 8-in listing, $0.94 each; [retail source screen](simple-joint-retail-inputs.md) records listed 6-in thread length and A307 | First complete thread, transition, body length and diameter, tip threads |
| [Lowe's Hillman 490622, 1/4-20 zinc hex nuts](https://www.lowes.com/pd/Hillman-1-4-in-x-20-Zinc-Plated-Steel-Hex-Nut/1001265718) | 12-pack, $1.98; thread pitch and finish listed | Nut height and full-engagement dimension; published “all-purpose” is no demonstrated grade |
| [Lowe's Hillman 490687, 1/4-in zinc flat washers](https://www.lowes.com/pd/Hillman-1-4-in-Zinc-plated-Standard-Flat-Washer-16-Count/3035987) | 16-pack, $1.98; listed 1/16-in thick, 5/8-in OD | Delivered thickness range, bearing/bending adequacy and cut-washer equivalence |

The nominal **7/16-in drive** of the 8-in bolt in the [source
screen](simple-joint-retail-inputs.md) is across flats, not a head-height,
socket-engagement or extension-clearance drawing. The 5/8-in washer OD is
also smaller than the probe's illustrative 20-mm-diameter washer bearing
disk; that disk did not qualify any washer. All three bolt leads need
product-specific dimensions and thread/root checks. Fully threaded 5/6-in
bolts put threads through wood, so nominal 1/4-in full-shank bearing or yield
credit is unavailable without the applicable root-based joint analysis.
The 8-in bolts also need a member-by-member thread-position check. No steel
or wood strength is inferred from A307 or from these positive length margins.

## Count and bounded cost change

The revised length basket is **three 5-in, three 6-in, two 8-in bolts; eight
nuts; sixteen washers**. At the displayed retailer prices, individual bolts
cost `3×$0.62 + 3×$0.71 + 2×$0.94 = $5.87`. Nut allocation is
`8/12×$1.98 = $1.32`; washer allocation is `16/16×$1.98 = $1.98`.
Illustrative hardware allocation is **$9.17**, while first checkout for
eight individually priced bolts, one nut pack and one washer pack is
**$9.83**. The [rejected-pose published basket](simple-center-combined-cost-screen.md)
was two 5-in, four 6-in and two 8-in bolts: $5.96 in bolts, $9.26 allocated
and $9.92 first checkout. Replacing one illustrated 6-in lead with one 5-in
lead lowers each figure by **$0.09**. This is an arithmetic delta to that
published illustration, **not** a comparison with a fitting old-pose stack.

The shortened principal cleat retains its **145-mm grain-Y cut length** and
70.95-mm X size; its Z height falls from 103 to 61 mm. Thus the existing
length-and-kerf wood allocation remains
`(560.4/2438.4)P_4x4 + (463.2/2438.4)P_2x4 +
(390.3/2438.4)P_4x6`, and first wood checkout remains
`P_4x4 + P_2x4 + P_4x6`. For the same exactly 139.7-mm Z blank and assumed
3.2-mm rip kerf, that cleat's Z offcut rises from 33.5 to **75.5 mm**;
neither offcut is credited as another part. No numeric lumber price was
available in the [stock/cost sidecar](simple-center-combined-cost-screen.md).
The backer attachment and any other needed hardware remain uncounted, so
neither total is a complete center or frame purchase price.

## Geometry and assembly hold

The [small-tool probe](simple-center-combined-small-tool-probe.md) clears a
**24.511-mm-long, 7.8486-mm-radius socket body** placed straight outward at
each of sixteen nominal exposed ends. It does not model a socket engaged
over the actual head or nut, an extension's drive coupling and shaft, ratchet
head, handle swing, hand space, insertion of a full-length bolt, or the order
of tightening and installing neighboring cleats/bolts. Both ends need a
workable hold/turn state. In particular, the inherited upright-left end
still collides with the earlier 20-mm-radius straight tool envelope; a small
catalog socket body clearing its outward cylinder does not establish a real
socket-plus-extension assembly state. A dry sequence with delivered
hardware and tool geometry must be checked before treating this as usable.

The header rear transverse distance is **30.4 mm**, exactly the conditional
30.4-mm marker; the principal-cleat transverse distance is **30.5 mm**,
only **0.1 mm** above it. The principal cleat's nearest grain-end distance
is **44.7 mm**, just **0.25 mm** above the conditional 44.45-mm marker.
These nominal differences are smaller than ordinary unquantified cutting,
placement and bore-location variations. The axial ±0.05-in trial cannot be
transferred into those edge/end geometry checks. This pose is **unfit for
fabrication or drilling release** at these margins, even if a received bolt
stack passes. Loading direction, joint actions, contact retention, splitting,
washer pressure, wood bearing, bolt yield and the six-case structural
response remain open.

Reproduce with `.venv/bin/python -m scripts.simple_center_small_tool_stack_cost`
and `.venv/bin/python -m pytest -q
tests/test_simple_center_small_tool_stack_cost.py`.
