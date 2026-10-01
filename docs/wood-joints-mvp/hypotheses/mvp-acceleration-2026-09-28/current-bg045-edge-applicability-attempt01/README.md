# BG045 NDS edge applicability and splitting boundary

**Disposition:** source-supported grain categories; conditional loaded-edge
comparison; no adopted Table 12.5.1C pass/fail and no splitting capacity.
The signed actions stay within the reviewed 92-axis geometry. This attempt
changes no axis or member, runs no CAD query or native solver, and makes no
joint acceptance.

## What the official NDS text settles

The reviewed official AWC NDS-2024 Chapter 12 text defines edge distance from
the nearest fastener center to the member edge, measured perpendicular to
grain. For a member loaded perpendicular to grain, it calls the loaded edge
the edge in the direction toward which the fastener acts and the unloaded
edge the opposite edge (§12.1.2.1, printed p. 81). For `D ≥ 1/4 in`,
§12.5.1.3 sends bolt edge distance and row-spacing details to Tables 12.5.1C
and 12.5.1D. Table 12.5.1C sets a 4D perpendicular-to-grain loaded edge and
a 1.5D opposite unloaded edge (printed pp. 98–99). For the named conditional
`D = 6.35 mm` scenario, those are 25.4 mm and 9.525 mm. The 2024 NDS errata
check recorded in the existing [finished-profile source pins](../current-knee-finished-profile-attempt01/source-pins.json)
found no change to these Table 12.5.1A/C numeric requirements.

Every reviewed BG045 block lateral action is in the XY plane, while the
proposed block grain and through-bolt axis are +Z. The whole block action is
therefore perpendicular to proposed grain; Table 12.5.1C's perpendicular
loaded/unloaded category applies to the conditional bolt scenario. The
existing NDS/TR12 `Ceg = 0.67` lateral-reference adjustment does not waive
that detailing provision.

The block's signed action is generally oblique to the rectangular source
envelope's X and Y faces. The NDS gives the direction phrase above, but does
not prescribe a first-ray, component-by-component, or other construction for
choosing one loaded edge when a fastener acts toward two adjacent faces. A
first-intersected-face ray is a clear geometric reading of the full action
vector; this review records it as a conditional interpretation, not as a
formula stated in NDS. It does not convert every signed component into a
separate Table 12.5.1C loaded edge.

For A1-rear axis 2, the block receives `(+50.096, −71.224, 0) N` at the
full-factor-one endpoint. Its proposed grain is +Z. The signed action and the
two-bolt group resultant both point toward −Y; the rectangular ray first
reaches the −Y face. The source-envelope center-to-face distance is 20.0 mm.
If that face is the loaded edge under the NDS direction wording, the named
4D comparison is `25.4 − 20.0 = 5.4 mm` short. The opposite +Y face is 113.35
mm away, greater than the conditional 1.5D unloaded-edge value. The 5.4 mm
arithmetic needs no delivered-stock inspection; it remains conditional on
the named bolt diameter, modeled envelope, and edge interpretation. It is not
an adopted NDS failure or a move instruction.

The other cases show why a face-selection rule matters. A12-rear and
K12-rear block axis 1 each have a +Y force component toward a 20.0 mm face,
but the full-vector ray first reaches +X, 44.45 mm away. Under a
component-face sensitivity, that +Y face is below 4D; under a first-hit
reading, +X is the candidate loaded edge and the opposite −X face is also
44.45 mm away. The official text does not resolve that distinction. The
previous proposal to require 4D from both Y faces is therefore a conservative
geometry sensitivity, not an NDS rule: Table 12.5.1C distinguishes one
loaded edge from its opposite unloaded edge and assigns different distances.

The header presents a separate scope limit. Its proposed grain is +X, while
each full lateral action contains both X-parallel and Y-crossgrain
components. The header actions are mixed to grain, at the angles listed in
[`load-classification.json`](load-classification.json). The signed Y-face
distances are useful component sensitivities, including 20.0 mm at the
A12-rear and K12-rear axis-2 −Y faces, but they do not establish a full-vector
Table 12.5.1C loaded/unloaded check. The load is lateral to the +Z through
bolt; the header's obliquity is to its grain, not to the bolt axis. This
assessment makes no §12.5.1.2(b) shear-area claim and no grain-angle edge
interpolation.

