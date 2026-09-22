# Outer-rail barrel-bolt length sensitivity

This preserved detached screen reconstructs the **historical 5 in bolt /
70 mm barrel setback** rail producer with the kerf-right outer-header row at
Y = −85 mm. The current viewer instead uses nominal 6 in bolts / 60 mm
setbacks at these six stations. This comparison consumes a source-bound
historical connector inventory and changes no selected baseline, fixed axis,
or current viewer pose. The six exact outer-rail duties are:

| Family | Left station | Right station |
| --- | --- | --- |
| Bottom | `clip_horizontal_bottom_left_1` | `clip_horizontal_bottom_right_2` |
| Lower | `clip_horizontal_lower_left_1` | `clip_horizontal_lower_right_2` |
| Upper | `clip_horizontal_upper_left_1` | `clip_horizontal_upper_right_2` |

Each station owns two barrel/bolt rows, giving **12 modeled 1/4-20 shafts**.
All twelve current 5 in shafts end **33.551 mm short** of their provisional
barrel-body midpoint axis points. Nominal alternatives retain each exact
bolt start, direction, diameter, modeled washer offset, and barrel pose.

| Nominal shaft | Tip past assumed axis | Tip past modeled barrel's far wall | Added bore to tip | Rail wood beyond tip to far X face |
| --- | ---: | ---: | ---: | ---: |
| 6 in / 152.4 mm | −8.151 mm | −13.1548 mm | 0 mm | 979.401 mm left; 976.226 mm right |
| 7 in / 177.8 mm | +17.249 mm | **+12.2452 mm** | 10.2452 mm | 954.001 mm left; 950.826 mm right |

These values apply to both rows of each bottom, lower, and upper duty on
the stated side. The far-side measure follows the bolt axis to the actual
receiving rail's far X face. It is not radial edge distance, net-section
strength, or a drilling depth. Both nominal tips lie inside their receiving
wood in this current geometry.

The barrel body's source-recovered outside diameter is 10.0076 mm. Its
midpoint axis lies 160.551 mm from the bolt start, and its downstream cylindrical
wall lies 165.5548 mm from that start. Thus the 7 in nominal tip exits the
*modeled barrel envelope* and projects 12.2452 mm into the receiving rail
beyond it. This alone does not tell where usable threads would engage in a
delivered barrel or whether the bolt would bottom out.

The existing 7.5 mm viewer machine bore ends 167.5548 mm from the bolt start,
already 2 mm past the modeled barrel wall but 10.2452 mm before the 7 in
nominal tip. Extending that bore by exactly 10.2452 mm gives **zero modeled
axial clearance beyond the tip**. The modeled 6.35 mm shaft inside a 7.5 mm
bore has only a nominal 0.575 mm radial gap per side; this is a viewer envelope,
not a delivered fit or drill-size specification. The 6 in tip lies within the
existing bore but still misses the assumed barrel axis. A deeper bore with
appropriate tip clearance and verified matching thread engagement are needed.

For both lengths, finite-solid checks found no positive-volume hits above
1 mm³ between the trial shafts or added bore segments and unrelated kerf-right
wood, the fixed 66 panel/kicker screw and 12 frame-bolt envelopes, the other
protected envelopes (142 T-nuts, 142 hold-hole/projection trials, 132 lights,
131 wires), or neighboring viewer bolt-stack and barrel solids. The matching
barrel is excluded from neighbor hits because its shaft engagement is the
intended contact. An added bore's volume outside its receiving rail is zero.
These are nominal collision observations, not toleranced clearance or
structural acceptance.

The ordinary retail lead is [Home Depot Everbilt model 807396, 1/4-20 × 7 in
hex bolt](https://www.homedepot.com/p/204281599). It is **not selected
hardware**. The listing and this screen do not establish delivered shaft
length, usable thread span, matching barrel engagement, head/washer fit,
capacity, bore depth with clearance, or approval to drill or fabricate. The
7 in alternative is **not a demonstrated fit** merely because it reaches the
assumed axis.
No contact or purchase was made. The current outer-rail stations remain
`REVISE`; this probe makes no release claim.

Run `uv run python -m scripts.owner_barrel_outer_rail_bolt_length_probe` for
the per-bolt source-bound record. The script reports each trial shaft, bore
extension, far-side residual, and collision family independently.
