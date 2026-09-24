# Historical WJ-04 4.5-inch bolt and spacer salvage screen

**Historical only.** The owner later directed WJ-04 to prioritize one
ordinary bolt/nut/two-washer joint; see the [decision log](decision-log.md).
Keep this dimensional salvage study as history, not as the active topology.
The current ordinary-joint geometry reference is the
[WJ-04 workhorse probe](wj04-workhorse-probe.md) and its
[machine-readable configuration](wj04-probe.json). Its hardware remains
provisional and its joint remains unaccepted; the 4.5-inch screw, brass spacer,
and three-washer stack below are not the active ordinary hardware.

Historical result: **REVISE — source-bound dimensional diagnostic, 2026-09-23.** This explored one catalog-sleeve variant for the narrow `clip_horizontal_lower_right_1` pose in [`wj04-probe.json`](wj04-probe.json). The rail and cleat remain 38.1 mm each along the rail-bolt axis; the cleat remains 95.25 × 38.1 × 119.7 mm. Nothing here changes the current WJ-04 configuration or establishes wood, sleeve, washer, or bolt capacity.

## Catalog parts and order

The identified [Grainger 22TT96 / U51050.025.0450](https://www.grainger.com/product/Socket-Head-Cap-Screw-1-4-22TT96) is a 1/4-20 × 4.5 in, partially threaded 18-8 stainless socket-head screw listed to ASME B18.3. The [CDE ASME B18.3 table](https://cdefasteners.com/sites/default/files/product-specs/socketscapss.pdf) gives 82.55 mm minimum body `Lb`, 88.9 mm maximum grip-gaging length `Lg`, and −1.524 mm nominal-length tolerance for that size. These are standard bounds, subject to delivery confirmation.

The identified [USA Industrials ZSPCR-470 at Zoro](https://www.zoro.com/usa-industrials-brass-unthreaded-round-spacers-14-in-screw-size-zinc-plated-brass-12-overall-lg-zspcr-470/i/G601011174/) is a cataloged zinc-plated brass round spacer: 0.500 ± 0.005 in long and OD, with 0.252–0.262 in ID. It is made for a 1/4 in screw and supplies a published length tolerance. It is an electronics/general spacing product; its compression, bearing, fatigue, and corrosion suitability for this wood joint is **unproved**. The minimum ID is only 0.002 in over the screw's nominal 0.250 in body diameter, so screw straightness, plated finish, and actual receiving fit still need checking.

For a bounded stack, use the [K.L. Jack 25NWUS8Z washer](https://www.kljack.com/products/25nwus8z/) thickness 1.2954–2.032 mm and [K.L. Jack 25CNFHS nut](https://www.kljack.com/products/25cnfhs/) thickness 5.3848–5.7404 mm as dimensional comparators. Proposed order from head to nut: **head washer → 76.2 mm wood → wood-side washer → spacer → outer washer → nut → 2.54 mm tip reserve**. The three-washer scheme avoids direct nut bearing on the narrow spacer end and transfers spacer force into a washer at the wood face. The Grade 8 zinc washer's compatibility and bearing with stainless screw, brass sleeve, and wood are not established.

| Dimension screen | Bound | Result |
| --- | ---: | --- |
| Wood far face from under head, with maximum head washer | 78.232 mm | 4.5 in standard minimum smooth body is 82.55 mm; **4.318 mm** margin before other tolerances |
| Seated nut near face from under head, with all three washers and spacer minimum | 92.6592 mm | 4.5 in standard latest complete thread is 88.9 mm; **3.7592 mm** engagement-location margin |
| Maximum listed stack through 2.54 mm tip | 103.4034 mm | Minimum screw length 112.776 mm; **9.3726 mm** length reserve |
| Tip beyond seated nut | 11.9126–16.256 mm | Requires a stud-clearing nut tool |

The spacer **does resolve the standard thread-location conflict on paper** while keeping the existing wood grip. These figures carry catalog part tolerances only. They do not include delivered wood section, bore position and diameter, washer flatness, seating compression, bolt straightness, or angularity.

## Tool and service envelope

The [FACOM RB.7/16](https://www.facom.com/product/rb716/716-drive-12-point-thin-wall-socket?tid=609036) is 22 mm overall, 14.8 mm at its working diameter, and 15.8 mm at its drive end; its [catalog](https://docs.rs-online.com/6a69/A700000008404294.pdf) lists `L1 = 9 mm` nut engagement. Its internal stud-through depth and square-drive intrusion are unpublished. The seated nut can have up to **16.256 mm** of protruding stud, so a guaranteed 9 mm nut engagement with that stud has not been shown.

For the current source face gap, a 22 mm exterior socket following the nut completely off the maximum-length 4.5 in bolt ends only **8.9454 mm nominal** before the upper service rail. A [GEARWRENCH 81011T](https://www.gearwrench.com/all-tools/ratchets-sockets/ratchets-drive-tools/81011t-14-drive-90-tooth-teardrop-ratchet-5) has a listed 0.35 in / 8.89 mm head thickness. Simple axial addition leaves **0.0554 mm nominal** before that rail, with no allowance for a drive tang, coupling, tool variation, wood variation, handle swing, or protected upper SDS. The ratchet head is 0.98 in / 24.892 mm wide, near the generic 25.4 mm CAD tool diameter. This arithmetic is a bounding comparison, **not** a ratchet/socket assembly fit or moving-solid clash pass. Some tang may overlap the socket, but its actual dimensions and socket reception must be obtained before crediting overlap.

The 12.573–12.827 mm OD spacer itself nominally fits within the earlier 12.827 mm nut and 25.4 mm tool radial envelopes, yet it is an additional installed and removable body. Its washer support, protected-wire clearance, retained upper SDS, withdrawal to the bolt tip, and hand path have not been re-screened in CAD. The existing WJ-04 trial also retains the conditional rail near-end shortfall and principal loaded-edge uncertainty; this sleeve does not fix either.

## Disposition

**Historical dimensional thread and stack salvage only.** A real 4.5 in bolt and 1/2 in sleeve SKU existed for this comparison, and their published axial tolerances produced positive wood-body, nut-thread, and tip reserves. The FACOM socket's internal clearance was unknown, and a documented 1/4-in ratchet consumed essentially all nominal remaining upper-rail gap. The historical follow-up was to obtain matching socket/driver sections and delivered-part dimensions, then screen the full installed and moving volumes. That follow-up does not select this parked salvage stack or supersede the linked current WJ-04 configuration. No cutting, drilling, strength, or fabrication acceptance follows from this note.
