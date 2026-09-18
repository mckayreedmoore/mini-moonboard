# Perimeter connection layout screen

2026-09-06. **Space study only: no new frame, selected block, product or capacity.**
This examines the ten unresolved junctions in the separately published
`mid-batten-clip-development` candidate. Preserve the selected untied baseline,
its end screws and all previous results until a complete replacement is checked.

## Available faces and tested envelopes

Board-local X is across the board, S uphill and N rearward. The main rails'
rear faces are at N=38.1 mm; rim inner faces are X=±1219.2 mm. A rear-mounted
block or angle could join those two broad faces with side-grain fasteners,
subject to actual stock/grain, installation and demand checks. Kicker rear
faces instead lie at world Y=−74.1 mm, adjoining the inner cheek faces.

The trial envelopes below extend 76.2 mm inward from each rim. These are
**clearance probes, not proposed structural dimensions**. The main probes
occupy N=38.1–76.2 mm. Kicker probes occupy world Y=−112.2…−74.1 mm.
They avoid the in-plane corner occupied by longitudinal edge battens.

| Junctions | Other trial limits, mm | Screen result |
| --- | --- | --- |
| Main horizontal seam, left/right | S=1159.35–1279.05 | No intersections with existing bodies/hardware |
| Main top, left/right | S=2359.5–2428.4 | No intersections; only 1.05 mm nominal separation from the custom top-angle N envelope |
| Main bottom, left/right | S=10–78.9 | Each overlaps its cheek splice by 67,896.875 mm³ and intersects splice screw hardware |
| Kicker bottom, left/right | World Z=5–45 | No intersections with existing bodies/hardware; 5 mm above nominal floor |
| Kicker top, left/right | World Z=180–220 | Each overlaps its cheek splice by 34.728 mm³ |
| Shortened kicker-top probe | World Z=180–218 | No existing body/hardware intersections; new fastening/tool access remains unchecked |

The main-bottom splices already occupy S=−100…100 and N=50…146.15 near
each rim. Only **11.9 mm** remains immediately behind the rail before the
splice begins. That cannot contain the trial 38.1 mm rearward block depth.
The closest LED column is laterally 123.8 mm from these probes; this does not
qualify a full harness, connector clearance, bend radius or driver approach.

The runnable [perimeter block screen](../tests/test_perimeter_block_screen.py)
preserves the tested clashes rather than deleting interfering parts to make a
test pass. It does not add fasteners, specify stock, check their edge distances,
or prove that every required installation motion is possible.

## Next layout decision

Develop **two coordinated details**, not ten copied A21 placements:

1. A rear-face side-grain attachment for the main seam/top and kicker rails.
   Resolve actual block/clip dimensions, receiving grain, fastener penetration,
   head/washer seating, tool access and assembly sequence. The 1.05 mm top-angle
   gap is a warning for tolerance and hardware development, not a fit allowance.
2. An integrated lower transition joining the main-bottom rail, rim, kicker
   cheek and nearby kicker-top backing. Redesign the splice and its attachment
   deliberately; do not trim away an existing load path merely to eliminate
   the probe's collision. Keep the full floor seat and the separate pad exclusion.

The [end-grain product screen](candidate-hardware-audit.md#perimeter-end-grain-product-screen)
does not establish a screw-only mixed-load replacement. It remains an alternative
only if a specific manufacturer's installation applies to the actual members
and joint demands. No permissible force, stiffness or equal-sharing assumption
follows from these space checks. All replacement joints still require a
complete connection-aware model and product/material resistance checks.
