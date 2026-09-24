# WJ-05 center kicker backer transfer diagnostic

Status: **nominal_geometry_clear_diagnostic**. Geometry trial only; no joint capacity, drilling, fabrication, or climbing release.

This source-bound trial retains the kerf-right panels, all four fixed center-kicker screw axes, and the two inner kicker edges. It uses the owner-review ±180 mm center-post placement and adds two ordinary vertical through-bolts from each separate 4×4 backer into the maintained `base_header`. This remains a diagnostic WJ-05 topology; it does not replace the selected candidate or transfer old acceptance.

## Candidate geometry

| Piece | X (mm) | Y (mm) | Z (mm) |
|---|---:|---:|---:|
| Left backer | -90.4875…-1.5875 | -124.9…-36.0 | 0.0…238.9 |
| Right backer | -1.5875…87.3125 | -124.9…-36.0 | 0.0…238.9 |
| Base header | −1219.2…1216.025 | −175.7…−36 | 238.9…277 |

Each backer receives two provisional 1/4-20 Z-axis through-bolts with a 7.3 mm nominal clearance bore. The left axes are at X/Y=(−35,−97) and (−35,−63) mm; the repaired right axes are at (41,−98) and (25,−76) mm. Each bolt crosses 238.9 mm of backer and 38.1 mm of header. A 20 mm diameter, 7 mm deep open counterbore in the backer bottom contains one standard 1/4-in hex head and one Type A washer at maximum envelope thickness; their combined depth is 6.807 mm, leaving 0.193 mm nominal recess allowance. The illustrative top stack uses three Type A washers. These dimensions are an investigation pose, not a cut or drill schedule.

The model screens all 66 purchased-length screw-axis envelopes and all twelve retained frame-bolt axes. It also checks the backers, bores, hardware stacks, and tool envelopes against maintained hold/T-nut, LED, wire, panel-screw, and frame-bolt solids, with exact solid intersections after bounding-box pruning. The source report contains every collision witness.

## Receiver and support results

The four fixed center-kicker axes are modeled at X=±70 mm, Z=60/192 mm, along −Y. All four have full nominal axis-volume reception in their assigned backer; each 63.5 mm purchased-length axis enters 45.24375 mm of backing beyond the kicker panel back. Both kicker inner-edge support sample sets are contained by the backers. The gross backer/header contact is 7903.21 mm² per side before bolt bores.

WJ-05 tool geometry uses one Ko-ken 3305A-7/16 outer-envelope proxy. It includes seated and prior approach-endpoint placements plus their continuous coaxial sweep. Top seat datum is the nut bearing face at Z=283.096 mm; bottom seat datum is the bolt underhead face at Z=4.968 mm. The modeled exterior envelope is checked against wood, fixed axes, and protected services. Intended occupancy at the named nut/head is recorded separately and is not an obstacle clash. Internal 12-point profile, fit, clearances, driver, tolerances, and tool access are not assessed. Nominal positive gaps are not tolerance or assembly acceptance. A geometry-clear result does not establish connection resistance or an integrated frame.

## Bolt thread and tool screen

The shaft begins at the bolt underhead bearing face, Z=4.968 mm, beneath the 2.032 mm bottom washer. Wood bearing starts at Z=7 mm and ends at Z=277 mm: 270 mm of wood, but 272.032 mm from the underhead datum to the wood top. This screen does not require a smooth shank through all 270 mm of wood. Under NDS 12.3.7.2, nominal D is permitted only when thread bearing in the member holding the threads stays within one-quarter of that member's full bearing length; otherwise use measured root diameter. Here the tip member is the 38.1 mm header, so that limit is 9.525 mm. Complete nut engagement and at least 3.175 mm of threaded tip remain required. The 12-in ASME envelope has 268.478–279.400 mm smooth-shank length, corresponding to at most 3.554 mm of thread bearing in the header, but its long-shank end does not guarantee full nut engagement. Type A washer thickness is 1.295–2.032 mm; the finished hex nut maximum thickness is 5.740 mm.

| Nominal bolt and top washer stack | Standard smooth/thread transition range from underhead (mm) | Measured transition band for NDS limited-thread use and full nut engagement (mm) | Worst-case header thread bearing |
|---|---:|---:|---|
| 11.5 in + 1 washer | 255.78…266.70 | 262.51…273.33 | 16.25 mm (over the 9.525 mm NDS nominal-D limit) |
| 12 in + 1 washer | 268.48…279.40 | 262.51…273.33 | 3.55 mm (within limit) |
| 12 in + 3 washers | 268.48…279.40 | 262.51…275.92 | 3.55 mm (within limit) |

