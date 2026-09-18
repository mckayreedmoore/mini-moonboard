# Part-local machining review package

This package describes **`wide-principal-development`**: 29 wooden parts,
188 connection assemblies represented by 276 member-specific axis rows, and
422 additional feature records. It is a dimensional inspection package, **not
approved machining, assembly or climbing instructions**. Existing STEP/viewer
geometry, structural limitations and historical variants remain unchanged.

## Schedules

- [Part datums and oriented extents](wide-machining/datums.csv)
- [Connection axes and raw-material entry/exit witnesses](wide-machining/connections.csv)
- [Panel holes, service spaces, housings, head recesses and bearing planes](wide-machining/features.csv)
- [Numbered raw-profile vertices](wide-machining/drawings/vertices.csv)
- [Complete structured metadata and source hashes](wide-machining/metadata.json)
- [Hardware quantities and product references](wide-purchase-bom.md)
- [Assembly/access sequence](wide-principal-assembly.md)

Coordinates in each vector cell are ordered **U, V, W**, not automatically
world X, Y, Z. Triplets and lists of triplets use JSON notation inside CSV
cells. The datum record supplies the world origin and three unit axes needed
to transform them back into the assembly. Measurable local coordinates and
feature dimensions are supplied in millimetres and decimal inches.

| Part family | U | V | W |
| --- | --- | --- | --- |
| Inclined face panels, rims, principals and crossmembers | X across board | S up the inclined board | N toward backing |
| Leg plies and side gussets | World Y | World Z upward | World X through the ply |
| Kicker halves | World X | World Z upward | Negative world Y toward backing |
| Header and posts | World X | World Y | World Z upward |

The origin is the minimum corner of the **oriented raw-form envelope**. A slope,
housing or trim may remove that corner, making it virtual. It is not a hole,
an arbitrary visible corner or an instruction to measure from the nearest edge.
The sketches and vertex table identify the actual profile; establish usable
physical face/edge witnesses before laying out stock. Datum frames are not grain
directions or a recommendation for clamping the part.

## Reading the operations correctly

The connection schedule separates:

- 56 bolt-clearance rows, one per intersected wooden member;
- 56 panel-clearance rows;
- 56 receiver insert-pilot axes;
- 108 manufacturer clip-screw axes, transferred through actual factory holes.

`raw_entry_local_*` and `raw_exit_local_*` are intersections of the full axis
with the undrilled part form. They are useful layout witnesses, **not selected
drill depths or thread engagement**. The bolt under-head origin can sit inside
a recess, so its signed distance to a raw surface may be negative. The schedule
does not invent SDS pilot diameters or replace manufacturer installation guidance.

The additional features comprise 142 T-nut holes (132 main and ten kicker),
132 main LED holes, 80 straight service reservations, 56 panel-head envelopes,
two principal housings, two backing counterbores and eight bearing-plane markers.
The currently modeled T-nut bore is 11.1125 mm (7/16 in), while LED bores are
13 mm. These are this candidate's geometry, not a substituted universal hardware
recommendation; reconcile them with the selected T-nut and LED records.

`entry_role` distinguishes a stated physical panel face from a **cutter reference
that has not been verified as a material surface**. Through-hole cutters have
1 mm overshoot on each side. Service cylinders begin at the board backplane,
which may lie in air in front of a housed principal. Their 45 mm cutter depth is
not automatically a 45 mm blind bore from the nearest timber surface.

The 17 mm receiver reservation is not a finished insert pilot depth. The insert
outer-diameter display cut is not its installation pilot. Likewise, the 80°
maximum-head envelope is not an approved depth for the provisional 82° workshop
countersink. Effective engagement, drill-point allowances, seating, torque and
application resistance remain unresolved.

The CAD insert origins are at the receiver surface. The manufacturer describes
Type E installation below that surface but does not specify the recess in the
retrieved instructions. Consequently, the listed origins are nominal layout
datums, not an instruction to install at zero recess. A resolved recess changes
the screw's reach relative to the insert top and may require a changed screw
length or pilot reservation. See the [engagement arithmetic](panel-insert-selection.md).
Do not apply the CSV's nominal receiver depth or the rendered insert position
as a finished stop setting while this remains unresolved.

