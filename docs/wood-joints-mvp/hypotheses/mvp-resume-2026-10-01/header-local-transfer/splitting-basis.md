# Header local transfer: bounded splitting basis

**Current conclusion:** the target header bolts establish no applied Y splitting
load in the saved nominal states. Their full-depth Z shafts provide a mechanical
route for their own Z washer loads, conditional on adequate steel, seats and load
transfer. The actual outward Y actions belong to the kicker withdrawal/contact
path. Section VY alone establishes neither their point-load magnitude nor a
perpendicular-tension resistance requirement at a center-post cleat.

## Authority and applicability

Four primary technical sources were read; their limited conclusions are:

| Source | Applicable requirement / interpretation | SHA-256 |
| --- | --- | --- |
| [NDS 2024 §3.8.2, p.24](https://awc.org/wp-content/uploads/2026/09/AWC_NDS2024_withCommentary_20260911_Website-Chapter-3-Design-Provisions-Equations.pdf) | Avoid induced perpendicular tension where possible; consider sufficient mechanical reinforcement when unavoidable. It supplies no sawn-lumber Ft⊥. | `27cb362cdbedab537fd406a089ae774b30c13d9083ecba76bafb594b48ace384` |
| [NDS 2024 Table 12.5.1C note 2, p.99](https://awc.org/wp-content/uploads/2026/09/AWC_NDS2024_withCommentary_20260911_Website_Chapter-12-Dowel-Type-Fasteners.pdf) | Medium/heavy concentrated loads suspended below a single beam's neutral axis require mechanical/equivalent reinforcement against perpendicular tension. | `53f6ec05dfd1ceabeccd4d6e88c342111678d3da4631ee7b482b706f77c1780f` |
| [NDS 2024 §§11.1.2–.3, p.70](https://awc.org/wp-content/uploads/2026/09/AWC_NDS2024_withCommentary_20260911_Website_Chapter-11-Mechanical-Connections.pdf) | Evaluate actual local member stresses; an eccentric connection inducing perpendicular tension needs an applicable engineering procedure or tests. No universal FEM method is prescribed. | `45a3d78de1a4fba573589be0fc776e37bd581e4cedec24e38d63856161092d33` |
| [Official AWC **2018** Commentary C3.8.2 / C11.1.3, pp.208 / 249](https://awc.org/wp-content/uploads/2021/10/AWC_NDS2018-withCommentary_20200827_AWCWebsite_Commentary.pdf) | Historical explanation: prefer load entry through the compression side; stitch bolts/plates can resist otherwise unavoidable perpendicular tension. Seasoning defects preclude adopting clear-wood strength for commercial lumber. | `3402c7703cddef3e6693741ebaef9bfd0c1b0ddf075762c6f411fe1916751f7d` |

The public 2024 chapter PDFs contain specification text, not verified 2024
commentary. The historical commentary supports the mechanism, not a claimed
2024 commentary rule or a numerical Ft⊥. In particular, no fraction of Fv is
adopted as Ft⊥.

Note 2 concerns a particular suspension/load-entry geometry. A coordinate
below the geometric Z centre, a cut shear, or a nonzero couple is insufficient
to demonstrate that geometry. For the kicker path, assess bending in X/Y and
the actual tension-side load entry; Z=257.95 is the Z midplane, not an exemption
from Y-plane behavior. The read note supplies no numerical medium/heavy
threshold; the load classification must be explicit. Its tension-side mechanism
cannot be waived merely because an ordinary screw withdrawal law exists.

## Current geometry and attributable actions

Reuse [end-grain placement](../header-endgrain-placement/README.md) and
[header-joint-attempt02/final](../header-joint-attempt02/final/checks.json).
Header grain is X; bounds are X = −1219.2…1216.025,
Y = −175.7…−36, Z = 238.9…277 mm. Geometric centres are
Y = −105.85 and Z = 257.95 mm; they are not a verified perforated-section
neutral-axis assignment. Target shafts run in Z through 38.1 mm of header.

| Path | Actual header action and scope |
| --- | --- |
| Twelve target lateral bolt states, six cases | Seventy zero in-plane states and two pure-X states. Maximum interface \|FY\| across 36 joints is 7.404e-12 N: rounding, not a Y demand. |
| Post Z clamps | Header washer at Z=277 acts −Z; block contact at Z=238.9 acts +Z. Both enter the wood in compression. |
| Principal/knee Z clamps | Actual header washer at Z=238.9 acts +Z; block contact at Z=277 acts −Z. Both enter the wood in compression; a contact may be inactive in a particular state. |
| Ten kicker-header Hillman withdrawal ties | Outward +Y action at the front face Y=−36, opposed by actual inward −Y kicker-face contacts. Maximum nominal tie is 290.2331456 N: `a12-forward / kicker_header_left_5`, at (−1000,−36,257.95) mm. |
| Source dead-load nodal Y terms | Small self-equilibrated terms, approximately 2e-4 N maximum; retain in a local free body rather than inventing exact global zero. |

The [parent's frozen topology result](results/attempt01/result.json), SHA-256
`124c4700a46c652390b424aa864e39473738eaec7da441222d11a801bf17eb41`,
now binds these actions: 394 header actions per case and 1,092 physical wrenches
matching the operator exactly. Maximum body residuals are 6.789e-13 N and
3.201e-9 N·mm. No whole point-data export is duplicated here.
The saved VY=185.724277191 N at
`k12-rear / center_post_cleat_right` is an internal cut resultant, not transverse
bolt shear or a Y point load at that cleat.

Saved pure-Z tie points at principal Z=411.7 or knee Z=416 can describe the
other outer seat. Relocation along the same Z force line preserves the wrench;
local header bearing uses its actual own seat above. The saved point need not
be inside the header, and this is not an operator defect. The parent's maximum
Z relocation is 177.1 mm, with exactly zero change to the couple.

## One elementary check: the actual Z washer path

For `a12-rear / knee_outer_left_inner_header_1`, the existing same-state result
has T=233.181012397 N. The header head washer is on Z=238.9 and pushes +Z
into the header. Its supported area is 206.013152119 mm²:

```text
p = T / A_supported = 1.131874397 MPa
p / Fc_perp_reference = 1.131874397 / 4.309223308 = 0.262663203
```

These are reused [washer-seat fields](../header-joint-attempt02/final/joint-states.json),
not a new capacity or an Ft⊥ check. The necessary geometry/action condition is
a continuous through shaft with functioning head/nut/washer transfer, a supported
header outer seat, and the force directed inward at that seat. The bolt spans
the header depth and transfers the suspension force to compression bearing;
there is no separate unreinforced Z pull on that header face in this model.
Steel axial/combined strength, washer metal, nut/head transfer and any local
bearing spread must remain adequate. Existing wood pressure alone does not
qualify those parts or every adjacent ligament.

Thus the existing shaft can serve the mechanical Z transfer/reinforcement
function for its own axial load; it is not automatically qualified reinforcement
for all stresses. A Z shaft supplies no direct Y axial bridge across a
Y-normal split, and no friction or preload is credited. Z forces and their
couples still produce ordinary bearing, shear, bending and torsion; a couple
alone does not identify tensile stress perpendicular to grain.

## Exact remaining Y condition: tension-side combined load

Ordinary local screw withdrawal is addressed by an applicable withdrawal law
within its material, penetration and detailing limits. Do not add a separate
Ft⊥ check to every tie merely because its force points in Y. The saved role is
`non_qualifying_parametric_screw_withdrawal`: the numerical force is available,
but this leaf supplies no Hillman withdrawal qualification. The separate local
question is whether the **combined beam/connection load enters through the
bending-tension side and needs mechanical reinforcement beyond that law**.

The parent's gross front-face σXX is a bending-side selector, not σYY or a
splitting resistance. Of 60 kicker states, 59 are active; 46 have tensile signs
on both neighboring cuts (45 active), six are compressive on both, and eight
are near zero or straddle. Consequently a blanket compression-side conclusion
is unsupported. Conversely, 46 tensile selectors are not 46 demonstrated local
splitting failures. The largest withdrawal state, `left_5 / a12-forward`, has
σXX before ≈0 and after +0.056748084 MPa; it is not tensile on both traces.

**Concrete source condition for the elementary receiving-segment check:** use
`k12-rear / kicker_header_left_1` (row 1438), the largest active withdrawal
among the both-tensile selectors: +Y **223.037504211 N** at
(−200,−36,257.95) mm, with gross σXX before/after
**+0.698097835 / +0.697674290 MPa**. These are existing parent fields, not a
new splitting demand. Bind the actual front receiving face, finished
section/neutral axis in X/Y, screw's receiving segment, and same-state kicker
contact footprint. Determine whether the attached kicker's outward load is
suspended from that tension-side portion of the single header, or whether an
existing supported contact/connection actually routes it into the compression
side. Use that state's attributable forces and moments; an inward contact on
the same face or a negative group resultant alone does not prove the latter.

If the actual load remains a medium/heavy concentrated tension-side suspension,
note 2 requires an adequate mechanical/equivalent reinforcement route. A Z
clamp is not that Y route. If a justified compression-side route avoids the
induced perpendicular tension, no independent reinforcement demand is inferred
from the gross tensile selector alone. The ordinary withdrawal law still
requires its own applicability. Where the actual topology leaves induced
perpendicular tension, §§3.8.2/11.1.3 govern an applicable engineering transfer
check; they supply neither an Ft⊥ nor a mandatory FEM procedure. No actual
finished-section tension-side or Y reinforcement acceptance is established here.

The screw's own withdrawal qualification and front-margin decision remain with
the parent. This file neither determines that margin nor changes panel work.

### Parent receiving-segment result

The parent subsequently completed that bounded location/sign calculation in
[the load-path worksheet](README.md#receiving-segment-at-the-tension-side-probe),
using the connected finished section rather than the gross selector.
[Current result](results/attempt03/result.json), SHA-256
`fc01abc2ce52d1848c686dfb0f400f0fd41f277fbceefa417a13657add47b3e9`,
places the entire declared nominal receiving interval Y = −36…−81.24375 mm
on the tension side of the linear section field. The zero-normal-stress
planes are Y = −107.966453 / −107.956186 mm; tip margin is at least
26.712436 mm. This receiving segment supplies no demonstrated
compression-side route. The location probe is complete.

Local perpendicular resistance, load classification and adequacy of a Y
transfer/reinforcement route remain unestablished. The refined sigma_X field
supplies no sigma_Y or fracture strength. The existing Z path remains separate.

## Frozen bindings and closure

| Existing input | SHA-256 |
| --- | --- |
| `../two-receiver-frame-attempt03/comparison.json` | `0ff0dfc00c112a906910641141fd242f4a58295aa3324ca569132a3fa2d388a5` |
| `../two-receiver-frame-attempt03/response.npz` | `774c3bbddf8061f6b9d1cfdd5f22efbeb1025bd57431a249912ae8e60a731f52` |
| `../header-joint-attempt02/final/joint-actions.json` | `fcdd3e85f7856220504de79f818724dbf271f029f1066143ec8335f59ed966a4` |
| `../header-joint-attempt02/final/joint-states.json` | `a09e64e57c4110932d9eab3dcaafb1872228dd1f69142f61bd9286357acec48c` |
| `results/attempt01/result.json` (parent-owned) | `124c4700a46c652390b424aa864e39473738eaec7da441222d11a801bf17eb41` |

The current pins were checked; existing saved seat/action fields were read.
Official source PDFs were read from the existing cache or fetched into memory;
no reference copies or new result files were retained. This worksheet is the
only new file. No model, solves, tests, review, shared edits, staging or commits
were performed by the worker. The parent's added receiving-segment result
closes the location probe; any revised integrated force source must recheck
the actual combined Y path while preserving the ordinary withdrawal law's scope.
