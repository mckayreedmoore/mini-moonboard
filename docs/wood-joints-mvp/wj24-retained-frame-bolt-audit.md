# WJ24 retained frame-bolt audit

Status: source-bound geometry and hardware diagnostic, 2026-09-24. This is
not a WJ24 bolt-capacity check, a structural pass, a drilling instruction, or
a release. WJ24 replaces the 24 angle/SDS duties while retaining the twelve
starting frame-bolt arrangements. No acceptance transfers from the selected
angle-frame candidate or earlier WJ studies.

## Evidence boundary

The [WJ24 composition](hypotheses/wj24-integrated-static/composition.json)
and [diagnostic](hypotheses/wj24-integrated-static/diagnostic.json) bind to
the current [source inventory](source-inventory.json)
(`07af4c3e…f21c2d78`) and its [kerf-right connection axes](../floor-flush-construction-kerf-right/connection-axes.csv)
and [profile outlines](../floor-flush-construction-kerf-right/stock-profiles.json).
The inventory records source commit
`df7f5eca86ae831b35a8bcf9e6dcd7ae8af852bb`. Its official/kerf-right
cross-check confirms the same host pairs and legacy axis IDs. WJ24's geometry
input is the 4×8 kerf-right packet; it is the same candidate's width option,
not a second load study. The selected authority remains
[`current-candidate.json`](../../current-candidate.json),
`compact-floor-flush-development`.

For the right-hand bolts, the kerf-right source moves the recorded X origin
3.175 mm along the bolt axis relative to the official packet; Y/Z and axis
direction match. This changes the station's axial datum with the width option,
not the through-bore line. WJ24's [hardware inventory](hypotheses/wj24-hardware-inventory/README.md)
keeps these 12 retained stacks separate from its 104 proposed replacement
bolts.

WJ24 preserves all twelve axis IDs, origins, directions, host names, nominal
lengths, diameters and grips: each reported live-to-inventory delta is zero.
It contains 12 occupied-axis proxies, 60 modeled installed components (five
per bolt), and 72 total bolt shapes. Its frame-hardware/finished-wood and
frame-hardware/candidate-hardware intersection maps are empty. Each row still
has `candidate_recheck_status: required`; every
`structural_recheck_complete` value is false, and the top-level structural
recheck is false. Those results authenticate identity and modeled geometry
only. They provide no signed force, bolt-group response, resistance, preload,
fit, or acceptance.

WJ24 moves the two center-post hosts outward by 120 mm: left from X =
−89.05…−50.95 mm to −209.05…−170.95 mm, and right from X =
50.95…89.05 mm to 170.95…209.05 mm. No retained frame bolt is hosted by
either center post, and no retained bolt station is moved. The changed
architecture and support locations can still redistribute demand through the
frame; the old frame-bolt forces cannot be copied into WJ24.

## Twelve-station reconciliation

The selected baseline axis packet distinguishes the bolt-shank envelope from
the larger wood clearance opening. `D` below is the nominal bolt diameter;
the last column is the source hole range, not a bit size. The profile distances
are centerline-to-outer-profile measurements derived from the kerf-right
[member datums](../floor-flush-construction-kerf-right/bolt-member-datums.csv),
profile outlines, and source axes. For each member, profile vertices were
projected onto the recorded grain vector `g` and perpendicular vector
`c = (g_z, -g_y)`; ray distances from the bolt center to the profile boundary
give `End` along `±g` and `edge` along `±c`. Left and right are mirrored and
give the same values. These are geometric
distances only: they do not classify an NDS loaded end or edge, include a
shop tolerance, or prove the WJ24 connection.

