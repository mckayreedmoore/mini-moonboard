# HL53 separated-rib component comparison

Status: **all three nominal cases reject; no connected architecture verdict**.
This is a coarse comparison of one wood layout at 480, 520, and 560 mm rib
center spacing. The companion JSON records the modeled solids, bolt checks,
and collision classes. It is not a complete joint, rating, or drilling plan.

The [Simpson Strong-Tie connector catalog](https://www.strongtie.com/resources/literature/wood-construction-connectors-catalog)
and its [HL angle dimensions page](https://dhcsupplies.s3.us-east-2.amazonaws.com/Documents/simpson-strong-tie/hl-angles.pdf)
provide the nominal HL53 2.5-in bend length, 5.75-in leg reach, and two
1/2-in bolt positions per flange at 2 and 4.5 in from the bend. The model
uses ideal 7-gauge plate, 9/16-in hole, 1/2-in bolt, 25.4-mm washer, and
38.1-mm tool envelopes. These are fit assumptions, not delivered dimensions
or specified bolt stacks. No catalog load value is adopted.

The catalog's **88.9-mm (3.5-in) minimum wood thickness** is checked at
every modeled bolt center in the bolt-through direction, independently of
bore overlap and collision. A narrow centerline cylinder samples the actual
uncut receiver; its intersected length is reported for each bolt in JSON.
All 32 header-link receivers meet the nominal minimum: 88.9 mm through the
front/rib principals and header, and 184.15 mm through the central post.

The fixed front carriers are two widened, one-piece principal profiles at
X = ±70 mm and a single central backing post at X = ±92.075 mm. The backing
post supports the kerf-right kicker seam and retains the four center kicker
screw receivers. Separate 88.9-mm-wide principal/post ribs sit at X = ±240,
±260, or ±280 mm. Each principal profile extends 80 mm rearward. A one-piece
raised header spans the ribs, Y = -250 to -36 mm and Z = 238.9 to 327.8 mm
in the central region. The six affected side rails end 15 mm beyond the rib
outer faces, at |X| = 299.45, 319.45, or 339.45 mm. No lap or custom steel
is modeled.

Eight HL53 bodies link the front principals and central backing post, and
the separated upper/lower ribs, to that header. Every body includes both
flanges with two nominal holes cut from each. Every one of the 32 header-link
bolt cylinders intersects its own bracket hole corridor and receiving wood;
the modeled wood bores are contained. The front carriers and structural
ribs/posts have zero volumetric overlap. The fixed six panel solids, 66
panel/kicker screw axes, and their wood receivers remain in place. The
original 12 frame axes are screened against the changed hardware.

The earlier HL53 outward-seat header-bore sign is quarantined here: each
seat axis is computed as `face_x + seat_direction × offset`, then checked
inside its own flange. No earlier outward-seat hole axes are imported. All
modeled bolts meet their own hole corridor and receiver, including the rail
probe below.

All three spacings fail because the 146.05-mm HL53 seat reaches into the
neighboring rib or front carrier. Its washer and access envelopes also
meet that wood. At 480 and 520 mm, some header-link bolt paths meet the
neighboring wood; that particular bolt-path clash clears at 560 mm, while
the bracket-body and washer/access clashes remain. No case earns an
assemblable header-link verdict.

One ninth HL53 was probed only at the **520-mm bottom-right rail end**. Its
four bolts meet their own holes and have some receiver wood. Both seat
bores exit the shaped rail, however, and the access envelope meets a panel.
Those two rail-seat bolt centers have only **49.904 mm** of local wood along
the vertical bolt axis, below the HL53 88.9-mm minimum. The trimmed rail
retains its original 38.1-mm (1.5-in) section; resection did not turn it
into a 3.5-in-thick receiver. This is an independent catalog-applicability
failure: the 520-mm rail probe is **catalog-inapplicable** even if its bore
and access clashes were resolved.
The other five rail ends have no factory bracket in this model. Thus the
15-mm rail gaps and failed single probe prevent any connected architecture
verdict, regardless of the header-link results.

Delivered HL53 tolerances, actual bolt heads/nuts/washers and tool sweep,
wood edge/end distances, joint resistance, and the full frame load path
remain unresolved. No material property, connector rating, fabrication, or
drilling is released.