The corrected three-washer transition band is 262.507–275.918 mm from the underhead. This permits up to 9.525 mm thread bearing in the 38.1 mm header and requires threads to start by the nut bearing face for full engagement. For the 12-in standard envelope, the thread starts 3.554 mm into the header at its shortest smooth-body extreme, which fits the NDS one-quarter limit; a measured transition is still needed to prove full nut engagement. The 11.5-in envelope permits 16.254 mm in the header at its shortest smooth-body extreme, so it needs a measured transition in its allowed interval or a root-diameter calculation. No SKU is accepted.

### Conditional receiving specification for the modeled three-washer stack

The wood path is Z=7–277 mm, with a 4.968 mm underhead datum. On receipt, measure each 12-in bolt's delivered underhead length, thread transition, nut, and washer stack together. For the three-washer case, require the transition to fall between 262.507 mm and the underhead-to-wood-top distance plus the actual washer stack; with three minimum washers this is 262.507–275.918 mm. This is an NDS limited-thread and full-nut-engagement receive band, not a full-wood smooth-shank requirement. If thread bearing exceeds the 9.525 mm header limit, carry measured root diameter into the NDS lateral-yield method. Also verify threads through the complete nut and at least 3.175 mm beyond it. No SKU currently meets this evidence requirement; physical receive fields remain blank.

Tool screen uses cataloged Ko-ken 3305A-7/16: 55 mm overall length, 17.2 mm maximum OD, 16 mm working-end OD, H1=12 mm, H2=41.5 mm. The external model applies maximum OD over full length; it does not model internal profile or claim a fit. At the bottom stations, the seated external envelope reaches -50.032 mm (-50.032 mm below member bottom), and the full insertion sweep reaches -54.807 mm below member bottom. The 1.4 mm value from 20 mm counterbore diameter less 17.2 mm envelope is a nominal radial remainder only. Ratchet/extension, drive-end access, floor clearance, and installation/removal sequence are unmodeled and unverified.

Dimension references: [ASME B18.2.1-2012](https://studylib.net/doc/27174816/asme-b18.2.1-2012), [ASME B18.2.2-2022](https://studylib.net/doc/27188368/asme-b18.2.2-2022), [12-in bolt example](https://boltdepot.com/Product-Details?product=5238), [finished hex nut](https://boltdepot.com/Product-Details?product=2563), [1/4-in washer](https://boltdepot.com/Product-Details?product=2947), [Type A washer catalog dimensions](https://www.panduit.com/content/dam/panduit/en/products/media/6/86/986/6986/101806986.pdf), [Type A washer tolerance reference](https://www.nvent.com/sites/default/files/acquiadam_assets/2021-09/CB_Technical%20Reference.pdf), and [7/16-in deep socket](https://kokenusa.com/products/deep-socket-3-8sq-dr-12-p-7-16).

## Required follow-up

- Establish a mechanics model for two long bolts parallel to backer grain, header bearing, the eccentric backer-to-header transfer, and the bottom counterbores. No capacity is assigned here.
- Obtain a 12-in partial-thread bolt whose coupled delivered length, smooth-shank/thread transition, measured three-washer stack, nut seat, and 3.175 mm minimum thread projection satisfy the conditional receiving specification; otherwise this receiver connection remains blocked.
- Check whether the bottom head/tool pockets and socket/ratchet can be assembled and removed in the declared frame sequence while respecting the floor assumption.
- Integrate and recheck the changed center-post/header/principal duties, all 24 duty owners, the other 62 fixed panel axes, and twelve frame-bolt arrangements in the complete WJ-06 model.
- Add dimensional tolerances, contact/opening, tool swing, member transport, and complete forward/reverse assembly to WJ-07.

Physical receiving and observation fields stay blank. This file does not authorize purchase, cutting, drilling, fabrication, or use. No resistance or load-capacity result is assigned.

Reproduce with `uv run python scripts/wood_joints_wj05_center_backer_transfer_probe.py --write`. Source hashes are recorded in [`wj05-center-backer-transfer.json`](wj05-center-backer-transfer.json).
