# Candidate 13 development layout

The preserved evaluated baseline is `eoere-candidate13-side-depth-v10`.
The [latest owner top-rail constraint](top-rail-standard-stock-owner-constraint-v1.txt)
supersedes its 50.8 mm top as a purchase design: evaluate standard actual
38.1 × 139.7 mm first, then 88.9 × 139.7 mm if exceedances remain. Changed
geometry needs its own forces and strength checks; no Candidate 13 passing
section result is carried over. The viewer below still shows the preserved baseline.
The [local viewer](http://127.0.0.1:8767/?model=eoere-current-frame-development&view=rear)
and [explicit V10 route](http://127.0.0.1:8767/?model=eoere-owner-frame-v10-development&view=rear)
show 1,167 occupied parts and 116 complete bolt stacks. The
[preserved V9 route](http://127.0.0.1:8767/?model=eoere-owner-frame-v9-development&view=rear)
retains its own 96-bolt geometry and evidence.

**Read the [center-principal correction](candidate13/paper-audit/center-principal-correction-13-v1.txt)
before the earlier paper audit.** Bolts 068/069 act away from the near edge
in all six cases. Their idealized perpendicular-resultant screen clears
the near unloaded-edge 1.5D and opposite loaded-edge 4D distances. The
optional both-edges 4D envelope is not an established NDS violation;
local pressure reversal does not automatically reclassify the loaded edge.
Actual oblique/eccentric behavior and splitting remain unresolved.

The [group and relocation handoff](candidate13/paper-audit/wsl-group-and-relocation-handoff-v1.txt)
requires a justified physical-group assessment in place of the unsupported
receiver-signature 1/n diagnostic. Preserve individual forces and couples,
establish shear planes and load sharing, and cover brittle wood and fitting
transfer. NDS, EC5 and CWC comparisons do not supply interchangeable factors.
Translating a complete angle cannot change its internal 41.275 mm top-grid
pitch. A new orientation/pattern changes the joint; principal moves must fit
both receivers, and rear-pair relocation changes pitch and moment arm.
No new relocation or steel-hole pattern is adopted.

## Geometry and material assumptions

| Component | Candidate 13 geometry |
| --- | --- |
| Top rail | Solid actual 50.8 × 139.7 mm; upper face retained. Eight additional near beam-flange bolts at the four top angles. Near post-flange holes remain omitted. |
| Top outer angles | Moved 50.8 mm inward onto solid timber packers. Associated holes and grips are regenerated. |
| Sloping sides | Solid actual 88.9 × 152.4 mm. Material is added behind the retained front faces and bolt grips. |
| Center principals | Upper profiles trimmed 12.7 mm for the revised top-rail seat. |
| Cleats | Four nominal 12.7 mm plywood leaves, two glued per side; nominal pair 25.4 mm, credited wall 23.8 mm. Outlines 410.3 × 215.9 mm, with three added direct wood bolts per side. |
| Cleat plywood | PS 1 APA Group 1 sanded plywood, Other category, strength axis along local vertical Z. Actual stamp, thickness and bond remain unobserved. |
| Upper rear-leg joints | Two nominal ½-inch Grade 5 bolts per side, revised diagonal centers and 50.8 mm extra rear-leg end material. |
| Header and rear feet | Four added shared header bolts; lower rear stacks use nominal ½-inch Grade 5 hardware. |

The model contains 22 sawn members, four cleat leaves, six unchanged wall
panels, 24 angles and 66 retained Hillman screw axes. Hardware totals are
116 bolts, 116 nuts, 232 washers and 60 spacer pieces: forty one-inch and
twenty half-inch spacers. Counts and dimensions describe the nominal model.
They do not establish delivered dimensions, shank coverage, machining marks
or permission to substitute stock or hardware.

The specified 152.4 mm side depth cannot come from the earlier nominal 4×6
stock, and nominal 2×6 stock does not provide the 50.8 mm top thickness.
Use the actual dimensional requirements when assessing availability; no
structural purchase selection or favorable green-lumber equivalence follows.

## Planning packet and evidence

The [geometry receipt](candidate13/geometry-receipt-13.json),
[six-case response bank](candidate13/response-bank-13.json),
[reference review](candidate13/reference-review-13.json), and
[additive paper audit](candidate13/paper-audit/paper-audit-bundle-v1.json)
are copies of the frozen isolated package. Its
[builder plan](candidate13/packet-13-complete/builder-plan.md),
[hardware BOM](candidate13/packet-13-complete/hardware-bom.csv),
[cut plan](candidate13/packet-13-complete/cut-plan.csv) and
[drill plan](candidate13/packet-13-complete/drill-plan.csv) remain conditional
planning records. Axis coordinates are not necessarily entry-face marks or
bit settings. Actual/Disposition cells stay blank until observed.

The source package was frozen before repository integration. Its historical
execution denials, geometry-stage `current_response_computed=false`,
readiness `FULL_ANALYSIS_PENDING` label and viewer non-selection labels are
retained as issue-time metadata. The later own response bank and final
mechanics join authenticate six Candidate 13 fields and their replays.
The maintained revision index records the current development selection;
none of those stage labels supplies a structural release.

The [provenance map](../../../site/eoere-v10-candidate13-provenance.json)
maps 57 source artifacts, including the additive correction, to portable repository files. Six large JSON files
are stored as deterministic gzip; their decoded bytes retain the original
SHA-256 identities. The original paths inside frozen records remain intact.
The viewer uses additive document routes and shares the unchanged V9 meshes.
Raw case/operator banks and CAD remain in the retained isolated source package;
the portable source check does not claim those banks were copied or re-solved.

## Remaining engineering work

The [continuation evaluation](continuation-evaluation.json) records the new
84-row single-fastener yield scenarios, 24 rear-bolt full-couple reference
constructions, corrected geometry classification and all 13 component
dispositions. It reuses the unchanged six-case fields. Full connection
acceptance remains unresolved; panel-screw work is owner-deferred.

The adhesive subagent selected standard tan **Loctite PL Premium, model 1390595,
Home Depot SKU 223222**, as a conditional planning basis for the plywood-to-plywood
leaf bond. [Henkel's TDS](https://datasheets.tdx.henkel.com/LOCTITE-PL-Premium-Construction-Adhesive-en_US.pdf)
gives mechanical support for 24 hours and cure of 24–48 hours at 25°C/50% RH,
longer in cold/dry conditions. It supplies no cleat-specific full-face spread,
clamp pressure, bond allowable or creep/stiffness qualification. Its
lumber-to-plywood tests do not qualify the target plywood leaf bond. The
perfect-bond model assumption is unchanged and remains unqualified.

All 26 trial bearing flags across 13 components remain recorded. Their
`1/n` factors group matching receiver signatures; they are not established
NDS load-aligned rows or adopted Cg values. The 0.997005 legacy N/M diagnostic
is not a physical safety margin. The independent elastic steel reference is
0.422766. A complete force-and-moment connection criterion, applicable
end/edge/group checks, splitting, fitting/washer transfer, screw/panel
resistance, adhesive and support/contact applicability remain unresolved.

The top-grid spacing check remains conditional. For principal 068/069,
the [corrected completion index](candidate13/paper-audit/completion-index-v3.json)
supersedes the earlier inference from through-thickness pressure reversal
to loaded-edge classification. No full oblique/eccentric or splitting pass
follows. Proposed stock-depth or pattern changes have not been modeled or
adopted by this integration; the optional both-edges envelope does not itself
require a deeper principal.

The [development summary](../README.md) and existing
[completion ledger](../../wood-joints-mvp/completion-ledger.md#current-v10-candidate13)
record continued engineering work. Fabrication, drilling, structural assembly
and climbing remain on hold. The separate selected screw-and-bracket baseline
retains its own authority.
