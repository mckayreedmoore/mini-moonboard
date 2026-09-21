# PB02 integrated ten-bolt stack sensitivity

Status: **bounded sensitivity only; no fastener selection, purchase, strength,
fabrication, or drilling verdict.** The
[reproduction script](../../scripts/simple_center_pb02_integrated_stack_screen.py)
applies the maintained
[`simple_center_current_stack_tip_screen`](simple-center-current-stack-tip-screen.md)
logic to the committed `e9e4e42` PB02 Z370 working pose. Relative to that
screen's source pose, `header_cleat` wood grip is **105.1 mm** instead of
109.1 mm and `cleat_link` is **99.7 mm** instead of 94.9 mm. A script guard
requires those to be the only grip changes.

## Invented sensitivity bounds

The calculation retains the earlier invented bounds: wood grip ±0.05 in,
each washer 0.050–0.075 in, nut height 0.20–0.25 in, and 0.25 in required
tip beyond the nut. These are analysis intervals, not retailer or
manufacturer facts, purchased-part tolerances, or installation requirements.
The minimum tip margin uses maximum grip, two thick washers, the tall nut,
and the nominal trial bolt length. The latest usable-thread start uses
minimum grip and two thin washers. No listed product verifies that complete
usable-thread datum.

| PB02 bore(s) | Count | Grip mm | Trial in | Min tip margin mm | Latest thread start in |
| --- | ---: | ---: | ---: | ---: | ---: |
| `post_cleat_1/2` | 2 | 177.8 | 8 | +7.62 | 7.050000 |
| `cleat_header_1/2` | 2 | 182.0 | 8 | +3.42 | 7.215354 |
| `header_cleat` | 1 | **105.1** | 5 | +4.12 | 4.187795 |
| `cleat_principal` | 1 | 109.05 | 5 | +0.17 | 4.343307 |
| `post_low/high` | 2 | 127.0 | 6 | +7.62 | 5.050000 |
| `upright` | 1 | 127.0 | 6 | +7.62 | 5.050000 |
| `cleat_link` | 1 | **99.7** | 5 | +9.52 | 3.975197 |

All ten current nominal lengths clear the invented axial interval. The
`cleat_principal` five-inch trial remains limiting at +0.17 mm. A positive
calculated margin does not verify delivered length, first or last complete
thread, runout, tip chamfer, washer or nut dimensions, engagement, bearing,
or installation access.

## Length and installed-envelope sensitivity

The alternate rows change only the named nominal trial lengths. Maximum tip
is measured outward from the wood face at minimum invented grip with the thin
head washer.

| Trial | Minimum tip margin mm | Maximum tip from wood mm | Permanent-envelope result |
| --- | ---: | ---: | --- |
| Current 5-in `header_cleat` / `cleat_principal` | +4.12 / +0.17 | 21.90 / 17.95 | No modeled hit |
| 5.5-in principal pair | +16.82 / +12.87 | 34.60 / 30.65 | No modeled hit |
| 6-in principal pair | +29.52 / +25.57 | 47.30 / 43.35 | Left tip/wood hit, 518.98796 mm³ |
| Current 5-in `cleat_link` | +9.52 | 27.30 | No modeled hit |
| 5.5-in `cleat_link` | +22.22 | 40.00 | No modeled hit |

The six-inch principal result is orientation specific. The opposite tested
orientation has no positive-volume hit, but this does not establish assembly,
tool, hand, or hold-and-turn access. Across these trials the script reports
no potential positive-volume collision between permanent envelopes belonging
to different bolts.

## Ordinary-store leads already documented

This follow-up adds no retailer search and transfers no facts between SKUs.
The existing source notes identify these exact nominal-length leads:

At 5 inches the leads are Home Depot Everbilt `800676` (A307, listed fully
threaded), Home Depot Prime-Line `9058745` (A307 Grade A, 25-pack), and Lowe's
Hillman `190059` (listed partially threaded).

At 5.5 inches they are Home Depot Everbilt `805336` (single), Home Depot
Everbilt `805330` (A307, listed fully threaded, 25-pack), and Lowe's Hillman
`190062` (listed partially threaded).

At 6 inches the lead is Home Depot Everbilt `805436` (A307, galvanized, listed
fully threaded). At 8 inches they are Home Depot Everbilt `800696` (A307,
listed six-inch thread) and Home Depot Prime-Line `9058821` (A307 Grade A,
10-pack).

These are online ordinary-store leads, not selected hardware or local-stock
claims. “Fully threaded” does not locate the first and last complete usable
threads or establish the delivered under-head length. The documented
six-inch thread on `800696` likewise permits only an inferred nominal
two-inch thread start if both dimensions share a datum and the thread runs to
the nominal tip. The script therefore marks every lead's usable thread
interval unverified.

Run:

```text
.venv/bin/python -m scripts.simple_center_pb02_integrated_stack_screen
.venv/bin/python -m pytest -q tests/test_simple_center_pb02_integrated_stack_screen.py
```
