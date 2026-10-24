# Candidate 13 geometry applicability paper audit

This audit changes no geometry, hardware, force result, criterion or release. The source-bound per-occurrence record is `geometry-applicability-13.json`; its sources include final candidate 13 geometry, the independent footprint inventory and the six-case signed force/pressure atlas.

## Findings

The 54 short-of-7D markers are not 54 demonstrated minimum-distance violations. The verified 2024 NDS distinguishes full-value end distances from reduced-value minimums. It also treats edge distance separately: an end-distance factor cannot waive a mandatory loaded-edge minimum.

| Occurrences | Actual nearest-end classification | Geometric reference result | Current disposition |
|---|---|---|---|
| 40 | Square-cut sawn-member ends, including four new packer occurrences | About 6.833D; parallel-softwood-tension end ratio 0.976190476 if applicable. At least full 4D for principal perpendicular/compression reference. | Load direction, complete group and factor propagation still require classification. |
| 2 | Square-cut ends in outer posts at front-rail bolts | About 6.299D; tension end ratio 0.899887514 if applicable. Above full 4D reference. | Same classification hold. |
| 8 | Lower plywood-leaf ends | About 3.581D; conservative softwood-tension trial ratio 0.511623547. Nominal margin above 3.5D is only about 0.775 mm. | Panel strength-axis/species, actual leaf transfer and oblique application unresolved. No factor adopted. |
| 4 | Actual nearest sloped cuts at rear foot/floor receivers | Grain-ray diagnostics about 5.179D or 5.712D. | The verified NDS end-distance definition refers to a square-cut end. No sloped-end equivalence or factor adopted. |

A previous whole-profile flag obscured this distinction: the four upper center-principal occurrences have locally square nearest ends even though another end of the same member is sloped. The audit evaluates the actual nearest boundary plane rather than classifying every end from that global flag.

## Bolts 068 and 069

Both center-principal near-edge distances are **33.704 mm**, versus the **38.1 mm** conservative perpendicular-loaded-edge marker. Their net receiver forces generally point away from that edge, but their affine bearing pressures reverse through the wood thickness. In the forward case, the signed near-edge pressure components are approximately −24.372/+12.780 N/mm for 068 and −16.569/+8.683 N/mm for 069. The near edge therefore cannot be declared unloaded from the net resultant alone.

This is an **unresolved oblique/local-pressure applicability check**, not an unconditional declaration that Table 12.5.1C has been violated. The verified normative definition and table address principal parallel/perpendicular loading. No verified provision reviewed establishes that any nonzero perpendicular component automatically triggers 4D, gives an oblique edge interpolation, or maps a sign-reversing distributed pressure plus free couple directly onto a nominal bolt-load direction. Conversely, no source supports clearing the issue with an end-distance reduction or ignoring its local outward pressure.

## Primary rule boundaries

The cached official [2024 NDS Chapter 12](https://awc.org/wp-content/uploads/2026/09/AWC_NDS2024_withCommentary_20260911_Website_Chapter-12-Dowel-Type-Fasteners.pdf) was read offline and hash-bound in the JSON record.

- Sections 12.1.1–12.1.2: scope includes wood structural panels; edge distance is measured perpendicular to grain, end distance is defined from a square-cut end, and a row aligns with load direction.
- Section 12.5.1.2 and Table A: principal softwood tension has minimum/full end references of 3.5D/7D; compression and perpendicular loading have 2D/4D. The permitted actual/full end ratio is conditional on remaining above its minimum. The smallest applicable factor propagates across the group and relevant shear planes.
- Section 12.5.1.2(b): load inclined to the fastener requires an equivalent end shear-area check. It does not establish an oblique-to-grain edge interpolation.
- Section 12.5.1.3 and Tables C/D: edge and between-row distances are separate requirements. Length/D uses the lesser applicable wood-main/combined-wood-side length. Outermost cross-grain spacing and shrinkage detailing also need the correct complete-group definition.
- Sections 12.6.2–12.6.3: actual oblique group center-of-resistance/member-axis alignment and local stresses need engineering-mechanics evaluation.

The official cached TR12-2015 scope was checked only to establish that its generalized lateral single-fastener yield equations refer geometry and group requirements back to NDS. It is not substituted for the unverified full TR12-2026 text, and it does not qualify the present pressure/couple mapping.

## Other checks still missing

The JSON records 62 signature-group/member row-geometry screens. These are candidate rows, not qualified NDS rows: actual signed group loads are oblique, differ between connected members, and have moments. The quarter-offset stagger rule, complete connection membership and Table D length/D conditions remain unresolved. In particular, the top-rail 41.275 × 50.8 mm grid must not receive a blanket “all spacing passes 4D” label; a perpendicular principal-direction trial can change which spacing is between rows and which Table D requirement applies.

Local splitting/tension-perpendicular checks, inclined-to-fastener shear area, cross-grain shrinkage, unequal sharing and group-factor propagation also remain separate from net-section and bearing reference indices.

## Bounded geometry remedy for 068/069, if selected

Keep each center principal's panel-facing face, X thickness, bolt axes and hardware fixed. Adding solid stock at its +V back face would need **6.395705 mm** to reach 4D + 2 mm; a nominal 6.35 mm addition would miss that reserve by 0.045705 mm. A **9.525 mm** back-depth trial would change depth from 139.7 to **149.225 mm** and give a **43.229 mm** near-edge distance.

The added stock is away from the panels: panel back is near global normal 209.841 mm and the existing principal back is near 349.541 mm. This is only a geometric direction/bounds screen. It requires larger solid 2×8 stock, preserved upper S-seat cut, review of potential back overhang, all LED machining and screw backing, exact contacts/clearance and fresh matched forces/net sections. No candidate CAD or solver run was performed for this remedy.

Fabrication and climbing releases remain false.
