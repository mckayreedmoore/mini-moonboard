# Integrated barrel frame: owner decision sheet

22 September 2026. This is the **kerf-right, barrel-nut development candidate**
shown in the [interactive rear viewer][viewer], not the selected angle-frame
shop packet or a drilling, fabrication, load-test, or climbing release. The
[source-built assembly](../../scripts/export_owner_barrel_scene.py) is the
authority for the modeled pose. No separate corner blocks, kicker backers,
angles, or structural SDS screws are in this candidate view.

## What is in the one assembly

The two seam-side 88.9 × 139.7 mm modeled center posts receive all four fixed
center kicker screws and each joins the header through two barrel pairs.
The 66 panel/kicker screw axes and 12 retained frame-bolt axes are unchanged.
The 24 former angle duties have the following **trial** connections. A row
count is a fastener inventory, not a complete-joint capacity or proof that
the old bracket's moment path has been replaced.

| Physical connection | Former duties | Trial bolt/barrel pairs | Present disposition |
| --- | ---: | ---: | --- |
| Bottom/lower/upper outer rails to side framing | 6 | 12 | `REVISE`; 6-in reach and service unqualified |
| Bottom/lower/upper center rails to center framing | 6 | 12 | `REVISE`; shifted left rows need wood and tolerance checks |
| Top rail to outer and center posts | 4 | 8 | `REVISE`; joint resistance unqualified |
| Outer base to side members | 2 | 4 | `REVISE`; 10-mm inward trial axes |
| Outer header to outer posts | 2 | 4 | `REVISE`; recessed heads and rim-first service |
| Header to center posts | 2 | 4 | `VIEWER_ONLY_UNVERIFIED` |
| Center principals to header | 2 | 2 | `VIEWER_ONLY_UNVERIFIED`; one angled bolt per side |
| **Total** | **24** | **46** | **No accepted structural joint** |

The [integrated backing trace](../../scripts/owner_barrel_integrated_backing.py)
confirms the four fixed kicker screw axes terminate in the posts; it does
not rate screw withdrawal, the post/header joints, or the panel load path.
The [complete visual cut inventory](owner-barrel-viewer.md) includes the
46 trial joint pairs, their cuts, heads, washers, and barrels. Red `REVISE`
marks a problem or unqualified fit, not a structural rating.
For rim removal, the modeled full 160 mm straight-line swept bounding box
misses every retained barrel, bolt stack and protected fixed envelope on
both sides after temporary rim-fastener removal. The separate exact convex
sweep of each uncut rim has no modeled timber penetration above 1e-6 mm³.
This clears the **nominal straight-line geometry**, not real tool access,
delivered-part tolerances, safe support or repeated demounting.

## Checks before the candidate can be frozen

1. **Qualify the revised left center-rail paths.** The owner approved moving
   only the lower-left and upper-left center-rail first bore/bolt rows from
   N = 60 to **42 mm**. The maintained integrated scene now includes that pose.
   Before this change, those machine bores intersected inherited service
   voids `_054` and `_055`, about 320.5 mm³ each. The nominal revised screen
   gives **6.641 mm** bore-to-service gap at each station, and the whole-cut
   check below finds no overlap at the eight changed paths. Moving toward the
   rail front edge still requires wood edge/end, net-section, tolerance and
   drilling-access checks; nominal clearance alone does not qualify a joint.