| Retained axes, count | Receiver pair | Nominal bolt D / length / wood grip (mm) | Wood opening range (mm) | Host: nearest end / nearest edge (mm) |
| --- | --- | ---: | ---: | --- |
| `lumber_leg_bolt_{left,right}_1`, 2 | `base_side` + `lumber_leg` | 12.7 / 203.2 / 177.8 | 13.49375–14.2875 | `base_side`: 586.653 / 43.399; `lumber_leg`: 119.282 / 54.860 |
| `lumber_leg_bolt_{left,right}_2`, 2 | `base_side` + `lumber_leg` | 12.7 / 203.2 / 177.8 | 13.49375–14.2875 | `base_side`: 534.457 / 63.688; `lumber_leg`: 94.152 / 54.673 |
| `rail_front_bolt_{left,right}_1`, 2 | `base_post_outer` + `base_floor` | 9.525 / 101.6 / 76.2 | 10.31875–11.1125 | `base_post_outer`: 70.172 / 69.528; `base_floor`: 70.172 / 69.528 |
| `rail_front_bolt_{left,right}_2`, 2 | `base_post_outer` + `base_floor` | 9.525 / 101.6 / 76.2 | 10.31875–11.1125 | `base_post_outer`: 98.103 / 41.597; `base_floor`: 98.103 / 41.597 |
| `rail_rear_bolt_{left,right}_1`, 2 | `base_floor` + `lumber_leg` | 9.525 / 114.3 / 88.9 | 10.31875–11.1125 | `base_floor`: 71.952 / 69.000; `lumber_leg`: 71.062 / 69.836 |
| `rail_rear_bolt_{left,right}_2`, 2 | `base_floor` + `lumber_leg` | 9.525 / 114.3 / 88.9 | 10.31875–11.1125 | `base_floor`: 98.932 / 42.200; `lumber_leg`: 100.414 / 43.638 |

The nearest geometry deserves specific follow-up. The upper second bolt is
94.152 mm from the inclined top profile of the leg; the upper first bolt is
43.399 mm from the nearest cross-grain profile boundary of the rim. The first
front bolt is about 70 mm from the front/end profiles. The rear first bolt is
about 71 mm from each member's toe/rear profile. The second front and rear
bolts have only 41.597–43.638 mm to their nearest cross-grain profile
boundaries. These measurements are from the bolt centerline to the outside
profile, before subtracting the clearance-hole radius. The final directional
end/edge calculation must use the exact member cut, hole location, load
direction, delivered bore, and applicable NDS provisions; no minimum-distance
pass or failure is assigned here.

The WJ24 diagnostic reports changed-host cutter reconciliation for eight
bolts. The four upper bolts use changed `base_side_left/right` hosts: each
source cutter intersects raw wood by 14,252.929243 mm³ and the finished host
has zero overlap with the occupied bolt axis. The four front bolts use changed
`base_post_outer_left/right` hosts: each source cutter/raw-host intersection
is 3,695.203878 mm³ and the finished host has zero overlap with the occupied
axis. These figures show that the source holes are accounted for in the
changed hosts; they are not a bearing or edge-distance check. The four rear
bolts have no changed-host entries because `base_floor` and `lumber_leg` are
not rebuilt WJ24 shared hosts. Their source station and hardware records
persist, but this composition does not replay their host cuts as changed
geometry.

The WJ24 report's parent audit also matches its fourteen retained raw-host
records to WJ18. That is a source/candidate geometry identity check. It does
not show delivered lumber or hardware: the source inventory has no observed
stock, and the WJ24 artifacts record no physical measurement.

The source occupied diameters (12.7 and 9.525 mm) describe the bolt-axis
proxies. The opening ranges above come from the source construction packet;
the modeled upper-end openings are 14.2875 and 11.1125 mm. Actual finished
holes must remain within the recorded range, and the applicable shop checklist
controls any eventual operation. Do not use the CAD axis diameter as a drill
size.

## Grip and delivered-shank sensitivity

WJ24 carries the source nominal wood grips unchanged. The selected packet's
[hardware schedule](../floor-flush-construction/bolt-hardware.csv) defines
177.8 mm for each upper stack (88.9 mm rim plus
88.9 mm leg), 76.2 mm for each front stack (38.1 mm post plus 38.1 mm
runner), and 88.9 mm for each rear stack (38.1 mm runner plus the 50.8 mm
remaining leg section at the recessed connection). The rear grip therefore
depends on preserving the modeled 50.8 mm leg bearing section. Confirm that
section at the actual bolt station before using the nominal grip. The WJ24
inventory does not record a delivered measurement.

