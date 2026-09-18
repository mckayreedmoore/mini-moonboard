# Lean 38 mm frame: a lighter inspection concept

**Superseded topology:** use the [continuous top/bottom revision](continuous-frame.md)
for the current cross-board connection. This page and its evidence describe
the preserved split-beam version.

**Development geometry, not construction or climbing approval.** This candidate
replaces most of the [wide bolted frame](bolted-redesign.md)'s duplicated backing
with one layer of thinner, deeper members. Its purpose is to reduce material,
handling weight and hidden connections while preserving an inspectable design.
The reference photograph informs the arrangement, not member dimensions,
connection capacities or proof of stability.

## Stock and layout

The working assumption is **1½ in / 38.1 mm stock thickness**, not a measurement
of the photographed product. New principal members use nominal 2×6 lumber with
an assumed actual section of 38.1 × 139.7 mm (1½ × 5½ in). Nominal and actual
sizes differ; purchased stock, species, grade, moisture and measured dimensions
must be recorded before fabrication. See the American Wood Council's
[metric lumber-size guidance](https://awc.org/faq/how-do-i-convert-to-metric-lumber-sizes/)
and [weights and measurement guidance](https://awc.org/priorities/codes-standards/weights-measurement/).

Board-local S runs uphill along the climbing surface; N points behind it.
Most new members begin directly at the plywood backing plane, N=0, and extend
139.7 mm rearward. The retained perimeter rims and leg/kicker interfaces are
exceptions; the new member depth is not the entire assembly's rear extent.

The arrangement comprises:

- Two central uprights, running from S=139.7 mm to the top. Their positions
  leave a service gap around the F-column hardware. They are not a continuous
  solid backing strip across the central panel seam.
- Left and right top spans, plus two pairs of midpoint spans. The midpoint
  rows occupy S=1181.1–1219.2 mm and S=1219.2–1257.3 mm. Each panel edge gets
  its own 38.1 mm-wide receiver, avoiding two screw rows crowded onto one
  narrow member at the horizontal seam.
- Four short edge infills, interrupted around the purchased connector bodies.
  These provide direct panel-edge receivers and local leg/rim attachment stock;
  they do not duplicate full-length deep uprights behind a separate ledge.
  The two lower infills use 2×4 stock, 38.1 × 88.9 mm, because they back panel
  edges without receiving leg bolts. Upper infills remain 2×6 for the leg joints.
  Lower infill gross out-of-plane second moment is only 25.8% of the 2×6
  section; this role-based reduction still requires local strength review.
- A localized lower transition, described below, plus the retained kicker,
  splice profiles and four independent plywood leg plies.

Left and right span lengths differ because of the central service gap. Use the
generated grouped blanks instead of assuming every crossmember is identical.
Round T-nut/LED service reliefs remain necessary; a square-cut blank does not
mean a member needs no subsequent machining. The official face drilling layout
is retained. Central panel-edge support and the offset attachment rows still
require local plywood and fastener qualification.

## The deliberate lower exception

The lower transition is **not single-layer framing**. A flat 2×6 ledge spans
S=0–139.7 mm and N=0–38.1 mm. Two deep lower spans remain behind it at
S=100–138.1 mm and N=38.1–177.8 mm. Retained corner blocks and kicker-splice
geometry make this a localized exception to the simpler main backing.

Four front-driven GRK R4 #9 × 3⅛ in screws, product 103105, connect this ledge
to the lower spans. The [manufacturer's R4 product information](https://www.grkfasteners.com/grk-products/structural-framing-screws/r4-multi-purpose-screw)
identifies the family; the
[customer drawing](https://www.grkfasteners.com/getattachment/9a082069-c76f-4f86-9d32-76965836742c/GRK-R4-Customer-Drawing-(1).pdf)
gives 79.248 mm overall length, 40.894 mm thread length and 4.3942 mm major
diameter for this size. Through the 38.1 mm ledge, nominal gross penetration
is 41.148 mm. That is not effective threaded engagement or a withdrawal rating.
The modeled head and pilot remain proxies; tolerances, actual engagement,
head pull-through, splitting and mixed loading remain unqualified.

Consequently, this redesign does **not** eliminate every ledge or every
withdrawal-dependent connection. The retained lower detail is a priority for
the next structural review, not an approved shortcut.

## Connections and assembly

Sixteen ML24Z connector proxies use six SDS25112 screws apiece: **96 connector
screws, purchased separately**. Actual factory holes, bend geometry, installation
and application-specific resistance must be verified. No custom steel
fabrication or permission to alter purchased connectors is implied. The
[Simpson connector catalog](https://ssttoolbox.widen.net/content/orplhjaqw1/pdf/C-C-2026.pdf)
is the product reference, not a rating for the board's inclined joints.

Climbing panels screw directly into the main receivers. This removes the main
ledge-to-upright through-bolts and counterbores, but it still relies on panel
fastener withdrawal, head pull-through and local plywood behavior under outward
climbing loads. Smaller stock also limits fastener edge margins. Neither glue
nor bolt-clamping friction receives structural credit.

For practical assembly:

1. Label stock and grain direction. Group repeated blanks, keeping unequal
   left/right spans and paired midpoint rows distinct.
2. Lay out the backing-plane datum on a flat, supported work surface. Dry-clamp
   the frame and check diagonals, service gaps and panel seating.
3. Cut the round service reliefs and inspect them against actual hardware.
   Position purchased connectors from the actual products, not proxy steel holes.
4. Fit the retained lower transition and inspect its hidden connections before
   installing the panels. Keep separate access for the leg and kicker hardware.
5. Drill panel fastening locations from the current schedule. Do not reuse the
   wider bolted frame's pockets, long-bolt holes or attachment templates.

Fewer framing layers should simplify assembly, but the retained shaped legs
and kicker are not square-cut-only work. The erection/lifting method and safe
temporary supports still require planning; lower weight is not a one-person
lifting authorization.

## Structural tradeoffs, not capacity results

Compared with a 38.1 × 139.7 mm section, the previous 88.9 × 139.7 mm 4×6
section has 2⅓ times the gross area and out-of-plane second moment of area.
Returning to 2×6 therefore retains about **43%** of those quantities and about
**7.9%** of the former in-plane second moment. These equal-modulus, rectangular
section comparisons exclude holes and connections; they are not whole-frame
stiffness, strength or allowable-load ratios. Removing duplicate layers also
changes the load path, not just member weight.

An **unmodeled nominal 2×8-depth option**, 38.1 × 184.15 mm, would add about
32% member area while giving about 2.29 times the 2×6 gross out-of-plane second
moment. It would also alter connector space, rear projection, mass and joint
demands. It is an analytical option only—not another selectable or validated
design. No previous bonded-joint FEA result approves either depth.

## Measured CAD reduction and screening

The [source-bound report](../fea/results/lean-frame/report.json) includes each
part's calculated mass. Using the same assumed densities as the heavier variant
(wood 600 kg/m³, connector proxies 7,850 kg/m³), included mass is **181.14 kg /
399.34 lb**, down from 280.72 kg / 618.88 lb: **35.47% less, not half**.
Fasteners, holds, LEDs and glue are excluded from both estimates. Main plywood
faces alone contribute 64.80 kg; these are calculated volumes, not scale weights.

All 96 selected rigid-body cases meet the illustrative 1.5 edge-moment target:

| Climber weight | Minimum moment factor |
| --- | ---: |
| 150 lb | 1.935 |
| 200 lb | 1.901 |
| 250 lb intended maximum | 1.869 |
| 300 lb sensitivity | 1.837 |

These cases combine 1×/2× downward gravity, 0/300 N horizontal force over all
azimuths, 0/50/100 mm hold standoff and 80%/100% included mass. The result is
not joint-strength FEA, a sliding/contact solution or a climber rating. Upward
and opposite-normal exploratory loads are not included, and earlier concerns
about them are not superseded. Removing weight reduces restoring moments;
the heavy frame's stability result was not transferred to this version.

All 19 focused tests pass. CAD/export checks cover collisions, fastener components, official holes and
rear service reservations, direct panel receivers, thin-stock geometry, the
lower exception, mass, STEP solids, STL volume/bounds, dual-unit schedules and
source hashes. Screening tests replay the published cases. Independent design,
testing and dataflow reviews found no remaining substantial implementation
findings; that is not engineering approval.
Browser checks load all 267 selectable meshes, verify rear-member selection and
dual-unit dimensions, and exercise the rear-view URL. Front, close-up selection
and rear-overview screenshots were inspected locally.

```sh
uv run pytest tests/test_lean_frame.py tests/test_lean_exports.py tests/test_lean_screen.py
```

The screen generator, `uv run python -m fea.lean_screen`, refuses to overwrite
its published report. Use a fresh checkout without that report to regenerate
evidence. The exporter preserves all older variants and their source hashes.

Remaining gates include actual stock, connector and panel-fastener resistance,
net sections and splitting, panel support, racking, independent leg-ply load
sharing, the kicker splice, floor contact/friction and dynamic loading. The
crash pad remains a separate excluded element. No anchors or ballast are assumed.

## Inspection files

[Open the lean frame from the rear](https://mckayreedmoore.github.io/mini-moonboard/?model=lean-38mm-frame&view=rear)
to inspect the changed backing, or use the
[front view](https://mckayreedmoore.github.io/mini-moonboard/?model=lean-38mm-frame).
Download the [STEP assembly](../exports/lean-38mm-frame/lean-38mm-frame.step),
[parts schedule](../exports/lean-38mm-frame/lean-38mm-frame_parts.csv),
[connection schedule](../exports/lean-38mm-frame/lean-38mm-frame_connections.csv),
[grouped blanks](../exports/lean-38mm-frame/lean-38mm-frame_blank_groups.csv) and
[hole-entry coordinates](../exports/lean-38mm-frame/lean-38mm-frame_hole_entries.csv).
Schedules use metric and imperial units. They are inspection records, not
approved drilling templates or a construction release.
