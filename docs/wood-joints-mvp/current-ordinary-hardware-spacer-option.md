# Conditional nut-side washer-spacer option for the 48 six-inch WJ24 axes

**Screen date:** 2026-09-25. **Status:** one source-bounded dimensional
option for later review; not selected or accepted. This keeps the proposed
6 in bolt, wood grip, and bolt axis unchanged. It is not a hardware order,
strength check, CAD change, or fabrication instruction.

Using this option would add two spacers at each of the 48 nut stacks and move
each nut and its modeled bolt-tip envelope 6.096–6.604 mm outboard. This is a
proposed geometry change, not an adopted spacer or model state; a future
geometry review would be required before any implementation.

## Candidate arrangement

For the 48 axes screened at 152.4 mm nominal bolt length and 127 mm wood
grip, retain the existing wide steel washer directly against the nut-side
wood face. Place two McMaster-Carr [91201A029 steel oversized washers](https://www.mcmaster.com/product/91201A029/)
between that retained washer and the nut. The catalog lists each as for a
1/4 in screw, 0.281 in ID, 0.625 in OD, 0.120–0.130 in thick, steel,
Rockwell B84, and sold in packs of 25. Its page also says these washers may
be used as spacers and levelers and provides a traceable lot material
certificate. The product page showed in-stock status when checked on
2026-09-25; price and delivered availability are not recorded.

The added washers are smaller in outside diameter than the existing
nut-side wood-bearing washer, while their listed 0.625 in OD exceeds the
finished 1/4 in nut's 0.505 in maximum across-corners dimension. This is a
dimensional footprint comparison only. The existing washer remains in its
wood-bearing position and carries its existing footprint. The steel grade,
washer resistance, load sharing through the stack, corrosion protection,
and actual part dimensions still require review; Rockwell hardness is not a
capacity rating.

## Axial envelope screen

The baseline stack coordinates come from the
[current ordinary hardware basis](current-ordinary-hardware-basis.md):
earliest nut bearing at 128.5908 mm, farthest nut face at 137.8044 mm,
3.175 mm modeled bolt-tip extension beyond that face, and a 120.382 mm lower
bound on the under-head-to-last-scratch/body coordinate. The 3.175 mm value
is an inherited WJ05/WJ24 geometry input: the [WJ05 center-node probe](../../scripts/wood_joint_wj05_center_node_probe.py)
sets `THREAD_PAST_NUT_MM = 3.175`, while the [current WJ24 grip screen](current-grip-screen.md)
describes its shaft as an unthreaded occupancy envelope. It is not a required
amount of full-form thread beyond the nut or a published engagement rule. ASME B18.2.1-2012
Table 12 gives a 1/4 in, 6 in cap screw `LG,max` of 5.25 in (133.35 mm) and
`LB,min` of 5.00 in (127.00 mm); the over-4-in-to-6-in length tolerance for
1/4 in screws is −0.10 in, so the minimum permitted overall length is
5.90 in (149.86 mm). The local cached edition and its definitions are
identified in the linked basis note; the official [ASME standard record](https://www.asme.org/codes-standards/find-codes-standards/b18-2-1-square-hex-heavy-hex-askew-head-bolts-hex-heavy-hex-hex-flange-lobed-head-lag-screws)
lists B18.2.1-2012 (R2021) as in effect. The publicly available [CDE Grade 5/8
technical sheet](https://cdefasteners.com/sites/default/files/product-specs/capscrewgr5-8.pdf)
also reproduces the cap-screw length tolerance and explains that `LT` is a
reference dimension.

| Check | Calculation using the washer catalog range | Screen result |
| --- | --- | ---: |
| Added thickness, two washers | 2 × 0.120–0.130 in | 6.096–6.604 mm |
| Earliest nut bearing plane | 128.5908 + 6.096 | 134.6868 mm |
| Clearance beyond ASME `LG,max` | 134.6868 − 133.35 | 1.3368 mm |
| Nut far face, maximum stack | 137.8044 + 6.604 | 144.4084 mm |
| Modeled bolt-tip target, retained from WJ05/WJ24 | 144.4084 + 3.175 | 147.5834 mm |
| Minimum-length margin to modeled bolt-tip target | 149.86 − 147.5834 | 2.2766 mm |
| Minimum physical tip projection past nut far face | 149.86 − 144.4084 | 5.4516 mm |
| Body/last-scratch margin | 127.00 − 120.382 | 6.618 mm |

Thus the minimum washer stack places even the earliest nut-bearing plane
1.3368 mm beyond the 6 in cap screw's maximum grip-gage coordinate. The
maximum stack places the nut far face at 144.4084 mm. The modeled bolt-tip
target remains 3.175 mm beyond that face, at 147.5834 mm. At the 149.86 mm
minimum permitted bolt length, this tip target has 2.2766 mm of length margin
and the tip itself extends 5.4516 mm beyond the nut face. These are separate
limits: the 127 mm `LB,min` and the `LG,max` gage coordinate do not certify
functional engagement of the matched nut. The modeled tip extension does not
require full-form threads through the extension beyond the nut. The actual
bolt/nut pair must still be shown to engage through the nut's functional
thread height and seat without thread-runout interference.

## ASME point and thread-end limit review

The local cached ASME B18.2.1-2012 text was checked at §§1.5, 2.2, 2.4, 2.5.4,
2.5.5, 2.13, 4.7, and Tables 12–13. The limits apply to different parts of
the threaded length:

| Provision | What it bounds here |
| --- | --- |
| §2.2, product length | Measures from the head bearing surface to the extreme end, including the point if pointed. This supports the 149.86 mm minimum overall length. |
| §4.7 and Table 12, `LG,max` / `LB,min` | Control the head-side grip gage and body/last-scratch lengths for long screws. The screen checks these coordinates separately from thread availability at the tip. |
| §1.5 and §4.7, `LT` | Define thread length and a nominal length from the extreme end to the last complete thread for calculation. `LT` is expressly a reference dimension, not a tolerance on either end of the complete-thread region. |
| §1.5, point length | Defines point length from the point to the first fully formed thread at major diameter, determined using a cylindrical NOT GO major-diameter ring gage. It gives no acceptance limit for this cap screw. |
| §2.4, screw points | Requires a chamfered point, but says point features not defined by the product standard are at the manufacturer's discretion. It gives no maximum point/chamfer length for this cap screw. |
| §2.5.4, incomplete thread | Limits the major diameter of incomplete thread to no more than the actual major diameter of full-form thread. It does not limit how far incomplete thread extends axially from the point. |
| §2.13, quality assurance | Defaults dimensional assurance to ASME B18.18 Category 2, but does not create a point-length acceptance limit where §2.4 leaves that feature undefined. |
| §§1.6 and 4.9, Grade 5 material | Identify SAE J429 as a mechanical/material standard for externally threaded fasteners and as an allowed cap-screw material standard. It does not add a point-length limit absent from §2.4. |

Therefore, ASME B18.2.1 dimensional conformity, SAE J429 Grade 5 material
conformity, `LG,max`/`LB,min`, and minimum overall bolt length do **not** alone
guarantee functional full-height engagement with the matched nut. The washer
stack places the earliest nut face beyond the head-side gage coordinate, and
the last-scratch/body threshold remains met; the delivered nut fit still
needs verification. The retained 3.175 mm tip extension equals 0.125 in,
2.5 pitches at 1/4-20, or 0.5 bolt diameter (D = 6.35 mm). It is the existing
WJ05/WJ24 geometric shaft-end allowance, not a thread-extension requirement
or an ASME point/chamfer allowance. For this spacer stack the nut far face is
144.4084 mm; the modeled bolt tip is at 147.5834 mm. Full-form thread is not
required through that extra 3.175 mm solely to preserve the shaft envelope.
ASME's lack of a point-length limit matters only insofar as actual tip/runout
could intrude into the nut's needed threaded engagement; verify the matched
bolt/nut fit over the nut height.

An item claim of ASME B18.2.1 dimensions plus SAE J429 Grade 5 therefore does
not establish the delivered matched-nut fit. For example, the [Allied Bolt
50140 product page](https://alliedboltinc.com/product/1/4-inch-X-6-inch-HEX-CAP-SCREW-GR-5-ZINC-PLATED~50140)
claims those standards and lists 3/4 in thread length, but does not provide
item-specific thread-transition coordinates or matched-nut fit evidence. That
is a catalog example only; it is not selected for WJ24.

The standard and a catalog dimensional-conformity claim do not by themselves
establish the delivered matched-nut fit, but an exact vendor drawing is not
the only evidence route. A later receiving check of each delivered bolt and
its matched nut can verify functional thread engagement through the nut's
full height, seating against the washer without point/runout interference,
and the required physical bolt-tip location at or beyond the modeled target.
Until that matched fit is checked or bounded by an applicable item
specification, this remains a conditional gage/body geometry screen, not a
verified nut fit.

## Future geometry and quantity effects

For each of the 48 affected axes, the proposed arrangement inserts
6.096–6.604 mm between the retained wood-bearing washer and the nut. The nut,
its far face, and modeled bolt-tip target move outboard by the same amount;
the existing washer against wood stays in place. Keep the wood grip, member
locations, bolt axis, and head-side washer unchanged if this option is later
reviewed. A future geometry check must assess the 6.604 mm maximum outboard
envelope and added washer/nut access against neighboring parts. No such
geometry change is made or adopted by this note.

This arrangement adds two washers per affected axis: 96 pieces for 48 axes.
The catalog package is 25, so four packs would supply 100 pieces, leaving four
spares. This is quantity arithmetic only; the listing's temporary stock state
and price do not establish availability or cost for a later build.

The spacer dimensions put the nut beyond the gage coordinate while preserving
the inherited physical bolt-tip envelope, but this is only a conditional
screen. At minimum permitted bolt length, the modeled tip target is 2.2766 mm
inboard of the permitted bolt end, while the physical tip extends 5.4516 mm
past the maximum nut face. Neither figure proves functional thread fit. The
`LG`/`LB` comparison applies only to a selected 1/4-20 × 6 in cap screw that
conforms to ASME B18.2.1; do not transfer those limits to a generic hex bolt.
The no-spacer 6 in fit remains unresolved: its `LG,max` coordinate is
4.7592 mm beyond the earliest nut face, so the spacer's improved coordinate
screen does not establish product fit. No item is selected, and no washer or
bolt resistance is assigned.

## Sources

- McMaster-Carr item [91201A029](https://www.mcmaster.com/product/91201A029/),
  accessed 2026-09-25; dimensions, material, hardness, traceable certificate,
  package quantity, and displayed stock status.
- Allied Bolt Products [catalog page for item 50140](https://alliedboltinc.com/product/1/4-inch-X-6-inch-HEX-CAP-SCREW-GR-5-ZINC-PLATED~50140),
  accessed 2026-09-25; claims ASME B18.2.1 dimensional conformity and SAE
  J429 Grade 5, lists 3/4 in thread length, but provides no point-length
  limit.
- ASME [B18.2.1 standard record](https://www.asme.org/codes-standards/find-codes-standards/b18-2-1-square-hex-heavy-hex-askew-head-bolts-hex-heavy-hex-hex-flange-lobed-head-lag-screws),
  checked 2026-09-25 and listing B18.2.1-2012 (R2021) as in effect;
  §§1.5, 1.6, 2.2, 2.4, 2.5.4, 2.5.5, 2.13, 4.7, 4.9 and Tables 12–13 are checked
  against the local cached B18.2.1-2012 text as documented in the [ordinary
  hardware basis](current-ordinary-hardware-basis.md).
- CDE Fasteners [Grade 5/8 cap-screw technical sheet](https://cdefasteners.com/sites/default/files/product-specs/capscrewgr5-8.pdf),
  accessed 2026-09-25; standard dimensions, reference `LT`, and length
  tolerance table.