The linked baseline hardware notes give the following screening requirements
for the member-specific NDS full-body route described in the
[bolt-resistance basis](bolt-resistance-basis.md). Count the bolt's transition
as threaded, and measure from the under-head bearing face to the first reduced
section. The washer bound is the catalog maximum used in those notes.
The threshold is `grip + maximum head-washer thickness − one quarter of the
nut-side member's bearing length`.

| Stack group | Wood grip (mm) | Nut-side wood bearing length used (mm) | Minimum full body to transition (mm) | Status in WJ24 |
| --- | ---: | ---: | ---: | --- |
| Upper 1/2-in | 177.8 | 88.9 | 158.9278 | No delivered shank or transition measurement |
| Front 3/8-in | 76.2 | 38.1 | 69.3166 | No delivered shank or transition measurement |
| Rear 3/8-in | 88.9 | 50.8 | 78.8416 | No delivered shank or transition measurement; verify the remaining leg section |

These are measurement thresholds for the stated full-body assumption, not
capacity results. The [baseline bolt note](../compact-half-inch-hardware.md)
and [runner bolt note](../floor-runner-recess-hardware.md) distinguish catalog
length, body length, thread length, and grip. Bolt Depot's partially threaded
product descriptions specify minimum thread lengths, not a maximum or
guaranteed delivered body length. The separate [source correction](bolt-dimension-source-correction.md)
concerns a 1/4-in six-inch cap screw and does not set dimensions for these
retained bolts. The upper source stack leaves
only 2.7432 mm beyond the tallest modeled nut at shortest bolt length and
maximum washer stack in the cited dimensional screen. Nut seating and complete
thread engagement therefore also need actual-part checks.

The current source hardware table leaves the upper thread columns blank and
records only nominal 25.4 mm thread/start assumptions for the 3/8-in groups;
blank is not evidence of a smooth shank. Measure each received bolt, wood
thickness, washer and nut stack. If a bolt does not meet its member-specific
full-body threshold, the WJ24 mechanics must use the measured root diameter or
another supported threaded-bearing method and rerun the affected modes. The
selected-baseline full-thread-root sensitivity above 1.0 is a warning about
that separate baseline case, not a WJ24 result or acceptance value.

## Remaining checks before any WJ24 structural conclusion

- Bind the twelve current bolt product identities, material/area basis, actual
  body-to-thread transitions, thread roots, washers, nuts, and delivered
  lengths to one source-distinct installed stack for each group.
- Confirm the actual grips, including 50.8 mm remaining leg bearing at the
  rear stations; verify nut seating, usable engagement, and protrusion using
  measured dimensions.
- Reconcile actual finished bore diameter and position at both receivers for
  all twelve axes. Recheck the current WJ24 member sections, end/edge geometry,
  grain directions, clear wood to cuts, and any local 1:12 recess interaction
  with the actual hole and load direction.
- Produce fresh signed axial, lateral, and moment actions for each bolt and
  each applicable frozen load case from the WJ24 connected model. Check bolt
  tension/shear interaction, threaded or full-body lateral response, wood
  bearing, group action, splitting, net section, washers, and connected-member
  load transfer with applicable methods. Do not import old angle-frame bolt
  forces, utilizations, or six-case passes.
- Resolve physical wrench, counterhold, nut/washer removal, and bolt-withdrawal
  access around the new WJ24 parts, then finish tolerance, receiving, and
  assembly records. The current empty CAD intersection maps do not cover
  these operations.

The practical hold point is specific: WJ24 proves that the twelve modeled
stations and stacks remain present and that the changed upper/front host cuts
do not occupy their source bolt axes. It does not yet establish that any of
the twelve delivered bolts, wood receivers, or complete frame joints meet the
new candidate's demands.
