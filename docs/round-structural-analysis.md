# Structural screws and larger 2x6 passages

The owner selected structural panel screws for the current build, with future
insert space retained. `round-structural-development` preserves both aligned
service-rail rows (1134.2 and 1278.25 mm along the slope), all fixed upper
principal/rim screws, and the 60/140 mm kicker rows. The 56 attachments remain
exactly mirrored. Interior rail-screw columns use absolute X positions 435.075
and 835.075 mm: each shifts 11.6417 mm away from their former midpoint, giving
a 400 mm middle gap and equal 365.075 mm end gaps. Row heights, outer/center
principal screws and upper center screw #4 stay fixed. The change prevents
three original 2-inch screw tips from entering the enlarged LED passages. Historical screw and insert candidates remain separate.

LED routing holes increase from 25.4 to 38.1 mm in nominal 2x6 members only.
Other members retain their 25.4 mm passages. The actual stock cross-section,
not a name prefix, determines which holes enlarge. Panel LED and hold holes
retain their own diameters. Larger holes improve geometric feeding space but
remove more timber; previous member-strength results do not transfer.

The matching [audit](../fea/results/round-structural-audit-v1.json) checks actual
screw axes through the timber, tip containment, machined passages, hardware fit
and future insert clearance. The [build draft](round-structural-build-plan.md)
and [drilling PDF](round-structural-drilling/drilling.pdf) name the current products.
The final audit passes its assembled geometry and SPAX product-geometry gates.
All 200 screws remain inside their net timber receivers, including the enlarged
passages. All 56 future insert reserves fit without cutting those reserves.

| Screw family | Count | Minimum nominal tip-to-first-exit distance |
| --- | ---: | ---: |
| SPAX panel/kicker screws | 56 | 107.156 mm |
| SDS bracket screws | 144 | 2.555 mm |

These are nominal CAD distances along each actual screw axis, not a blanket
allowance for longer screws, undersized lumber or overdriving. The tight SDS
margin includes the modeled ML24Z thickness. Use the specified lengths and
normal seating; verify delivered parts match the schedule. Tip containment
and product spacing do not establish joint resistance or frame strength.

The initial enlarged-hole layout exposed three panel screw tips inside the LED
passages. The mirrored interior-column adjustment above resolves that conflict
while retaining the two-inch screw product and every row height.

## Minimum remaining work and further simplification

- Keep the current geometry and fastening pattern; no screw-count or symmetry
  optimization is needed for the next decision.
- Use one specified panel screw and one manufacturer-required bracket screw;
  avoid bespoke insert machining in this build.
- Keep future inserts optional. A clearance reserve is not a promise that a
  particular insert can safely retrofit a worn screw hole.
- Do not require floor measurements or physical floor tests. Record one intended
  installation and explicit analytical stability assumptions, rather than
  claiming measured friction or universal hardwood/carpet/mat acceptance.
- Replace the extensive simulation research program with a focused structural
  assessment where conservative calculations and applicable published ratings
  are sufficient. Resolve unsupported bracket load directions, leg/base load
  transfer, panel fastening and local sections around enlarged passages.
- Use a representative LED feeding check with the actual intact kit instead of
  more detailed cable simulation. The feed arrangement remains part of assembly.

No floor-strength, frame-strength or climbing approval follows from geometry
or from removing measurement tasks from the scope. New load/connection evidence
must match this screw-based candidate rather than the preserved insert model.
