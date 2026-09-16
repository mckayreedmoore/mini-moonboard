# Fitted-block restraint decision

Date: September 14, 2026.

## Decision

**Reject the examined route before CAD.** Four Simpson Strong-Drive SDWS
Timber screws driven vertically upward from the header underside through the
fitted 6x6 seat and into the square-ended rim would provide a conceptually
positive screw path for seat thrust and rim uplift. The required two-column
layout cannot coexist with the outer-post/header bearing, however, and the
published screw route does not qualify this three-member, two-interface,
oblique-to-rim-grain application.

This is a finite rejection of one ordinary commercial-screw concept. It does
not reject every fitted-block restraint and does not predict physical failure.
No geometry, drilling, hardware selection, CAD, response model or design
selection changes. `compact-floor-uncut-development` and this square-end
concept remain unselected.

## One examined physical layout

Left-side coordinates are stated below; no mirrored rollout is proposed.
Retain the square rim end and independent seat from
[the bevel decision](uncut-rim-bevel-decision.md): rim and seat
X[-1219.2,-1130.3] mm, seat grain along Y, header Y[-175.7,-36] mm and
Z[238.9,277] mm, and outer post X[-1308.1,-1168.4] mm,
Y[-175.7,-36] mm, Z[0,238.9] mm.

The examined group has upward vertical axes at the Cartesian product of:

- X = -1193.8 and -1155.7 mm, leaving 25.4 mm to the two seat/rim X edges;
- Y = -110.0 and -59.2 mm, giving 50.8 mm row pitch.

Use SDWS22600DB, 0.220-inch by 6-inch, at the rear row and SDWS22800DB,
0.220-inch by 8-inch, at the forward row. Install from the header underside
before placing the rim, with the integral washer head seated on the flat header
underside. Screws pass through the 38.1 mm header, then the separate seat, and
terminate within the rim. No interface friction, adhesive, screw preload or
composite action is credited.

Exact vertical wood paths are:

| Row Y (mm) | Seat top / rim end Z (mm) | Seat path (mm) | Rim path available above end (mm) | Header-bottom to rim-top (mm) | Nominal screw penetration into rim (mm) | Tip reserve below rim top (mm) |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| -110.0 | 334.480564 | 57.480564 | 78.215753 | 173.796317 | 56.819436 | 21.396317 |
| -59.2 | 291.854303 | 14.854303 | 181.383097 | 234.337399 | 150.245697 | 31.137399 |

In intended mechanics, screw axial action would restrain rim/seat uplift and
screw lateral action across the header-seat and seat-rim planes would restrain
horizontal translation. Compression remains assigned to the fitted rim/seat
and seat/header faces only. No screw capacity is assigned by this description.

## Accepted-case screening witness

The accepted no-slip A12-left uncut report records 242.800 N vertical
compression at the left rim/header contact. Applying only the frictionless
square-seat force transformation gives

```text
N = 242.800/cos(40 degrees) = 316.953 N
H = 242.800*tan(40 degrees) = 203.733 N
```

`H` acts rearward on the seat. These values show the force components the new
path must represent; they are not demands from the changed geometry, are not
divided among screws, and transfer no prior acceptance. An uplift demand is
not obtained from this compression witness. Positive uplift restraint remains
a topology requirement for a later response, not an invented numeric load.

## Geometry and installation rejection

The outer screw column at X = -1193.8 mm lies inside the outer post's X
interval. Both Y rows also lie inside its Y interval. Their integral washer
heads would therefore occupy the post/header bearing interface at Z = 238.9 mm.
Leaving the heads proud prevents full post seating; recessing them removes wood
from the 38.1 mm header at the post bearing and creates a different unassessed
joint. Installing the screws before the post does not remove this collision.

Only 38.1 mm of seat/rim width lies inward of the post face,
X[-1168.4,-1130.3] mm. That strip cannot preserve this two-column layout with
its 38.1 mm pitch and 25.4 mm edge offsets. Moving both columns there, replacing
the post bearing, or adding an offset plate would be a new concept. Thus the
specified positive restraint has no installable application planes in the
preserved post/header geometry.

## Primary resistance-basis rejection

[IAPMO ER-192](https://forms.iapmo.org/ues_reports/reports/er_0192.pdf) is the
primary evaluation for SDWS Timber screws. It supplies product dimensions,
installation requirements and withdrawal/lateral routes, and directs combined
lateral/withdrawal design to NDS section 12.4.1. The matching
[Simpson fastener technical guide](https://ssttoolbox.widen.net/content/zpm9nibpvz/pdf/C-F-2025TECHSUP.pdf)
requires its lateral spacing conditions in both connected members.

This proposed screw crosses three independently acting wood members and two
shear planes. Seat thickness along a forward axis is only 14.854 mm, while the
rear axis has 57.481 mm. The screw axis is perpendicular to header grain,
perpendicular to seat grain, but only 40 degrees from rim grain. Neither cited
source identifies this varying-thickness header-seat-rim stack as its listed
wood-to-wood connection geometry or supplies load allocation between its two
interfaces. Treating the seat and header as one side member would assume the
composite action expressly excluded here. Applying a two-member table twice
would assign the same screw force independently at incompatible shear planes.

[NDS 2024 Chapter 12](https://awc.org/wp-content/uploads/2026/08/AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-%E2%80%93-Dowel-type-fasteners.pdf)
provides dowel-type connection mechanics and load-direction-dependent placement;
it does not turn this proprietary screw and three-member path into two qualified
connections or supply an oblique rim-withdrawal value. No end-grain, glulam,
European or generic lag-screw value is transferred. Consequently no supported
lateral/withdrawal interaction or group resistance can be calculated even if
the head collision were ignored.

## Stop condition

Do not advance this vertical SDWS route to CAD, drilling, a native solve or a
mirrored layout. A later fitted-block concept must first place every physical
head and driver outside the post/header bearing and identify a primary method
covering each real shear plane plus axial restraint without combining the seat
and header. No second route is proposed by this bounded decision.
