# Compact spliced-knee flush-top development package

**Status: development package; commercial-angle connection gate open.** Six fresh
listed assembled cases meet their stated bolt/splice, member, contact and geometry
criteria. Retained ML24Z/SDS separation capacity and independent flange-couple
applicability are not established, so this is not a fabrication release. Results come
from current flush-top geometry; the previous spliced-knee six-case result and
later trim approximation do not qualify the relocated upper joint.
See the [six-case commercial-angle ledger](compact-spliced-flush-top-angle-ledger.md)
for the exact open demands and the
[online product/options review](compact-spliced-flush-top-angle-options.md) for
the larger-hardware disposition.

## Exact revision

Candidate `compact-spliced-flush-top-development` retains:

- solid 4x6 side rims and rear legs;
- compact 2x6 header, posts and base;
- four independent unnotched 2x6 knee pieces;
- sixteen 3/8-inch knee bolts and four 1/2-inch upper bolts, with complete stacks;
- outward-facing nuts and threaded tips on all 20 bolts;
- 66 panel/kicker screws, including the lower kicker row at Z60 mm; and
- 7 mm side-rim rear reserve and the no-slip floor assumption.

The owner has selected purchased Fas-n-Tite/Hillman model 42605 #10 × 2 1/2-inch
deck screws for those 66 locations within the accepted panel scope. CAD axis
intersections confirm 45.24375 mm nominal penetration into the 139.7 mm-wide
receivers and 94.45625 mm remaining before their rear faces. Public information
omits dimensions and design values needed to replace the archived SPAX analysis
or render exact purchased geometry. See the
[purchased panel screw record](current-panel-screw-purchase.md). This has no
effect on the separate ML24Z/SDS completion gate.

Only the rear-leg top and upper bolt pair change. Each leg now terminates flush
with its side-rim rear face. Its two half-inch bolts remain at 56 mm pitch, with
pair centre at world YZ `(1134.25, 1761.5)` mm and pitch direction proportional
to `(18, 53)`. Changed legs and rims require fresh stock; old upper holes are not
a repair or redrilling instruction. This candidate has no floor runners, leg
recesses or 1:12 side taper.

## Generated files

Viewer and STEP output live under
`site/hybrid/compact-spliced-flush-top-development/`. Exact fabrication
coordinates live under `docs/compact-spliced-flush-top-construction/`:

- `stock.csv` and `stock-profiles.json` record stock allowances and exact profiles;
- eight `*-bolt-sheet.svg` files, `bolt-member-datums.csv` and
  `profile-corner-datums.csv` record current bolt centres from physical corners;
- `bolt-hardware.csv` records modeled complete bolt stacks;
- `connection-axes.csv` records all 230 connection axes;
- `panel-attachment-axes.csv` and `panel-hole-axes.csv` retain panel operations;
- `timber-passages.json` retains current enclosed service passages; and
- `manifest.json` binds source, viewer and packet artifact hashes.

Sheets are dimensional records, not drill jigs. Use numerical coordinates and
each part's own physical datum. Do not infer pilot sizes, tolerances, torque,
hardware substitutions or resistance from rendered fastener envelopes.

## Hardware schedule and delivered-part acceptance

Use these catalog-identified Grade 5 stacks. Catalog identity is not acceptance
of an uninspected delivered part.

| Quantity | Function | Bolt | Nut | Washers |
| ---: | --- | --- | --- | --- |
| 4 | Upper leg-to-rim | Bolt Depot 407, 1/2-13 x 8 in, partially threaded | Bolt Depot 2573 | 8 Bolt Depot 15025 |
| 8 | Knee-to-rim or knee-to-leg endpoint | Bolt Depot 371, 3/8-16 x 6 in, partially threaded | 8 Bolt Depot 2571 | 16 Bolt Depot 15023 |
| 8 | Knee splice | Bolt Depot 367, 3/8-16 x 4 in, partially threaded | 8 Bolt Depot 2571 | 16 Bolt Depot 15023 |
| 66 | Panel/kicker attachment | Fas-n-Tite/Hillman 42605, #10 × 2 1/2 in | — | — |

Model 42605 is selected only for the owner-accepted panel scope. The 144 ML24Z
fasteners remain Simpson SDS25112 screws and must not be replaced with model
42605.

The nominal-diameter resistance pass requires SAE J429 Grade 5 bolts and the
conditional 90 ksi bending-yield input. Washer checks use 33 ksi as an explicit
material assumption and these catalog tolerance bounds:

| Family | Minimum washer OD | Maximum washer bore | Minimum washer thickness |
| --- | ---: | ---: | ---: |
| 1/2-inch | 34.7472 mm | 14.6558 mm | 2.1844 mm |
| 3/8-inch | 25.2222 mm | 11.5062 mm | 1.6256 mm |

Before assembly, measure each delivered bolt from its under-head bearing face
through the complete full-body shank. Count the thread transition and runout as
threaded. Accept a bolt under the nominal-diameter route only when the first
reduced or transition section starts no earlier than:

| Connection | Minimum full-body shank through transition |
| --- | ---: |
| Upper leg-to-rim | 158.9278 mm |
| Knee-to-rim endpoint | 120.1166 mm |
| Knee-to-leg endpoint | 107.4166 mm |
| Knee splice | 69.3166 mm |

These limits enforce the requirement that threaded bearing occupy no more than
one quarter of each member's bearing length. The catalog thread lengths—38.1 mm
minimum for the half-inch bolt and 25.4 mm minimum for the 3/8-inch bolts—are
minimums, not guaranteed maximums. Also verify that each nut seats fully on its
washer before runout and retains full usable formed-thread engagement at the
tip. Reject or reassess any stack that does not meet these conditions; the
nonpassing full-root sensitivity does not qualify it. See
[half-inch hardware](compact-half-inch-hardware.md) and
[splice hardware](compact-splice-hardware.md) for source details and tolerance
arithmetic.

## Qualification boundary

Matching receiver and washer fit, end/edge distances, six fresh no-slip assembled
cases, and the listed bolt/splice, member and contact checks form the current
evidence basis. The retained commercial-angle connection gate remains open.
Normal contact may open; no tensile floor contact is
credited. Owner excludes floor-friction qualification, so no friction test is a
gate. Conditional calculations are not an unconditional climber rating or
professional engineering approval.

## Regeneration

```sh
uv run python -m scripts.compact_spliced_flush_top_exports
uv run python -m scripts.compact_spliced_flush_top_construction
```
