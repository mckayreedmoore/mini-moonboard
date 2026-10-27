# V11 shorter-bolt builder geometry plan

**Current geometry ready to review. Cutting, drilling, committed assembly and climbing remain HOLD.**

Applies only to `v11-shorter-bolts-v1`, physical geometry `73ce1f19…`, checked receipt `cc2a1688…`, six-case bank `0ac9bb41…` and joint disposition `e846daf6…`. All six current cases are admitted; the checked receipt's earlier pending-mechanics sentence is preserved history. Matched numerical references remain separate from complete joint and physical fit qualification.

Use [member/cut planning](member-cut-planning.csv), [stock allocation](stock-allocation.csv), [152 receiver profile intersections](receiver-planning.csv), [66 screw axes](panel-screw-axis-planning.csv) and the [source-bound geometry packet](geometry-packet.json). Use the separate [current hardware schedule](../hardware/shopping-schedule-v2.json), [grouped shopping table](../hardware/shopping-list-v1.csv) and [112-axis hardware crosswalk](../hardware/axis-crosswalk-v1.csv). Use the separately bound bracket and rear-member templates for the same revision; this packet selects no new hardware or jig.

30 wood/panel profiles: **20 sawn members, four separate nominal 19.05 mm plywood cleat leaves, six existing face panels**. Installed assembly: 112 bolts, 24 angles, 66 Hillman axes, four metal spacers, no wood packers, 1,089 occupied parts. Glued cleat pairs are nominal 38.1 mm; perfect bond and 36.5 mm strength allowance are analysis hypotheses, not measured glue-up dimensions.

The provisional stock assignment covers each current sawn member once: **five 2×6×8, three 2×6×10, three 4×6×8, two 4×6×10**. Its member lengths are recomputed from current finished local envelopes; only the prior assignment pattern and 25.4 mm per-end trim / 3.175 mm per-member kerf assumptions are reused. Actual usable stock, defects and machining allowances remain unobserved. There is no 4×8 or packer allocation. Top, both sides, rear legs and outer front posts use actual 88.9 × 139.7 mm; floor runners, header, center supports and horizontal rails use 38.1 × 139.7 mm. Timber is the owner's kiln-dried Douglas fir No. 2 design assumption. Cleats need their own saved APA 24oc PS1 / Group 1 / five-ply / strength-axis-Z basis; face-panel ownership does not qualify cleats.

## Datums and cuts

Dimensions are millimetres. Each row retains its own world datum and positive L/U/V basis; L follows the saved grain/reference axis. A local L-span is a finished geometric envelope, not a saw setting or final square-blank length. Cut-face normals/offsets and boundary vertices are read from the bound cached BRep, with zero-based face indices; keep all other recess, service, bevel, hole and panel details in that exact full BRep. Do not scale-cut the CSV or infer a machining sequence from face order.

**Never reorder `blank_mm` as L/U/V.** Current sides finish at L 0…2539.767606 mm although their inherited tuple begins 2501.667606. Current center-principal finished L extent is 2455.367119 mm and rear-leg extent 1989.026085 mm; their source blank metadata is not substituted for these values. Header uses U 139.7 / V 38.1; floor runners use U 38.1 / V 139.7. Top uses U 88.9 / V 139.7 with U −50.8…+38.1. Panels' inherited vertex records are incomplete in L; current dimensions come from their finished BReps.

Preserve left/right labels and their independent datums. The assembly is not mirrored about world X = 0: rear-leg exterior planes are X −1308.1 and +1304.925 mm. Left and right horizontal rail spans are 1041.25 and 1077.275 mm. Source signs, negative coordinates and the right-side kerf offset are intentional.

## Receiver and screw planning

All 112 structural axes are represented by 152 physical member/profile rows. Their two endpoints mean increasing saved shaft parameter, not a selected drilling side. U_min/U_max/V_min/V_max labels identify profile boundaries only; they do not prove a flat supported finished land or actual fixture approach. Rear-foot profile prisms overlap 38.1 mm and must not be interpreted as two full physical walls. Use the current rear-leg/floor-runner finished-recess templates for those entries. Bracket-carried holes must follow the current fitting/wood crosswalk and verified physical bracket pattern.

Bore-envelope and nominal shaft diameters are analysis geometry, **not final bits, pilots, bushings or tolerances**. All Actual/Disposition cells remain blank. Keep the 66 purchased Hillman 42605 policy; no structural resistance or installation rule transfers from SDS/SPAX. Current source records include the two lowered kicker screws and two upper-center screw moves; the screw-axis CSV records all 66 current origins/directions without converting them into shop entry marks.

## Earlier templates

The C13 `owner-frame-v10/candidate13/packet-13-complete/{cut-plan,drill-plan}.csv` describes 116 axes, 32 profiles, half-inch enlarged cleats, deeper sides, a 50.8 mm top and packers. It does not govern V11. `paired-frame-v1/receiver-holes.csv`, its drilling requirements, and its member SVGs also retain earlier geometry and hardware. `geometry-packet.json#/historical_templates` lists exact added, removed and changed line IDs and exact paired-frame drawing paths whose profile records differ; no earlier bit/reach/stock dimension is adopted by this packet.

## Review and physical disposition

Review the current member datums/cut faces, named receiver intersections and separate hardware/template crosswalks together before assigning physical marks. Complete joint method/property, glue/bond, delivered shank/runout/seat/access, actual cuts/holes, panel-screw resistance and analytical no-slip support retain their recorded limits. The current joint disposition controls engineering status; this packet grants no purchase, cut, drill, fabrication or climbing release.

Reproduce without a CAD rebuild or solve:

```bash
uv run python fea/generated/v11-shorter-bolts-v1/build-package/geometry-packet/produce_geometry_packet.py --check
```
