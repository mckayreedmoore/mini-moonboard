# BR904 center joint: no-contact geometry concept

Status: search envelope only. No sample has been measured. No connector, bolt
diameter, hole, joint resistance, or drilling pattern is selected.

The exact [Newhouse BR904](https://newhouseelectric.com/products/bracket-90deg-4-hole)
is listed at [Home Depot](https://www.homedepot.com/p/325186317). Newhouse states
four factory 9/16 in holes with 1-7/8 in spacing, 4-gauge Q235 steel, and an
electro-galvanized finish. It does not give bend-to-hole centers, plate width,
leg lengths, finished minimum thickness, bend radius, or tolerances. The
advertised spacing is not a dimensioned confirmation of pitch on each leg. The
conditional material route is recorded in `newhouse-br904-retail.json`.

## One installed arrangement to investigate

The left center principal meets the header at X = -89.05, Z = 277 mm in the
uncut frame. One BR904 could bridge the principal side to the header top;
one inverted BR904 could bridge the center post to the header underside.
The two header legs would need coincident factory axes to share two
through-header bolts. Each vertical leg would use two separate bolts. The
header, principal, post, center support positions, kerf-right panels, and all
66 panel/kicker screw axes remain where they are. This is a *proposed* load
path, not proof that two supplied parts can occupy those faces.

```text
     principal  | BR904 vertical leg: two occupied holes
                |           first hole >= trial bend offset
                +-- bend at top butt -- BR904 header leg: two holes
     header     ======================  two shared through-header bolts
                +-- inverted bend --- BR904 underside leg: two holes
     center post| BR904 vertical leg: two occupied holes
```

The scripts use a **hypothetical** 34.5 mm first vertical hole offset and
36.5125 mm first horizontal offset, then applies Newhouse's advertised
47.625 mm spacing to *both* legs as a trial assumption. Neither first offset
nor the two actual leg pitches is a BR904 factory measurement. At 1/2 in bolt
diameter, the principal hole Z axes would be 311.5 and 359.125 mm; the
shared header X axes would be -125.5625 and -173.1875 mm. The post axes
would mirror below the header at Z = 204.4 and 156.775 mm, subject to its
actual raw face and edge check. No installation hole may be marked from
these coordinates.

| Search variable | 1/2 in preferred trial | 7/16 in defect alternative |
| --- | ---: | ---: |
| Nominal principal grain ray to actual oblique end | 45.037 mm | 45.037 mm |
| Margin over 3.5D *ray-only search filter* | 0.587 mm | 6.143 mm |
| Margin after maximum radial play in nominal factory hole | -0.207 mm | 4.555 mm |
| Reversible 4D two-edge Y row band, nominal | 1.837 mm | 16.476 mm |
| Maximum symmetric Y allowance, before other errors | 0.918 mm | 8.238 mm |
| Factory-hole minus bolt diameter | 1.588 mm | 3.175 mm |

The 1/2 in trial fails the ray-only search filter if the bolt is displaced
toward the oblique end by the full nominal factory-hole radial clearance;
wood-hole play and manufacturing tolerances are not even included. It is not
a viable nominal search target without a justified centering detail or a
larger measured near-hole offset. The row band is also nearly tolerance-free.
The 7/16 in alternative widens that band but increases bolt-to-factory-hole
clearance; bearing, centering, washer coverage, load sharing, and permitted
fastener schedule would need their own basis. Neither is a formal 2024 NDS
oblique-end verdict. The ray is not the NDS square-cut end distance. The
conditional 4D two-edge requirement does not establish which edge is loaded
under each simultaneous action.

The exact placement still needs a genuine sample or a controlled BR904
drawing. Before any installed-fit verdict, record both bend-to-hole offsets,
all four hole centers, plate width, leg lengths, hole diameters, minimum
finished thickness, bend geometry, and tolerances. Then check complete wood
bores, the protected screw axes and actual screw bodies, opposed plate/washer/
nut stack, wrench access, removal, contact, and steel net section. An omitted
factory hole still weakens steel; using it or leaving it empty is a separate
joint decision. A fit sample is neither a load test nor construction approval.

The repeatable raw-CAD calculation is
`scripts/bolted_candidate_br904_center_envelope.py`. It intentionally does
not run a new frame solve or claim the center joint is viable. This one
concept is the only BR904 layout under current development; the alternative
changes bolt diameter solely to test the governing nominal edge margin.
