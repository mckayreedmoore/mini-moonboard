# Conditional purchasing specification for the 104 structural stacks

This worksheet turns the [assembly census](README.md) into a finite bolt,
nut and washer specification. It covers eleven candidate families, including
the isolated top-corner 4×6 correction, and three retained families: **104
bolts, 104 nuts and 208 separate washers**. The 66 purchased Hillman screws
remain separate. It changes no geometry, frozen response, hardware selection
or physical-release status. Main owns the joint conclusions and integration.

Use the named catalog routes below with the stated axial profile. A supplier
drawing or a checked matched stack can establish that profile; a catalog
nominal length and a minimum thread-length field cannot establish it alone.
This is a conditional purchasing specification, not a claim that any delivered
parts have been inspected. Actual/Disposition cells remain blank.

The frozen stack/profile source uses the preserved six-joint
`all-outer-corner-frame-attempt01/`:
`comparison.json` SHA-256
`ec69b49c821a56fdde76d94148405f9f743e4f72add17c89d35af512be76f6a3`,
and `response.npz` SHA-256
`aa70480aa18c33bb1cbd7d3a53ff582a0c7a90c93487f92721619474ec251901`.
The [producer](hardware_engagement.py) reads saved geometry and source records;
it does not rebuild CAD or solve the frame. Its local output directory is
`rawlocal/hardware-engagement/`.
Current force comparisons use `two-receiver-frame-attempt03/`; the dimensional
family tables below do not depend on the old force values. The central-seat
section preserves its six-joint force arithmetic and links the current
catalog-opening comparison separately.

## Order description and dimensional rules

Specify right-hand coarse Unified threads, a partially threaded hex cap
screw to ASME B18.2.1, and the correct diameter/pitch. The quarter-inch and
retained families use a conditional SAE J429 Grade 5 bolt / SAE J995 Grade 5
finished-hex nut route. The top-side listing route uses a Grade 8 bolt and
Grade 8 nut. External 2A and internal 2B are the declared matched class
scenario; where a catalog does not state final coated thread class, that is
an exact supplier fact to resolve. No bolt grade establishes washer yield,
wood resistance or an adopted dowel-bending strength.

All axial dimensions start at the bearing face under the bolt head. `LB`
means the end of the full-diameter body at the last thread scratch; count
transition/runout as threaded wood bearing. A full-diameter cylinder drawn
in CAD is not a delivered shank.

For each ordered wood receiver with under-head interval `[a,b]`, require
`LB ≥ b − (b−a)/4` for the conditional NDS §12.3.7.2 nominal-diameter
route. Apply that test to **every member**, including each of the three
members on a continuous knee-side bolt. The family table reports the
largest requirement over its axes and maximum head-washer thickness.
The separate interface table below identifies where a smooth shank crosses
each shear plane. Smooth shank at a shear plane alone does not establish
the threaded-bearing limit throughout its adjoining members.

The conservative external-thread window below runs from the earliest nut
bearing face to the latest far nut face over the washer/nut ranges. Specify
first full-form male thread at or before its lower bound and last full-form
male thread at or after its upper bound. This sufficient coverage condition
allows the matched nut's entire active internal thread to engage at its
seat. The nut's entry and exit chamfers still need dimensions: outer nut
height is not full-form engagement length, and no stripping capacity is
assigned from that height.

`Lmin` adds three nominal pitches beyond the latest physical nut face. This
is the already-declared top-corner fit scenario extended here as a comparable
order option, not a universal installation rule or a new structural gate.
It is physical tip projection, not three guaranteed full-form threads past
the nut. Earlier 3.175-mm endpoint comparators remain historical. A part
that misses this option is not thereby a failed joint.

## Family specification

Dimensions are millimetres. The wood grips are frozen model dimensions;
washer and nut ranges are the conditional catalog stack below. Numbers
shown to four decimals are calculations, not shop measurement precision.

