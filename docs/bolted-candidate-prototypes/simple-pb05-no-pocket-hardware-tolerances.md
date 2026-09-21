# PB05 no-pocket outer blocks: retail hardware tolerance and receiving gates

Status (2026-09-21): **nominal axial fit only; no retail-part worst-case acceptance, drilling,
fabrication, or structural approval.** This independent desk review concerns the twelve
1/4-20 × 8 in outer-upright through bolts in the six detached PB05 narrower-block stations.
No supplier was contacted and no material was bought or measured. The PB05 screen models
95.25 × 57.15 × 300 mm blocks, an uncounterbored 184.15 mm upright wood grip, and two
upright bolts per block. Its separate 5 in rail bolts are not qualified by this review.

## Evidence ledger

| ID | Evidence and product identity | What it establishes | What it does **not** establish |
| --- | --- | --- | --- |
| E1 | [PB05 detached screen](../../scripts/simple_pb05_narrow_outer_screen.py), using the [PB03 hardware constants](../../scripts/simple_pb03_outer_counterbore_revision.py) | Modeled 184.15 mm wood grip, 8 in shaft, 0.065 in washer at **each** end, 0.226 in nut, and two 1/4-20 pitches of projection. Its 0.734 in washer OD and 0.505 in nut across-corners values are collision envelopes. | Delivered wood, product dimensions, usable thread, torque, or strength. The PB05 geometry-only result is not an installed-part inspection. |
| E2 | Home Depot [Everbilt 800696](https://www.homedepot.com/p/204281626), 1/4-20 × 8 in zinc hex bolt (single), and the retailer's [8 in product Q&A](https://www.homedepot.com/p/questions/1-4-in-20-x-8-in-Zinc-Plated-Hex-Bolt-25-Pack-800690/204281625/2) | Retail lead and nominal 8 in length; the Q&A lists 6 in thread length for the 8 in bolt family. The listing describes A307. | A controlled 800696 underhead length interval, first/last **complete usable** thread coordinates, runout/chamfer, or a stated B18.2.1 edition and dimensional conformance. A307 is a material specification, not a dimensional certificate; see [ASTM A307](https://store.astm.org/a0307-21.html). Mixed Q&A answers are not an inspection record for this SKU. |
| E3 | Home Depot [Prime-Line 9058821](https://www.homedepot.com/p/310465152), 1/4-20 × 8 in A307 Grade A hex bolts (10-pack) | An alternative retail lead whose listing explicitly claims ASME B18.2.1 and ASTM A307 Grade A. This is stronger evidence for applying a **conditional** B18.2.1 length row to that SKU than E2 provides. | A measured lot, exact complete-thread start/end, or interchangeability of its thread pattern with Everbilt's 6 in listing. The page calls the bolt zinc plated while a specification field says uncoated; verify the delivered label/finish. |
| E4 | Home Depot [Everbilt 807210](https://www.homedepot.com/p/204284538), 1/4 in zinc flat washer (100-pack), and [size-filter result](https://www.homedepot.com/b/Hardware-Fasteners-Washers-Flat-Washers/1-4-inch/0734-in/0065-in/N-5yc1vZc2ckZ1z1bszxZ1z23290) | The exact modeled washer-size retail lead: listed 0.734 in OD and 0.065 in thickness. The [Home Depot generic USS chart](https://www.homedepot.com/catalog/pdfImages/4a/4a362438-0e50-481c-af25-7f98aa28c057.pdf) shows 5/16 in ID, 0.734 in OD and 0.065 in thickness for a 1/4 in pattern. | Lot-specific ID/OD/thickness limits or proof that this retail washer satisfies a structural cut-washer requirement. A [Fastenal specification](https://www.fastenal.com/content/product_specifications/FW.LC.USS.A.Z.00.pdf) for **its own** 1/4 in Type A wide washer gives 0.051–0.080 in thickness; those are not 807210 limits. |
| E5 | Lowe's [Hillman 490622](https://www.lowes.com/pd/Hillman-1-4-in-x-20-Zinc-Plated-Steel-Hex-Nut/1001265718), zinc 1/4-20 hex nut (12-count) | Retail 20 TPI nut lead for a 1/4 in bolt. | Nut height, across-flats/corners range, effective threaded height, thread fit/strength, or conformance to [ASME B18.2.2-2022](https://www.asme.org/codes-standards/find-codes-standards/b18-2-2-nuts-general-applications-machine-screw-nuts-hex-square-hex-flange-coupling-nuts). The page's “Grade 2” general prose and “All-Purpose” grade field are not a product-specific grade certificate. A [Fastenal U-bolt kit specification](https://www.fastenal.com/content/product_specifications/UBOLT.LT.4FHN.HDG.08.pdf) gives 0.212–0.226 in height and 0.428–0.438 in across flats for **different** hot-dip-galvanized hex nuts; it only illustrates a possible size family. |
| E6 | [ASME B18.2.1-2012 (R2021)](https://www.asme.org/codes-standards/find-codes-standards/b18-2-1-square-hex-heavy-hex-askew-head-bolts-hex-heavy-hex-hex-flange-lobed-head-lag-screws) and bolt-maker [length-tolerance table](https://www.portlandbolt.com/technical/faqs/bolt-length-tolerance/) | For a **non-pointed hex bolt** of 1/4–3/8 in diameter longer than 6 in, the published B18.2.1 rendition shows +0.10/−0.18 in length. Hex-bolt length is [measured under the head](https://www.portlandbolt.com/technical/faqs/bolt-length/). | An unconditional tolerance for 800696; the pointed cap-screw row is a different product type. The standard's existence does not certify a retailer lot. |
| E7 | Bolt-maker [thread-length](https://www.portlandbolt.com/technical/faqs/bolt-thread-lengths/) and [runout](https://www.portlandbolt.com/technical/faqs/thread-runout/) explanations | A usual B18.2.1 hex-bolt pattern above 6 in is `2D + 1/2 in`, or 1 in at 1/4 in diameter. Runout is not complete usable thread; the explanation finds no specified maximum runout for an ordinary hex bolt. | A 1 in thread-length claim for either actual SKU, or a bound on its first complete thread. Everbilt's listed 6 in thread length differs markedly from that usual pattern. The 1/4 in cap-screw transition value must not be transferred to a hex bolt. |

The Everbilt washer in E4 is **not** the 5/8 in OD Hillman washer used in an earlier cost
illustration. The modeled 0.226 in nut height and 0.505 in across-corners envelope are not
published Hillman 490622 limits. Retail availability varies by store and date; online listings
identify candidates, not assured local stock or a matched assembly.

## Axial stack and actual-thread acceptance

All lengths below are measured from the underside of the bolt head. Let `G` be the installed
wood grip along this bolt, `W_h` and `W_n` the installed washer thicknesses, `H` the nut's
installed bearing-face-to-outer-face height, `L` the actual underhead bolt length, `S` the
first complete usable external-thread coordinate after the shank/runout, and `E` the last
complete usable external-thread coordinate before the tip chamfer. `P = 2/20 in = 0.100 in
= 2.54 mm` is the PB05 **design target**, not a published A307/Everbilt or wood-joint rule.
Decide whether it requires two *complete* exposed thread pitches; the stricter gate below
uses that definition. The nut bearing plane is `B = W_h + G + W_n`.

Nominal modeled reach is:

`203.2000 − [184.1500 + 2(1.6510) + 5.7404 + 2.5400] = +7.4676 mm`.

The nominal nut bearing plane is `187.452 mm` from the head, with outer nut face at
`193.1924 mm`. These numbers use modeled dimensions only. **If** the applicable non-pointed
B18.2.1 length row governs an exact received bolt, `L_min = 8 − 0.18 = 7.82 in =
198.628 mm`: holding all other inputs nominal leaves `+2.8956 mm`. The `−4.572 mm`
length sensitivity is conditional, **not** an Everbilt allowance or a complete worst case.
For reference, a usual 1 in terminal thread pattern would place its nominal transition near
7 in/177.8 mm; Everbilt's listed 6 in would imply about 2 in/50.8 mm. Neither subtraction
locates `S`, because the listed thread length, runout and delivery tolerance are unresolved.

For an accepted group of received parts and cut wood, use measured or product-controlled
bounds, including measurement uncertainty, in **both** inequalities:

1. **Nut can seat on complete thread at minimum grip:**
   `S_max ≤ W_h,min + G_min + W_n,min`. Confirm by assembling the actual washer–wood–washer
   stack: the nut must reach the far washer without stopping on the shank/runout, and its
   required engaged height must be on complete threads.
2. **Nut and projection fit at maximum grip:**
   `E_min ≥ W_h,max + G_max + W_n,max + H_max + P_required` when two complete exposed pitches
   are required. Also require `L_min ≥` the same right-hand side for physical tip reach.
   If a project-approved target concerns physical tip rather than complete threads, state
   that explicitly and still prove complete thread through the nut's effective engaged
   height. `E_min ≤ L_min` normally makes usable-thread reach the stricter check.

The resulting worst-case head-to-tip demand is
`G_max + W_h,max + W_n,max + H_max + P_required`; compare it with **actual** `L_min` and
**actual** `E_min`. Relative to the nominal model, any excess grip, washer or nut height,
required projection, or unusable tip consumes the 7.4676 mm. If the conditional 4.572 mm
shortfall is used, their combined extra demand must stay at or below **2.8956 mm** before
allowing for the incomplete tip. For example, only under nominal washers/nut/projection and
the conditional length row would `G_max ≤ 187.0456 mm` follow. This is a sensitivity
threshold, **not** a lumber acceptance tolerance. No finite SKU-backed worst-case reserve
can be asserted from the reviewed listings.

## Necessary receiving and measurement gates

- Fix the exact bolt, washer and nut models/finish, plus the required complete nut engagement
  and exposed-thread criterion. Do not combine the Everbilt 6 in thread claim with the
  Prime-Line B18.2.1 claim. If a different 8 in bolt or a locknut is substituted, redo the
  stack and tool envelopes for that actual part.
- For each delivered bolt (or a traceable controlled lot with justified sampling), record
  underhead `L`, diameter/body form, `S` after runout, `E` before chamfer, and the axial
  shank/thread occupancy in **each** wooden member. A nominal thread-length label alone is
  insufficient. Check the nut on the actual bolt through full installation travel.
- Measure both washers individually for thickness, ID, OD, flat seating and material/pattern;
  measure each nut's height, across flats/corners, thread fit, and effective threaded height.
  Confirm washer bearing on both faces and the real socket/wrench access against the PB05
  clearances. The 0.734 in OD washer and 0.505 in nut envelope used by CAD are only nominal
  clearance inputs. Resolve the applicable washer bearing requirement separately.
- Measure the finished **no-pocket** wood grip at every one of the twelve upright axes,
  including face flatness and assembly gaps. Establish `G_min` and `G_max`; the 184.15 mm
  model is not a purchased-lumber tolerance. Recheck the 95.25 mm block size and hole/edge
  placement against the delivered stock before drilling.
- Apply the two inequalities to the **same** selected part family and measured wood range,
  with tool uncertainty. Make a dry assembly of each limiting stack to witness nut seating,
  full engagement, projection and accessible tightening. Record failures as hold/reselect;
  do not rescue reach by omitting a washer, accepting partial nut engagement, or cutting an
  unstudied pocket.

Passing these dimensional gates would establish only hardware fit for the no-pocket upright
stacks. PB05's rail bolts, washer bearing classification, thread-root/bending-yield basis,
wood bearing and net sections, contact and same-case joint actions, transport and complete
structural acceptance remain separate open work. There is **no structural or fabrication
release** here.
