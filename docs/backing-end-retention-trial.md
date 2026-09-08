# Purchased backing-end retention trial

**Unselected geometry investigation.** The current wider-principal CAD, its
18 installed angles and purchasing schedule are unchanged. This trial addresses
the load-path concern identified in the
[isolated backing-contact calculation](wide-backing-contact-bound.md), not a
proven physical failure.

## Proposed arrangement

Investigate one ML23Z angle at each junction between the backing's rear face
and the inner side rim. The virtual corner is at X = ±1181.1 mm,
S = 44.45 mm and N = 38.1 mm. One flange lies against the backing, the other
against the rim; the bend follows S. Four SDS25112 screws per angle give eight
additional screws. The central backing bolts would remain for this comparison.

Unlike the existing upper-frame ML24Z angles, these bend axes follow S rather
than N. Do not assign their board-normal retention the ML24Z F1 value. The loaded
member, installation figure, signs and combined-load treatment require separate
qualification. No application capacity is assigned here.

The [official 2026 catalog, page 323](https://ssttoolbox.widen.net/content/wrzfhjzbna/pdf/C-C-2026-p323.pdf)
lists ML23Z as a nominal 2 × 2 × 3 inch, 12-gauge angle using four separately
purchased 1/4 × 1-1/2 inch SDS screws. The manufacturer's
[product page and drawing downloads](https://www.strongtie.com/decks_decksandfences/ml_angle/p/ml)
provided the exact drawing references recorded in [ml23z-reference.json](ml23z-reference.json).
No vendor drawing is redistributed.

## Drawing-backed dimensions and fit scope

| Feature | ML23Z drawing datum |
| --- | --- |
| Bend-line width | 76.2 mm / 3 in |
| Thickness | 2.5654 mm / 0.101 in |
| Outside flange reach | 53.3654 mm / 2.101 in |
| Width stations relative to midpoint | ±22.225 mm / ±0.875 in |
| Staggered flange offsets | 35.9029 and 42.2529 mm / 1.4135 and 1.6635 in |
| Factory hole diameter | 6.731 mm / 0.265 in |

The manufacturer cautions that drawing geometry is approximate. These precise
coordinates are not manufacturing tolerances. ML24Z scaling would give the
wrong holes and thickness. ML23Z also has chamfered outer corners; a complete
solid model must retain those and the bends.

Centered on the backing, the nominal width leaves 6.35 mm at each S edge. Its
screw axes sit 22.225 mm from the nearest S edge. The backing flange's minimum
axis distance from the rail's X end is 35.9029 mm. These are measured geometry,
**not a passed edge/end-distance requirement**.

The proposed eight screw axes and full 6.35 mm nominal shaft envelopes are
tested against their intended current, service-pocketed wood receivers. Gross
penetration is 38.1 − 2.5654 = 35.5346 mm. This is not effective thread length,
withdrawal resistance or proof of the complete assembly's fit.

## Remaining before selection

1. Complete bracket solids, heads and tool/removal envelopes; test against all
   existing fasteners, panels, service reservations and floor/base geometry.
2. Establish applicable manufacturer edge/end-distance and installation limits
   for both members. Reconcile the shallow backing with cross-grain loading.
3. Compare realistic panel/backing/rim load transfer and connection resistance.
   An added bracket is not an infinitely stiff, infinitely strong support.
4. Define transport separation: leaving angles on the rims may require removal
   of backing screws. Do not credit repeated SDS removal/reinstallation as a
   qualified demountable connection. Preserve routine panel-only service access.

The source is `mini_moonboard/backing_end_trial.py`; tests run with
`uv run pytest -q tests/test_backing_end_trial.py`. No new holes are added to
the current candidate, no purchase is requested, and this trial is not shown as
installed in the viewer.