| Family | Count | Diameter / pitch | Wood grip | Proposed nominal order class | `Lmin`, three-pitch option | Minimum `LB`, each-member route | External full-form thread must cover |
| --- | ---: | --- | ---: | --- | ---: | ---: | --- |
| Ordinary | 44 | 1/4-20 | 127.0 | 6 in | 140.6144 | 119.5070 | 129.5908–136.8044 |
| Unchanged side | 12 | 1/4-20 | 177.8 | 8 in | 191.4144 | 157.6070 | 180.3908–187.6044 |
| Top rail, corrected | 4 | 1/4-20 | 177.8 | 8 in | 191.4144 | 144.9070 | 180.3908–187.6044 |
| Top side, corrected | 4 | 5/16-18 | 177.8 | 8 in | 194.2507 | 158.2166 | 181.0512–190.0174 |
| Outer post | 4 | 1/4-20 | 76.2 | 4 in | 89.8144 | 68.7070 | 78.7908–86.0044 |
| Center post | 4 | 1/4-20 | 127.0 | Named 6-in alternative to unsourced 5.75-in class | 140.6144 | 119.5070 | 129.5908–136.8044 |
| Center principal | 4 | 1/4-20 | 122.0 | 5.5 in, profile-specific | 135.6144 | 114.5070 | 124.5908–131.8044 |
| Center post/header | 4 | 1/4-20 | 167.0 | 7.5 in | 180.6144 | 136.8070 | 169.5908–176.8044 |
| Center principal/header | 4 | 1/4-20 | 172.8 | 7.5-in lead unresolved for this body route; proposed 8-in alternative | 186.4144 | 165.3070 | 175.3908–182.6044 |
| Inner knee/header, both directions | 4 | 1/4-20 | 177.1 | Named 8-in alternative to unsourced 7.75-in class | 190.7144 | 169.6070 | 179.6908–186.9044 |
| Continuous knee side, three members | 4 | 1/4-20 | 215.9 | 9.5 in, supplier specification needed | 229.5144 | 195.7070 | 218.4908–225.7044 |
| Retained front rail/post | 4 | 3/8-16 | 76.2 | 4 in | 94.8055 | 69.3166 | 79.4512–90.0430 |
| Retained rear rail/leg | 4 | 3/8-16 | 88.9 | 4.5 in | 107.5055 | 78.8416 | 92.1512–102.7430 |
| Retained upper leg | 4 | 1/2-13 | 177.8 | 8 in, length-specific for this projection option | 201.7463 | 158.9278 | 182.1688–195.8848 |
| **Total** | **104** | | | | | | |

The family names reconcile to the frozen axis CSV; the ordinary source ID
still ends in `_48`, and the side source ID in `_16`. Their current counts
are 44 and 12 after the four top-rail and four top-side overrides. Two
inner knee/header axes place 139.0-mm block last; the other two place
38.1-mm header last. Their shared 177.1-mm grip does not make their `LB`
requirements equal. Keep one continuous knee-side bolt through three wood
members, with washers only at the two exterior faces.

The following shear-plane coordinates use the maximum head-washer thickness.
For smooth shank at an interface, its body must reach that coordinate. The
`LB` requirement in the preceding table additionally checks threaded bearing
in the full length of every receiver; use the larger applicable bound.

| Ordered wood bearing lengths, head to nut (mm) | Current axes | Shear-plane coordinates from under-head, at maximum head washer (mm) |
| --- | ---: | --- |
| Ordinary, 88.9 → 38.1 | 40 | 90.9320 |
| Ordinary, 38.1 → 88.9 | 4 | 40.1320 |
| Unchanged side, 88.9 → 88.9 | 12 | 90.9320 |
| Corrected top rail, 38.1 → 139.7 | 4 | 40.1320 |
| Corrected top side, 88.9 → 88.9 | 4 | 91.5416 |
| Outer post, 38.1 → 38.1 | 4 | 40.1320 |
| Center post, 88.9 → 38.1 | 4 | 90.9320 |
| Center principal, 83.9 → 38.1 | 4 | 85.9320 |
| Center post/header, 38.1 → 128.9 | 4 | 40.1320 |
| Center principal/header, 134.7 → 38.1 | 4 | 136.7320 |
| Inner knee/header, 38.1 → 139.0 | 2 | 40.1320 |
| Inner knee/header, 139.0 → 38.1 | 2 | 141.0320 |
| Continuous knee side, 38.1 → 88.9 → 88.9 | 4 | 40.1320 and 129.0320 |
| Retained front, 38.1 → 38.1 | 4 | 40.7416 |
| Retained rear, 38.1 → 50.8 | 4 | 40.7416 |
| Retained upper leg, 88.9 → 88.9 | 4 | 92.2528 |