2. **Close one delivered hardware stack by family.** The current 6-in
   outer-rail tips pass only 1.849 mm beyond the *assumed* Hillman 880543
   barrel center. Moving those barrels 2 mm toward the rail ends improves
   axis reach but worsens the smaller axis/far-wall margin. A
   [7-in off-the-shelf hex-bolt listing][seven-bolt] alone does not prove
   enough threaded tip length and requires a deeper bore. Neither change is
   selected. A [documented 3/4-in partial-thread comparator](owner-barrel-integrated-stack-audit.md)
   now gives positive nominal male-thread/body overlap at all 46 trial
   lengths, but does **not** establish usable engagement. This is **not**
   the actual retailer-bolt thread specification or a selected order. Obtain actual bolt
   tip/thread-runout, washer OD/ID/thickness,
   barrel axis, through-thread/usable depth, and a positive tip-clearance
   allowance before a drilling plan. The
   [reach audit](owner-barrel-integrated-stack-audit.md)
   previously flagged four top-outer tips exactly at their modeled bore caps.
   The owner approved a **2 mm** machine-bore extension for those four rows,
   now in the maintained integrated scene. The nominal extension remains in
   `base_rail_top` without a modeled protected-feature, service, retained-
   hardware, other-wood or peer-path intersection; physical tolerances and
   actual hardware dimensions are still required. The [Home Depot Everbilt 800646 3½-in
   single](https://www.homedepot.com/p/204633291) is an ordinary-store
   full-thread/A307 *listing*, and the [Hillman 880543 barrel](https://www.homedepot.com/p/202242356)
   is described as threaded through its sides. Neither listing supplies
   controlled usable engagement or barrel resistance. The
   [insertion-bore audit](owner-barrel-integrated-stack-audit.md#barrel-insertion-holes-are-not-yet-drill-sizes)
   also finds zero nominal barrel-to-bore diameter allowance in all 46 CAD
   rows. No actual drill size or barrel fit is selected.

   The [combined current-pose regression](../../scripts/owner_barrel_combined_owner_trial.py)
   screens **both approved changes together** in a detached copy of the
   maintained 46-pair assembly. The complete visual cut represents all 46
   pairs, with no missing drill path, unexpected path host or intersection
   involving all eight changed drill paths (including both shifted barrel
   entry bores) and another protected/source cut.
   The four extra bore-tip segments stay within the modeled top rail and
   report no protected-feature or unrelated-wood hit above the 1 mm³ screen.
   Each top-outer shaft has 2 mm **nominal** bore-tip clearance. This does
   **not** establish net-section strength, thread fit, service tolerances,
   or any fabrication approval.
3. **Resolve the demanding center and outer-header load paths.** The single
   principal/header fastener cannot transmit a free couple by itself;
   compression/contact and the connected frame must carry signed opening
   and twist demands. The [24-duty local rank screen](owner-barrel-integrated-kinematics.md)
   retains a face-normal twist mode at both single-bolt center joints even
   with all modeled face cells closed. Every two-bolt duty reaches full *local*
   rank only under a closed-face assumption. The same screen gives the
   connected 20-timber framing a conditional 114/114 rank with every face
   closed but 112/114 with all faces open; it does **not** decide which contacts
   stay compressed in a signed case. The
   [cut-face screen](owner-barrel-integrated-preliminary.md)
   finds only 588.180 mm² of modeled face behind each bolt line; that is
   geometry, not a capacity or verified compression path. The modeled header
   pocket leaves only 2.092 mm nominal edge stock. Outer-header counterbores
   leave 6.35 mm nominal side stock, and
   the installed rim blocks the driver; the rim-first sequence is only a
   finite-screen option. These are not acceptable by appearance or by a
   bolt-shaft rating.

   A read-only [center-pose screen](../../scripts/owner_barrel_center_margin_options.py)
   found one collision-free *alternative*: replace each centered bolt with
   two rear-entry angled 4½-in trial bolts at principal X offsets ±11.25 mm,
   header entry Z = 257.7/258.1 mm. The nominal pair has 22.5 mm X pitch,
   but leaves only **2.796 mm principal side wood** beside a barrel,
   **2.092 mm header pocket edge wood**, and **1.501 mm** between pockets.
   Its right-side bores clear the candidate 25.4 mm F1–G1 passage by at least
   5.009 mm. Simply adding a second bolt next to the *existing* centered
   one instead produced pocket, washer and driver collisions. The two-bolt
   pose is **not selected**: its thin wood margins, installation tolerances,
   barrel engagement, splitting and resistance have no acceptance basis.
   Local closed-face rank could improve, but that is not a strength or
   signed-case result.

   Two seemingly simpler second-bolt directions also have immediate envelope
   limits in the maintained wood. At the same principal X center, two
   separate 21 mm rear-entry head pockets cannot both stay within the
   38.1 mm-high header: after allowing one radius at each edge, their
   centerlines can separate at most **17.1 mm**, less than the **21 mm**
   needed to keep the pockets distinct. A vertical bolt driven upward from
   the header underside at the principal center would put its head beneath
   the seam-side center post: on the right, the post spans X = −1.5875 to
   87.3125 mm and the bolt would sit at X = 70 mm; the post covers the same
   header Y span and meets its underside. Neither observation rules out a
   different head/driver envelope or a redesigned member, but it explains
   why simply adding a second ordinary barrel bolt is not yet an integrated
   center-joint solution.
4. **Verify material and panel yield.** The proposed 25.4 mm F1–G1 LED
   passage in one principal clears the modeled center hardware, but a real
   prewired strand and connectors have not been fed through it. The modeled
   4×6 center posts are not an identified dry, grade-stamped delivered lot.
   Measure both owned plywood sheets: the [Roseburg listing][plywood] reports
   actual dimensions smaller than the rectangular kerf-right main blanks, so
   neither a two-sheet main-panel yield nor a third-sheet-only kicker fix is
   established. Keep the fixed panel outlines and screw axes.

After those choices, the engineering work remains: measured repeated
assembly/service fit; a same-topology **signed six-case** response with
contact, opening and joint slip; complete 24-duty bolt/barrel/thread/wood
checks, retained-bolt and member checks, and floor stability; then a
predeclared guarded coupon and non-climbing frame-test program. The
[six-duty 2024-NDS preliminary](owner-barrel-integrated-preliminary.md)
contains conditional component scales, **not** complete connection
resistances or new-topology demands. The
[test-readiness note](owner-barrel-load-test-readiness.md) separates
exploratory coupons from proof testing.

## Cost scale, not a checkout total

The current trial length mix is **4 × 3½ in, 26 × 4½ in, 4 × 5 in,
12 × 6 in** bolts, plus 46
barrels and 46 head-side washers. Public Lowe's/Home Depot catalog arithmetic
for just the nominal bolts and Hillman-shaped barrels was **$98.50** on
22 September 2026. Adding one unqualified washer-pack comparator makes
**$106.47**; a different size-only barrel/washer comparator is **$114.14**.
These are neither a compatible 46-pair order nor a complete low/high range.
The [cost record](owner-barrel-integrated-cost.md) now also prices a **$435.14
full frame-and-face comparison basket**, including all counted frame sticks,
two face sheets, 12 retained bolt stacks and 66 panel screws. That basket
substitutes treated Southern pine and sheathing for the specified DF-L and
Roseburg plywood, and some fasteners are not Grade 5. It is **not** a buildable
bill, actual owner cash need, floor or ceiling. Hold/LED/pad shortfalls,
tools, delivery and tax remain outside it. No construction-hardware purchase
follows from either catalog subtotal.

**Owner decision recorded:** both bounded frame-hole changes above are
approved for modeling and integrated. Neither moves a panel, panel screw,
retained frame bolt, or center post. Neither authorizes drilling, fabrication,
load testing, or climbing. The next design decision is how to provide and
verify the center principal/header moment path without unacceptable thin
wood margins; delivered barrel and bolt thread evidence is also required.

[viewer]: https://mckayreedmoore.github.io/mini-moonboard/?model=owner-barrel-layout&view=rear
[plywood]: https://www.lowes.com/pd/Roseburg-23-32-CAT-PS1-09-Square-Structural-Plywood-Douglas-Fir-Application-as-4-x-8/1000015973
[seven-bolt]: https://www.homedepot.com/p/204281599
