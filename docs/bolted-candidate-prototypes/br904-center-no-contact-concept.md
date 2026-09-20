# BR904 center joint: no-contact geometry concept

Status: search envelope only. No sample has been measured. No connector, bolt
diameter, hole, joint resistance, or drilling pattern is selected.

The exact [Newhouse BR904](https://newhouseelectric.com/products/bracket-90deg-4-hole)
is listed at [Home Depot](https://www.homedepot.com/p/325186317).
[Lowe's lists Adamax BR904](https://www.lowes.com/pd/Adamax-Electro-Galvanized-1-2-in-Angled-Strut-Bracket-with-4-Holes-Strut-Channel-Joining-Accessory/5002818545),
and [Newhouse says it is by Adamax Inc.](https://newhouseelectric.com/pages/about-us).
This supports a common branded model, not controlled identity of every
factory lot or received part. Newhouse states
four factory 9/16 in holes with 1-7/8 in spacing, 4-gauge Q235 steel, and an
electro-galvanized finish. It does not give bend-to-hole centers, plate width,
leg lengths, finished minimum thickness, bend radius, or tolerances. The
advertised spacing is not a dimensioned confirmation of pitch on each leg. The
conditional material route is recorded in `newhouse-br904-retail.json`.
The live manufacturer page links only a product photograph. Home Depot's
overall 4 in length and a reseller's unlabelled three-number size cannot
locate a hole relative to the bend or establish minimum finished thickness.
The published pitch is useful for a trial envelope, not a drilling datum.

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

The script uses a **hypothetical** 34.5 mm first vertical hole offset and
36.5125 mm first horizontal offset, then applies Newhouse's advertised
47.625 mm spacing to *both* legs as a trial assumption. Neither first offset
nor the two actual leg pitches is a BR904 factory measurement. At 1/2 in bolt
diameter, the principal hole Z axes would be 311.5 and 359.125 mm; the
shared header X axes would be -125.5625 and -173.1875 mm. The post axes
would mirror below the header at Z = 204.4 and 156.775 mm, subject to its
actual raw face and edge check. No installation hole may be marked from
these coordinates.

| Search variable | 1/2 in comparator | 7/16 in diagnostic |
| --- | ---: | ---: |
| Nominal principal grain ray to actual oblique end | 45.037 mm | 45.037 mm |
| Margin over 3.5D *ray-only search filter* | 0.587 mm | 6.143 mm |
| Margin after maximum radial play in nominal factory hole | -0.207 mm | 4.555 mm |
| Minimum near-hole vertical offset including nominal hole play | 34.659 mm | 31.010 mm |
| Reversible 4D two-edge Y row band, nominal | 1.837 mm | 16.476 mm |
| Maximum symmetric Y allowance, before other errors | 0.918 mm | 8.238 mm |
| Further symmetric Y allowance after nominal hole play | 0.125 mm | 6.651 mm |
| Factory-hole minus bolt diameter | 1.588 mm | 3.175 mm |
| Nominal factory hole within ordinary NDS bolt-hole range | Yes, at limit | No |

The 1/2 in trial fails the ray-only search filter if the bolt is displaced
toward the oblique end by the full nominal factory-hole radial clearance;
wood-hole play and manufacturing tolerances are not even included. It is not
a viable nominal search target without a justified centering detail or a
a larger measured near-hole offset. At the 34.659 mm threshold, the 1/2 in
trial has only about 0.058 mm further symmetric Y allowance after nominal
steel-hole play, before wood-hole, fabrication, or receiving variation. The
row band is thus also nearly tolerance-free.
The 7/16 in diagnostic widens that band, but its 1/8 in diametral steel-hole
clearance exceeds the ordinary 1/16 in maximum in
[2024 NDS §12.1.3.2](https://awc.org/wp-content/uploads/2026/08/AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-%E2%80%93-Dowel-type-fasteners.pdf).
It is **not an installable alternative under that ordinary bolt provision**.
A separate justified method would be needed before evaluating its bearing,
centering, washer coverage, load sharing, and fastener schedule. Neither
column is a formal 2024 NDS
oblique-end verdict. The ray is not the NDS square-cut end distance. The
conditional 4D two-edge requirement does not establish which edge is loaded
under each simultaneous action.

[2024 NDS §12.1.2.2](https://awc.org/wp-content/uploads/2026/08/AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-%E2%80%93-Dowel-type-fasteners.pdf)
defines bolt end distance from a square-cut end. Its separate sloping-end
figure for split-ring/shear-plate connectors in Chapter 13 cannot be
transferred to these bolts. A completed wood check still needs a defensible
oblique-end interpretation and the actual simultaneous load direction.

The exact placement still needs a genuine sample or a controlled BR904
drawing. Before any installed-fit verdict, record both bend-to-hole offsets,
all four hole centers, plate width, leg lengths, hole diameters, minimum
finished thickness, bend geometry, and tolerances. Then check complete wood
bores, the protected screw axes and actual screw bodies, opposed plate/washer/
nut stack, wrench access, removal, contact, and steel net section. An omitted
factory hole still weakens steel; using it or leaving it empty is a separate
joint decision. A fit sample is neither a load test nor construction approval.
The shared-header receiving screen in
`scripts/bolted_center_stack_receiving.py` now accepts an exact BR904
inventory label, but returns unresolved while either measured plate thickness
or the other delivered stack dimensions are absent. An illustrative
conditional grip result is not product acceptance.

The repeatable raw-CAD calculation is
`scripts/bolted_candidate_br904_center_envelope.py`. It intentionally does
not run a new frame solve or claim the center joint is viable. This one
concept is the only BR904 layout under current development; the alternative
changes bolt diameter solely to test the governing nominal edge margin.
