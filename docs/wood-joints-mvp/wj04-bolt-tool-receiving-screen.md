# Historical WJ-04 bolt and tool receiving screen

**Historical dimensional diagnostic only.** This note tests the earlier
95.25 × 38.1 × 119.7 mm cleat pose with a stainless socket-cap screw. The
owner later directed WJ-04 toward one ordinary Grade 5 hex bolt, nut, and
two-washer stack; retain this result as history, not as the active hardware
or geometry screen. It does not prove joint strength or authorize cutting
and drilling. Its source CAD screen was nominal and omitted the new WJ-03
node parts.

The current ordinary-joint geometry reference is the
[WJ-04 workhorse probe](wj04-workhorse-probe.md) and its
[machine-readable configuration](wj04-probe.json). That trial still has
provisional hardware and no accepted product, complete mechanics, or layout
result. The stainless screw, 3.5-inch comparison, and dimensions below do not
describe the active ordinary hardware configuration or establish acceptance.

## Product dimensions and stack

The candidate [K.L. Jack 25C400KCSS](https://www.kljack.com/products/25c400kcss/) is a 1/4-20 × 4 in partially threaded stainless socket cap screw to ASME B18.3. Its nominal under-head length is 101.6 mm. K.L. Jack lists a **minimum** 25.4 mm thread length and warns that delivered thread can be longer. The [CDE ASME B18.3 dimension table](https://cdefasteners.com/sites/default/files/product-specs/socketscapss.pdf) gives, for a 1/4 × 4 in screw, 69.85 mm minimum body length `Lb`, 76.2 mm maximum grip-gaging length `Lg`, and −1.524 mm length tolerance. These standard bounds require confirmation against the delivered lot; the retail listing alone does not certify a particular shank.

For a bounded washer comparison, [K.L. Jack 25NWUS8Z](https://www.kljack.com/products/25nwus8z/) lists thickness 1.2954–2.032 mm, ID 7.7978–8.3058 mm, and OD 18.5166–19.0246 mm. This Grade 8 yellow-zinc washer is a **dimensional comparator**, not an approved mate to the stainless screw. [K.L. Jack 25CNFHS](https://www.kljack.com/products/25cnfhs/) lists a stainless 1/4-20 nut, 5.3848–5.7404 mm thick and 0.488–0.505 in across corners. The CAD bore is 7.5 mm, an occupancy envelope rather than a drill instruction. The washer ID minimum exceeds this nominal bore by 0.2978 mm in diameter; real bore and washer tolerances still need a receiving check.

| Rail screw | Worst-case length reserve after 76.2 mm wood, two 2.032 mm washers, 5.7404 mm nut, and 2.54 mm tip | Guaranteed smooth body versus wood | Thread at seated nut |
| --- | ---: | --- | --- |
| 3.5 in ASME B18.3 length | **−1.1684 mm** | `Lb` 57.15 mm; insufficient | Cannot cure length deficit |
| 4 in 25C400KCSS | **+11.5316 mm** | `Lb` 69.85 mm; up to **8.382 mm** of the cleat may lie beyond guaranteed body | `Lg` ≤76.2 mm, before the earliest nut bearing face at 78.7908 mm |
| 4.5 in ASME B18.3 length | +24.2316 mm | `Lb` 82.55 mm covers worst-case 78.232 mm wood end | `Lg` may be 88.9 mm; nut cannot be guaranteed to seat at 78.7908–80.264 mm |

The 3.5 and 4.5 in rows apply the published standard dimensions as comparisons, not identified purchase SKUs. The 4 in length can carry the nut stack on paper, but the standard permits thread/root in the outer part of the cleat. A longer standard cap screw moves its guaranteed thread start past the nut seat. For a custom or lot-measured screw to guarantee both full smooth-body wood bearing and a fully threaded nut at every listed washer extreme, the body must reach at least **78.232 mm** from under the head while a complete thread must begin no later than **78.7908 mm**. This leaves only **0.5588 mm** for the transition before wood, washer, hole, and machining tolerances. The current products do not publish this guarantee.

## Tool and removal

The [FACOM RB.7/16 product page](https://www.facom.com/product/rb716/716-drive-12-point-thin-wall-socket?tid=609036) specifies 14.8 mm diameter and 22 mm overall length. The [FACOM catalog drawing](https://docs.rs-online.com/6a69/A700000008404294.pdf) additionally gives 15.8 mm drive-end diameter and 9 mm `L1` socket engagement. These external diameters are below the probe's 25.4 mm tool cylinder. With a 4 in screw and minimum 1.2954 mm head washer, the 22 mm socket's far end after full nut withdrawal is nominally **21.6454 mm short of the upper rail**, before a driver or ratchet is added. This is a calculated axial envelope from the current source faces, not a new CAD clash pass; the fixed upper SDS and other protected volumes still require an actual tool sweep.

The 4 in screw's protrusion past a seated nut spans roughly **14.0716–17.4244 mm** under the listed length, washer, and nut extremes. FACOM publishes `L1 = 9 mm` nut engagement but does not publish the socket's stud-through depth or the square-drive intrusion. Thus the socket cannot be guaranteed to engage the nut over the protruding stud. FACOM also supplies no ratchet head, extension, hand-space, or loaded removal envelope in the cited data. The 21.6454 mm nominal axial allowance cannot be counted as proof that a ratchet or driver fits, nor as an allowance for stock, seating, or assembly variation. The current probe's generic 50 mm moving-tool gap for a 4 in bolt would be **−6.348 mm**; substituting the 22 mm external socket alone gains 28 mm, but a working drive still needs evidence.

## Disposition

**Historical finding: no published bolt-plus-tool combination cleared this old dimensional gate.** The 3.5 in length failed this tolerance stack; the identified 4 in screw lacked guaranteed smooth-body coverage of all wood, and the FACOM socket lacked internal stud and drive clearance evidence; a standard 4.5 in cap screw could prevent nut seating. These results apply only to this stainless socket-cap comparison. The separate WJ-04 end/loaded-edge classifications, delivered cleat stock and grain, strength, eight washer seats under product dimensions, and integrated WJ-03/service screen were also open. The historical follow-up was to obtain a bolt drawing or measured lot and a socket/driver drawing or physical mockup, then re-run the product-sized sweeps. Use the linked current workhorse probe for current geometry status. No connector or capacity was accepted here.