The backing counterbores start at timber surface N=0 and extend 12.032 mm, with
28.575 mm diameter. Their bolt origins are at N=10, not the cutting surface.
Socket clearance, remaining ligament resistance and actual tolerances still
need review before machining. Principal housing dimensions describe the actual
rectangular CAD cut; the cutter corner need not be an exposed timber corner.

Each lower bearing-plane record supplies an actual face centroid and outward
normal in both coordinate systems. The four principal/rim seats are horizontal
at world Z=225 mm; all four leg-ply feet are horizontal at Z=0. These are plane
definitions, not saw settings or a claim of adequate bearing resistance. The
centroid is not a stock corner. For a point `p` on a plane, local coordinates
satisfy `normal · (p − plane_point) = 0`.

## Orthographic references

Each drawing has three dimensioned local projections and numbered vertices.
All raw edges—including hidden/rear edges—are shown. These are not finished
machined-part drawings, unfolded templates or CNC toolpaths. Dashed rectangles
are envelope bounds, which can differ from the stock blanks in the cut list.
Crowded vertex labels are omitted from the picture, not from the complete CSV.
Curved edges, if present, are sampled for display; the STEP geometry remains
authoritative for curves. Do not measure a printed SVG to set a cut or hole.

| Members | Drawings |
| --- | --- |
| Main panels | [Lower left](wide-machining/drawings/main_lower_left.svg), [lower right](wide-machining/drawings/main_lower_right.svg), [upper left](wide-machining/drawings/main_upper_left.svg), [upper right](wide-machining/drawings/main_upper_right.svg) |
| Kicker | [Left](wide-machining/drawings/kicker_left.svg), [right](wide-machining/drawings/kicker_right.svg) |
| Rims and principals | [Left rim](wide-machining/drawings/base_side_left.svg), [right rim](wide-machining/drawings/base_side_right.svg), [left principal](wide-machining/drawings/base_principal_left.svg), [right principal](wide-machining/drawings/base_principal_right.svg) |
| Crossmembers | [Top](wide-machining/drawings/base_rail_top.svg), [lower backing](wide-machining/drawings/timber_bottom_backing.svg), [mid lower left](wide-machining/drawings/base_rail_mid_lower_left.svg), [mid lower right](wide-machining/drawings/base_rail_mid_lower_right.svg), [mid upper left](wide-machining/drawings/base_rail_mid_upper_left.svg), [mid upper right](wide-machining/drawings/base_rail_mid_upper_right.svg) |
| Header and outer posts | [Header](wide-machining/drawings/base_header.svg), [left post](wide-machining/drawings/base_post_outer_left.svg), [right post](wide-machining/drawings/base_post_outer_right.svg) |
| Central posts | [Left front](wide-machining/drawings/base_post_center_left_front.svg), [left rear](wide-machining/drawings/base_post_center_left_rear.svg), [right front](wide-machining/drawings/base_post_center_right_front.svg), [right rear](wide-machining/drawings/base_post_center_right_rear.svg) |
| Leg plies | [Left inner](wide-machining/drawings/leg_left_inner.svg), [left outer](wide-machining/drawings/leg_left_outer.svg), [right inner](wide-machining/drawings/leg_right_inner.svg), [right outer](wide-machining/drawings/leg_right_outer.svg) |
| Base gussets | [Left](wide-machining/drawings/timber_base_gusset_left.svg), [right](wide-machining/drawings/timber_base_gusset_right.svg) |

## Reproduction and remaining gates

```bash
uv run python -m mini_moonboard.wide_machining
uv run python -m scripts.wide_machining_drawings
uv run pytest -q tests/test_wide_machining.py tests/test_wide_machining_features.py \
  tests/test_wide_machining_drawings.py tests/test_wide_machining_evidence.py
```

The schedule generator refuses to overwrite an existing package. Preserve
earlier outputs before intentionally generating a revised candidate. The drawing
generator regenerates its own SVGs and vertex table. Tests replay current CAD,
require complete CSV fields, verify actual entry/exit witnesses and bearing
planes, and check source/artifact identity. These tests do not qualify physical
stock, machining tolerance, tool access, handling or structural performance.

The [connection ledger](connection-qualification-ledger.md) remains the record
of unfinished joint resistance, load sharing and physical validation. No new
capacity, supplier approval or safe lifting/erection procedure is implied by
these additional dimensions.
