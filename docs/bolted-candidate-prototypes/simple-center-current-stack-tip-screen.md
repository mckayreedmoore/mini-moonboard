# Current PB-02 center: grip, stack and installed-tip screen

Status: **development sensitivity only; no bolt selection, purchase or drilling release.**
This screen uses `shorter_8in_trial` from the current
[two-bolt pose](simple-center-post-header-two-bolt-probe.md), not the older
single-axis post/header layout in the Astra C3 review. The post/header block is
X=177.65…266.55, Y=−175.7…−86.8, Z=95…238.9 mm: **143.9 mm** long in grain Z.
The six other bores come from the maintained tolerance pose. The
[reproduction script](../../scripts/simple_center_current_stack_tip_screen.py)
checks ten bore end pairs; this is not a qualified fastener schedule.

## Axial screen

Lengths below are trial nominal under-head lengths. The source bore-end planes
give wood grip. For sensitivity, wood grip is ±0.05 in, each washer is
0.050–0.075 in, nut height is 0.20–0.25 in, and required tip beyond the nut is
0.25 in. None is a delivered tolerance or an installation specification. The
minimum tip margin uses maximum grip, both thick washers and the taller nut.
"Latest thread start" is the furthest first *complete usable* thread could
start from under the head at minimum grip and thin washers; actual thread
start, thread end and nut engagement remain unknown. A positive length margin
alone does not make a stack usable.

| Bore(s) | Wood grip mm | Trial length in | Minimum tip margin mm | Latest usable thread start in |
| --- | ---: | ---: | ---: | ---: |
| Post/block pair (2) | 177.8 | 8 | 7.62 | 7.050000 |
| Block/header pair (2) | 182.0 | 8 | 3.42 | 7.215354 |
| Header/principal block | 109.1 | 5 | **0.12** | 4.345276 |
| Principal block/principal | 109.05 | 5 | **0.17** | 4.343307 |
| Post low/high (2) | 127.0 | 6 | 7.62 | 5.050000 |
| Upright | 127.0 | 6 | 7.62 | 5.050000 |
| Link | 94.9 | 5 | 14.32 | 3.786220 |

The old [8-in lead screen](simple-center-post-header-8in-stack-screen.md)
quotes retailer-reported thread lengths for Everbilt 800696 and Prime-Line
9058821. Its inferred 2.0-in and 7.0-in starts are nominal patterns, not
verified first complete usable threads. The current 8-in axes permit an
assumed start no later than 7.05 in (post/block) or 7.215 in
(block/header); both nominal patterns fit that *one* condition. Actual bolt
length, thread placement, runout and tip chamfer could erase the small margins.
No identified 5-in or 6-in product has been accepted for the other bores.

## Longer ordinary-retailer leads at the two limiting grips

The [Home Depot Everbilt 805336](https://www.homedepot.com/p/204633310)
listing identifies a 1/4-20 × 5½-in hex bolt, while
[Lowe's Hillman 190062](https://www.lowes.com/pd/Hillman-1-4-in-Zinc-Plated-Coarse-Thread-Hex-Bolt/1000379701)
lists the same nominal size and describes a partially threaded shank.
The [Home Depot Everbilt 805436](https://www.homedepot.com/p/204633311)
listing identifies a 1/4-20 × 6-in A307 galvanized hex bolt and says it is
fully threaded. These are dated public retailer leads, not verified delivered
thread/runout dimensions or approved substitutions.

Using the *same invented* grip, washer, nut and tip intervals above, changing
only `header_cleat` and `cleat_principal` gives:

| Trial nominal length | Minimum tip margin, mm | Maximum exposed tip from wood, mm | Modeled permanent envelope |
| --- | ---: | ---: | --- |
| 5 in, prior | 0.12 / 0.17 | 17.90 / 17.95 | No tested clash |
| 5½ in | 12.82 / 12.87 | 30.60 / 30.65 | No positive-volume wood, fixed-screw or other-bolt clash at either end |
| 6 in | 25.52 / 25.57 | 43.30 / 43.35 | Left end of principal cross-bolt tip enters left center principal by 518.99 mm³; opposite end avoids that modeled clash |

Each pair of numbers is header-to-principal-block, then
principal-block-to-principal. The 5½-in length is a better **nominal length
and occupancy lead** than the marginal 5-in trial, but the first complete
usable thread still must begin no later than 4.345 / 4.343 in from under the
head under the assumed minimum-grip/thin-washer case. Neither 5½-in listing
establishes that datum. Its actual grade, root diameter, washer/nut match,
thread engagement, delivered length, torque and tool access are not qualified.
The six-inch clash is orientation-specific, not proof that every six-inch
arrangement fails; an opposite orientation still needs the complete stack,
hold-and-turn access and contact checks. None of these rows selects hardware
or supports drilling.

## Permanent envelope, separate from temporary access

For each end of each bore the script tests both possible head/nut assignments.
At the nut end it places a conservative **3.65-mm-radius** shaft/tip cylinder
from the wood face through the maximum nominal exposed length at minimum grip
and thin head washer. It also places a **10-mm-radius** washer/nut cylinder
through the thick washer plus tall nut. The opposite head uses the earlier
pose's 10-mm-radius × 5-mm generic envelope. These radii and head height are
model envelopes, not purchased dimensions. All 60 envelopes have zero
positive-volume overlap with modeled wood and 66 fixed panel/kicker screw
axes. There are no potential overlaps between envelopes on *different* center
bolts in the tested alternate orientations. The shaft/tip test covers
finished assembly occupancy: removing panels during assembly cannot resolve
a permanent clash with them. It does not measure surface gap or tolerance.

The earlier pose checked a catalog-size socket outer cylinder and an
illustrative straight extension; this screen does not promote either to tool
access. Socket internal depth around the projecting tip, nut engagement,
drive coupling, handle sweep, hand clearance, hold-and-turn pair, insertion
sequence and installed panel access are still unknown. Actual washer OD,
washer bearing, nut across-flats/height, head size, delivered bolt shank and
usable thread interval must be measured against this same pose. The two
109-mm grips have essentially no nominal length reserve after the stated
sensitivity stack. The conditional edge/end markers, member resistance and
connected-center load path are separate unresolved checks.

Run `.venv/bin/python -m scripts.simple_center_current_stack_tip_screen` and
`.venv/bin/python -m pytest -q tests/test_simple_center_current_stack_tip_screen.py`.