These are bearing lengths on the bolt axis, not stock-section labels or a
drill schedule. The saved per-axis report retains the actual receiver IDs
and intervals; mirrored members do not inherit each other's force results.

## Matched nut and washer envelopes

Use one head washer and one nut washer per stack. These are compatible
nominal-size catalog routes, not selected or received combinations.
Thickness enters the axial table; ID/OD and head/nut bearing faces enter
the separate support and washer-transfer work.

The [bearing-face source check](bearing-face-basis.md) now distinguishes
the standard's head gage-plane diameters from actual flat bearing circles.
Conditional head gage minima are 10.01268 mm for rail and 11.43 mm for side
bolts; neither proves the model's 10/12 mm flat circles at both head and nut.
Nut-face minima and washer yield remain unresolved. An illustrative
same-source side-circle reduction gives 109.046 MPa required strip stress;
the original 198.153 MPa rail requirement remains governing. This supplies
no hardware-failure or stronger-hardware conclusion.

| Stack scope | Nut route; thickness / across flats | Washer route; ID / OD / thickness | Quantity |
| --- | --- | --- | --- |
| 84 quarter-inch candidate stacks excluding corrected top rails | K.L. Jack `25CNFH5Z`, Grade 5, 2B; 5.3848–5.7404 / 10.8712–11.1252 | K.L. Jack `25NWUS`, Type A Wide low-carbon steel; 7.7978–8.3058 / 18.4658–19.0246 / 1.2954–2.0320 | 84 nuts, 168 washers |
| Four corrected top rails | [Bolt Depot 2569](https://boltdepot.com/Product-Details?product=2569), Grade 5; same dimensional range as above; class/chamfers not listed | [Bolt Depot 2994](https://boltdepot.com/Product-Details?product=2994), low-carbon USS; same dimensional range as above | 4 nuts, 8 washers |
| Four corrected top sides | [Bolt Depot 2583](https://boltdepot.com/Product-Details?product=2583), Grade 8; 6.5532–6.9342 / 12.4206–12.7000 | [Bolt Depot 2995](https://boltdepot.com/Product-Details?product=2995), low-carbon USS; 9.3980–9.9060 / 22.0472–22.9870 / 1.6256–2.6416 | 4 nuts, 8 washers |
| Eight retained front/rear stacks | [Bolt Depot 2571](https://boltdepot.com/Product-Details?product=2571), Grade 5; 8.1280–8.5598 / 13.9954–14.3002 | [Bolt Depot 15023](https://boltdepot.com/Product-Details?product=15023), Grade 5 USS; 10.9982–11.5062 / 25.2222–26.1620 / 1.6256–2.6416 | 8 nuts, 16 washers |
| Four retained upper-leg stacks | [Bolt Depot 2573](https://boltdepot.com/Product-Details?product=2573), Grade 5; 10.8458–11.3792 / 18.6944–19.0500 | [Bolt Depot 15025](https://boltdepot.com/Product-Details?product=15025), Grade 5 USS; 13.8938–14.6558 / 34.7472–35.0520 / 2.1844–3.3528 | 4 nuts, 8 washers |

Bolt Depot identifies the nuts to ASME B18.2.2 / SAE J995 and the washers
to ASME B18.21.1; the linked pages were rechecked October 2, 2026. K.L.
Jack dimensions and the nut's explicit 2B class reuse the source-pinned
[September 30 fastener packet](../../hardware-material-specification-2026-09-30/fasteners.md).
No listed washer in this table publishes a numerical yield minimum. A
Grade 5 washer label, hardness, low-carbon description or bolt grade cannot
close washer metal resistance. The catalog ½-inch nut is at most 11.3792 mm
high; the modeled 11.5316-mm nut remains a separate occupancy envelope.

The publisher still lists [B18.2.1-2012 (R2021)](https://www.asme.org/codes-standards/find-codes-standards/b18-2-1-square-hex-heavy-hex-askew-head-bolts-hex-heavy-hex-hex-flange-lobed-head-lag-screws)
and [B18.2.2-2022](https://www.asme.org/codes-standards/find-codes-standards/b18-2-2-nuts-general-applications-machine-screw-nuts-hex-square-hex-flange-coupling-nuts),
rechecked October 2. Numerical body/gage comparisons reuse the project's
[inspected dimension-source correction](../../../bolt-dimension-source-correction.md);
the public publisher records do not expose those numerical tables.

## Named bolt routes and exact supplier questions

| Family | Existing named route | Finite disposition |
| --- | --- | --- |
| Ordinary 44 | K.L. Jack `25C600HCS5Z` | Request the ordinary axial specification above with `25CNFH5Z` nuts and `25NWUS` washers. Length/body class screens are favorable; full-form onset through the nut is not located by the listing's ¾-in thread-length field. |
| Unchanged side 12 and corrected top rail 4 | Lawson/FalconGrip `FA21103`; Motion `11706127` is a separate four-rail alternative | One 25-bolt Lawson pack supplies these 16 plus the four inner knee/header bolts, leaving five. Reuse the separate top-rail nut/washer route. Require the two different member-specific `LB` bounds even though both grips are 177.8 mm. |
| Corrected top side 4 | [Bolt Depot 28650](https://boltdepot.com/Product-Details?product=28650), 5/16-18 × 8 in Grade 8 | Listed under-head range 198.628–203.2 clears the 194.2507-mm projection option. Partial-thread / B18.2.1 / J429 are stated; minimum 1⅛-in thread does not locate `LB`, first full-form thread or nut engagement. Request the row's profile with the matching Grade 8 nut. |
| Outer post 4 | K.L. Jack `25C400HCS5Z`; historical BrightonBest `847030` | Exact four-inch length leads exist. Request the outer-post row's profile and exact-item J429/class basis; adjacent-size family data do not establish this item's profile. |
| Center post 4 | HiStrength `104-044` / `25C600HCS5P`, or the ordinary K.L. Jack six-inch lead | Use the named six-inch alternative conditionally; no exact 5.75-in SKU is needed for this proposed route. Its physical endpoint extends beyond the frozen 139.217-mm cylinder, so the assembly clearance record does not qualify that extension. |
| Center principal 4 | K.L. Jack `25C550HCS5Z` | The conditional 5.5-in table minimum `LB=114.300` misses the 114.507-mm maximum-washer requirement by 0.207 mm. Request a part-specific body bound meeting 114.507 and the stated full-form window. Nominal length alone does not establish that bound. |
| Center post/header 4 | HiStrength `104-049` / `25C750HCS5P` | Seven-and-a-half inches clears the projection option conditionally. The listed ¾-in thread-length field differs from the standard's over-six-inch one-inch reference; request the actual axial profile rather than interpreting either field as first full-form thread. |
| Center principal/header 4 | Same HiStrength 7.5-in lead; proposed Lawson `FA21103` eight-inch alternative | The standard 7.5-in `LGmax=165.100` is below the 165.307-mm full-body requirement at maximum head-washer thickness. Its standard minimum overall 185.928 also misses the optional 186.4144-mm three-pitch target by 0.4864. An eight-inch profile may satisfy the row's body and full-form window, but its nominal endpoint is 13.183 mm beyond the frozen cylinder and needs parent geometry reconciliation before substitution; no alternative is adopted here. |
| Inner knee/header 4 | Lawson `FA21103` eight-inch alternative | Use the shared 25-pack route. Require `LB≥169.607` across the reversed receiver orders; the nominal 7.75-in minimum body screen is insufficient for the two header-last axes. No exact 7.75-in SKU is needed for this proposed route. |
| Continuous knee side 4 | [Ro-Brand HC5127](https://www.robrandinc.com/screws-grade-coarse-p-310.html) | Request four 1/4-20 × 9.5-in partial-thread Grade 5 screws with B18.2.1 / J429 / final 2A basis, `L≥229.5144`, `LB≥195.707`, and full-form threads covering 218.4908–225.7044. Request package quantity and price separately. The present listing does not establish these facts. |
| Retained front 4 / rear 4 | [Bolt Depot 367](https://boltdepot.com/Product-Details?product=367) / [368](https://boltdepot.com/Product-Details?product=368) | Stated minimum lengths are 100.076 / 111.760, which clear 94.8055 / 107.5055. Preserve the distinct 38.1-mm front and 50.8-mm rear nut-side receivers; request their body/full-form profiles with the matched 3/8 nuts and washers. |
| Retained upper leg 4 | [Bolt Depot 407](https://boltdepot.com/Product-Details?product=407) | The listed 198.628–203.2-mm range does not guarantee the optional 201.7463-mm projection requirement. Specify at least 201.747 mm if using that option, plus the row's body/thread profile. This may be satisfied within the existing eight-inch nominal class; no longer bolt or new release condition is inferred. |

For HC5127, the October 2 product page still identifies nominal size and
Grade 5 coarse thread and says to call for pricing. The [supplier category](https://www.robrandinc.com/grade-screws-c-3_4_360.html)
has generic 105-ksi tensile text without a diameter band. That text does
not bind this quarter-inch item to SAE J429's applicable band; it also does
not prove the item is nonconforming. Partial threading, B18.2.1, final
thread class, body/runout/point coordinates, package quantity and price
remain exact unsupported product facts. The conditional 9.5-in standard
length/body comparison is not a product guarantee.

For a hypothetical conforming quarter-inch 9.5-in cap screw, the existing
ASME class screen gives under-head minimum 236.728 mm, `LBmin=209.550`
and `LGmax=215.900`. The first two exceed this worksheet's length/body
requirements by 7.2136 and 13.8430 mm. This shows a finite compatible
dimensional class to request; it does not turn `LG` into a first-full-form
thread or resolve HC5127's product specification. The actual point and
full-form end must still reach the stated nut interval.

Every profile request includes the actual under-head length range, body
diameter/end, first and last full-form male thread, point/runout, nut active
internal thread and chamfers. Pair the nut without shank/runout interference
at its seat. If a named part cannot meet that finite specification, return
that affected family to main for a compatible profile or a different
supported mechanics basis. Do not add spacers, move seats, drill different
holes or substitute a fully threaded bolt from this document.

## The central partial nut seat

The exception is `center_principal_right_2` on
`base_principal_center_right`, not all center-principal nuts. Keep the
existing bolt axis, F1-G1 passage and two exterior washer roles. The saved
[central-footprint scenario](../partial-seat-bearing.md) establishes full
wood support for a concentric 10-mm OD / 7.3-mm ID ring, area 36.68595 mm².
Its six-case 82.6281-N peak and 0.52267 perpendicular-bearing quotient are
from that earlier frozen response; they are not current all-outer results.

That preserved six-joint response has twelve zero/gap states. Its peak tie is
**81.364757 N at `k12-rear_gap`**, response row 1535. That index is bound
to `center_principal_right_2/outer-seat-axial-tie` by the current
`corner-frame-attempt01/row-identities.json`, SHA-256
`bec1feb75be61b321220a047a652cc42f09c4c11d1d3c66377c4035bde4826d5`;
the all-outer comparison pins that map. The older upstream row map has
different row identities and cannot identify this saved response by itself.

The finite interface is a nut/washer bearing-face and metal-transfer model
that sends its compression into the supported central region while giving
no support credit to the washer crescent over the passage. A catalog nut's
across-flats or chamfer-circle dimension does not establish that pressure
patch. A standard USS washer's full annulus is still partially unsupported.
The purchasing question is the matched nut's actual bearing-face geometry
and the washer's material/contact basis at this one station, not a request
to move the passage or buy an unproved smaller washer.

Use the real washer hole in that transfer model: the conditional quarter-inch
USS ID spans 7.7978–8.3058 mm, wider than the 7.3-mm wood bore used by the
saved ring scenario. Direct nut-to-washer pressure cannot be assigned over
the washer's empty hole. At that preserved peak and conditional DF-L No. 2
base perpendicular bearing of 4.309223 MPa, the concentric uniform-pressure
comparators are:

| Declared 10-mm outer circle, inner opening | Area (mm²) | Mean pressure (MPa) | Pressure / base perpendicular bearing | Equal-area minimum outer diameter (mm) |
| --- | ---: | ---: | ---: | ---: |
| Wood-bore-only 7.3000 mm | 36.68595 | 2.21787 | 0.51468 | 8.79379 |
| Catalog washer minimum ID 7.7978 mm | 30.78314 | 2.64316 | 0.61337 | 9.21121 |
| Catalog washer maximum ID 8.3058 mm | 24.35809 | 3.34036 | 0.77516 | 9.64505 |

Thus, a concentric supported contact ring outside the maximum washer hole
has a finite area route between approximately 9.646 and 10 mm outer diameter
under this uniform-pressure assumption. That is a contact-model interface,
not a sourced nut bearing face, a replacement washer, or a resistance pass.
The existing central ring establishes available
wood geometry; it does not establish the actual compression path, washer
bridging, tilt or pressure distribution. Those specific transfer facts
remain unproved and are parent mechanics work. No full-annulus bearing
pass or capacity reduced in proportion to the missing crescent is claimed.

The [current six-case catalog-opening comparison](../partial-seat-bearing.md#current-catalog-washer-opening-comparison)
uses the all-two-receiver force source instead: peak tie 22.525552 N at
K12-right, maximum-ID uniform pressure 0.924767 MPa and conditional wood
index 0.214602. The earlier numeric table and machine output remain frozen.
Actual nut/washer transfer is still open. The separate
[retained-washer worksheet](../retained-washer-checks.md) now binds all 24
3/8-inch and 1/2-inch exterior roles. The subsequent
[current saved-STEP support check](../retained-washer-support.md) confirms
all 24 nominal concentric annuli. Loaded shift/tilt and washer metal
acceptance remain open; frozen actual-support fields are not overwritten.

## Reproduction and record

Run the bounded producer from the repository root to verify saved arithmetic:

```sh
python3 -B docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/assembly-package/hardware_engagement.py --verify
```

The existing assembly producer and its seven outputs remain unchanged.
The supporting worker reproduced both output files byte for byte, checked all
15 direct source pins, joined all fourteen published family rows to their
numeric report fields, and reconciled the sixteen bearing-order rows to
104 axes. A separate read of the saved response confirmed the central tie
and the current row identity. All local Markdown links resolve.

| Artifact | SHA-256 |
| --- | --- |
| `hardware_engagement.py` | `d8e2a08e46fd9507a89d8e7ecb238ddf229490f4909345cbb641374ee8133295` |
| Local `rawlocal/hardware-engagement/producer.py.snapshot` | `d8e2a08e46fd9507a89d8e7ecb238ddf229490f4909345cbb641374ee8133295` |
| Local `rawlocal/hardware-engagement/hardware-engagement.json` | `93c24fe5fb421152b0294cc35106bfb6d595b558f45e0be826406405084c111a` |
| Local `rawlocal/hardware-engagement/hardware-engagement-axes.csv` | `9fd9f2f70dbaf347bf174925f21cc3d589c2640a7b42501e3b81f4533ab42cac` |

The two generated files are ignored by the existing hypotheses JSON/CSV
rules. Preparation used no software tests, native/CAD/frame runs or
independent review loop. Main owns staging and commits. These hash/count
checks authenticate the saved specification; they establish no delivered
fit or joint acceptance.