The complete seven-increment signed vectors, proposed grain axes, envelope
faces, ray and component sensitivities, source paths, and hashes are in
[`load-classification.json`](load-classification.json). The force direction
signs are stable over the seven increments in all three source cases. The
reported distances are model-envelope coordinates, not inspected finished
edges or verified lumber grain. Actual bolt diameter, finished profile,
tolerances, and member grain need confirmation before any final detailing
finding; those observations are not needed to record the conditional
20.0-versus-25.4 mm calculation.

## Splitting interpretation

NDS-2024 Table 12.5.1C footnote 2 is specifically about heavy or medium
concentrated loads suspended below the neutral axis of a single sawn-lumber
or structural-glued-laminated-timber beam. It calls for mechanical or
equivalent reinforcement to resist tension perpendicular to grain in that
condition and cross-references §§3.8.2 and 11.1.3. Section 3.8.2 says to
avoid designs that induce perpendicular-to-grain tension where possible and
to consider reinforcement sufficient for those stresses when they cannot be
avoided. Section 11.1.3 addresses eccentric connections that induce this
stress and requires appropriate engineering procedures or tests to ensure
the applied loads are safely carried. Those provisions identify a hazard and
analysis/test obligation; none supplies a general splitting-resistance
equation for this BG045 block/header topology.

The current case reports provide local fastener-plane forces, not a complete
BG045 member-section tension-perpendicular demand. The signed lateral force
vector alone is not that splitting demand. The reviewed NDS Appendix E
net-section and parallel-row tear-out methods do not become cross-grain
splitting checks. The existing EN 1995-1-1:2004 §8.1.4/Figure 8.1 screen is
not mapped to this end-grain-axis block/header detail, and the project has
not adopted an applicable EC5 edition, national annex, and complete factor
set. Therefore BG045 splitting remains an unresolved failure mode: no
splitting demand, resistance, capacity ratio, or pass/fail is reported.

## Conditional design-proposal dependency

Under the full-vector first-hit interpretation and current source envelope,
the A1-rear axis-2 −Y distance is the only first-hit block edge below 4D.
The existing axis-2-only proposal moves its Y coordinate from −155.70 to
−150.30 mm, which changes that modeled −Y distance from 20.0 to 25.4 mm. It
reaches the conditional comparator with no nominal allowance beyond 4D and
does not settle the unresolved NDS face-selection issue, the mixed-grain
header actions, or the conservative A12/K12 block-axis-1 component
sensitivities. The proposal screen also records the known BG003 bore-web,
washer-seat, and receiver dependencies; those remain attached to that
separate proposal. No axis change is established by this assessment.

Conditional proposals can be described with their geometry and consequences
now. A definitive detailing check needs a supported loaded-edge interpretation,
bound finished profile, tolerance, bolt diameter and grain assumptions,
header mixed-action detailing, and a mechanism-specific tension-perpendicular/
splitting method or applicable analysis/test evidence. Observed stock and
installation conformance are separate from conditional arithmetic. Report
required changes before altering the reviewed geometry; this packet makes
none.

## Sources and reproduction

The official AWC NDS-2024 sources and pins are listed in
[`source-pins.json`](source-pins.json). The Chapter 12 PDF SHA-256 is
`5fc837523ff10acc097a162718700a9b4ba64e627d2b0023439146d42fe4ee2a`; the
review used its standard text and did not attribute any wording to
Commentary. Official sources: [NDS-2024 Chapter 12](https://awc.org/wp-content/uploads/2026/08/AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-%E2%80%93-Dowel-type-fasteners.pdf),
[Chapter 3](https://web-media.awc.org/wp-content/uploads/2021/12/17210019/AWC_NDS2024_withCommentary_20240718_AWCWebsite_Chapter-3-Design-Provisions-and-Equations.pdf),
[Chapter 11](https://web-media.awc.org/wp-content/uploads/2021/12/17205958/AWC_NDS2024_20250124_AWCWebsite_Chapter11.pdf),
and the [AWC 2024 NDS resource page](https://awc.org/resources/2024-nds/).

Rebuild or compare only the source-pinned force classification from the
repository root:

```sh
python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-bg045-edge-applicability-attempt01/classify.py --write
python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-bg045-edge-applicability-attempt01/classify.py --verify
```

The producer verifies the three accepted numerical-demand reports and two
reviewed BG045 component screens before emitting the seven-increment
direction and geometry classification. It runs no native solver or CAD
query.
