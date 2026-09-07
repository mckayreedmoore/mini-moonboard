# Selected-product geometry integration

This is an inspectable development candidate, **not a build release, machining
instruction or structural approval**. `product_frame.py` keeps the earlier
transition model unchanged and exposes a separate `selected-hardware-development`
candidate. [Open its viewer](https://mckayreedmoore.github.io/mini-moonboard/?model=selected-hardware-development),
[STEP assembly](../exports/selected-hardware-development/selected-hardware-development.step),
[metric/imperial parts](../exports/selected-hardware-development/selected-hardware-development_parts.csv),
and [connection schedule](../exports/selected-hardware-development/selected-hardware-development_connections.csv).

**Preserved predecessor finding:** the top-rim bolt end distances fall short of the selected
conservative 7D layout screen. See the [connection-distance audit](product-connection-audit.md).
This exported state preserves that issue for inspection; it is not the final
goal candidate or a recommendation to fabricate these top joints.
The separate [top-joint candidate](top-joint-development.md) implements the
relocation. Its [review packet](candidate-review-packet.md) is the current handoff;
the evidence below remains specific to this predecessor unless explicitly reused.

![Selected-product candidate, front inspection view](../exports/selected-hardware-development/selected-hardware-development_front.png)

## What changed

- Four main skins and two kicker skins use the purchased Roseburg face stock's
  **23/32 CAT = 18.25625 mm** dimension as a nominal assumption, not a sheet
  measurement. Main backing planes and the kicker's Y = -36 mm backing plane
  stay fixed. A local kicker top trim removes overlap with the thicker main
  panel; its eventual STEP profile must accompany the cutting instructions.
- All 142 hold and 132 LED bores retain their original grid axes. Backing
  hardware/LED reliefs are regenerated from the undrilled predecessor.
- All 278 frame connections use the selected specification/envelope layer.
  Bolt bores are a project-assumed 7/16 inch (11.1125 mm); washers are annular,
  with explicit nominal axial and maximum radial envelopes. Physical grip
  datums remain fixed.
- R4 heads reserve a flush Ø10 × 5 mm envelope. This is **not** an instruction
  to drill a cylindrical recess or proof of actual head bearing. SD/SDS heads
  remain outside steel, with no countersinks. Custom SDS steel bores are 7 mm.
  Separate wood pilots are provisional; actual manufacturer installation rules
  and resistance checks remain necessary.
- The US A21 selection still uses an explicitly unverified UK hole/bend proxy.
  No connector holes were enlarged to make the new screw envelope pass.
  Remaining leg/splice stock is separately specified in the
  [material/hardware closure](remaining-material-hardware-closure.md).

## Diagnostic evidence and installation order

Run `PYTHONPATH=. uv run python tests/product_frame_screen.py --output docs/product-frame-screen.json`.
The [raw diagnostic](product-frame-screen.json) records source hashes and CadQuery
version. It checks nominal part and hardware intersections and straight tool
corridors; it never returns structural or complete fit approval.

The initial run found no unintended body/body, hardware/body, shaft/body or
distinct-hardware intersections above 0.01 mm³, and no Boolean errors. It retained
**24 tool/body intersections**, involving 16 distinct screws:

| Access obstruction | Required assembly sequence / later access |
| --- | --- |
| Four `analysis_edge_screw_{left,right}_{4,5}` tools intersect both corresponding leg plies: eight findings | Install these backing screws before attaching legs. Later access requires supporting the assembly independently and removing the obstructing leg; never remove a load-bearing leg from a standing unsupported board. |
| Twelve `rib_*_front` tools intersect main panels, with four seam locations crossing two panels: sixteen findings | Install and inspect rib screws before face panels. Later access requires removal of the corresponding face panel(s). |

These are retained assembled-access obstructions, not silently exempted clashes.
The sequence describes access dependency only; safe erection, temporary support,
lifting, tightening and stability remain part of the assembly-plan audit.

## Follow-up identified at this predecessor checkpoint

Five additional service tests pass: all 132 conservative Ø12.7 × 31 mm rear LED
reservations and eleven 11 × 2 mm straight routing corridors clear the candidate
parts/hardware; all 228 minimum washer-bearing annuli fit the actual receiving
bodies. These are not a complete harness, bend-radius or capacity check.

Revise the top bolt layout, then recheck geometry and service space. Verify
actual head/driver engagement, all other edge/end distances, manufacturing
allowances and material/product assumptions. Keep viewer, metric/imperial
schedules and assembly notes synchronized and independently reviewed. Previous rejected FEA
force recovery remains unusable for joint sizing; none of these geometry checks
establish connection resistance, load sharing, sliding/tipping stability or a
climber weight rating.
