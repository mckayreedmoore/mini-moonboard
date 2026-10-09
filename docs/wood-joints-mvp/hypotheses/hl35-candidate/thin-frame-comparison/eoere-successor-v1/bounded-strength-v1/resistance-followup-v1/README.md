# NDS component resistance followup

The repository's existing NDS helpers produce useful finite component
resistances. This followup also evaluates NDS 2024 §3.4.4.1 reduced-depth
connection shear. It resolves the 44 blanket service-cut washer-landing
flags through current saved CAD geometry. It does not replace the frozen
[four bounded studies](../README.md) or establish complete joint resistance.
The compact [result](result.json) and [verification](verification.json) bind
the calculation, evidence and reproduction.

## Usable results

Every demand below comes from the six issued **untrimmed raised-rail** fields.
Current local geometry means `eoere-grid-aligned-wire-cutouts-v1`: the two
trimmed cleats and six revised wire-cut rails. No current response field is
introduced. New geometry combined with old actions is a sensitivity.

| Component or screen | Numerical reference | Matching demand and disposition |
| --- | --- | --- |
| Washer compression perpendicular to grain, nominal hardware | 1.766 kN for retained 3/8-inch frame washers; 1.899 kN for the new 3/8-inch washers; 3.437 kN for retained 1/2-inch frame washers | Highest nominal ratio 0.2473: 849.882 N against 3437.331 N, right rear leg nut, K12-right. Finite ideal full-ring bearing references. |
| Washer compression, catalog dimension corners | References range 1.705–3.467 kN | Highest mean-pressure ratio 0.2659: 453.293 N against 1704.976 N, `eoere_bolt_006/nut-capture`, A12-left. At the two-face affine full-contact limit, the highest wood-pressure ratio is 0.4679. These limits do not establish the actual seated moment or combined washer metal strength. |
| Cleat near-end transverse connection shear, untrimmed rectangle | 1.396 kN using NDS Eq.3.4-6, dry DF-L No.2, CD=1 | Largest matching grain-normal section shear 347.214 N, left cleat A12-forward; ratio 0.2488. This is a rectangular bending-member component comparison. |
| Cleat shear, trimmed engagement with original stock depth | Lowest parameter-screen reference 1.131 kN | Same 347.214 N demand; ratio 0.3070. Holding stock depth avoids a favorable decrease in the denominator after trimming. Current nonrectangular complete-joint applicability remains open. |
| Cleat shear, trimmed local depth and engagement | Lowest parameter-screen reference 1.243 kN | Same 347.214 N demand; ratio 0.2793. This is a second geometric sensitivity, rather than a different load case or an adopted complete cleat capacity. |
| Cleat single-bolt parallel row tear-out, shortened grain ray | Worst applicable parameter screen 2.141 kN | Upper rear left bolt `eoere_bolt_067`, A12-forward: parallel component 720.277 N, ratio 0.3364. Sloping-end qualification is unresolved; the earlier square-end reference at that station is 4.129 kN. |
| Cleat net parallel tension at loaded bolt planes | 22.112–23.379 kN with the inherited CF=1.3 material scenario; base Ft=575-psi area references are lower | Largest average-tension ratio 0.01666: 368.428 N against 22112.290 N at the left upper bolt-plane query. This checks average axial tension only; bending, torsion and local fracture remain separate. |
| Previously issued single-shear bolt yield components | 552 comparisons, references 0.755–2.686 kN | Worst own comparison: 1561.214 N against 2233.165 N, left rear-leg bolt, A12-rear, ratio 0.6991. This does not supply missing group/geometry factors or mixed shared-stack capacity. |

The references are in newtons, with 1 kN = 1000 N. They are component
references under the documented material and contact assumptions. They
are not product ratings or an allowable climber weight.

## How the resistances are calculated

The wood library in use is the repository's
[`bolted_timber_checks.py`](../../../../../../../../mini_moonboard/bolted_timber_checks.py)
and [`reinforced_timber_resistance.py`](../../../../../../../../fea/reinforced_timber_resistance.py).
Their already pinned NDS sources and original force intake are reused.
`skppy` imports SketchUp geometry; it is not the resistance library. External
XC implementations were inspected as a source survey; none is installed or
used to substitute another design basis here.

For dry DF-L No.2 and the inherited CD=1 scenario, the shear reference is
180 psi = 1.241056 MPa and perpendicular compression is
625 psi = 4.309223 MPa. The base parallel-tension value is 575 psi; the
inherited stock-size scenario applies CF=1.3 to that parallel value. No
perpendicular-tension value is inferred from the parallel or shear values.

The washer bearing reference is `Fc_perp * A`, where the supported annulus
is `A = pi/4 * (OD² - max(ID, wood_bore)²)`. It assumes a sufficiently
stiff washer distributes load over sound wood. The component reference
does not credit a bearing-area increase, installation preload or an
unmeasured moment. The two-face contact-limit pressure calculation uses
the existing affine annulus helper; it remains a contact sensitivity.

NDS 2024 §3.4.4.1 uses the near-end expression
`Vr = (2/3) * Fv_prime * b * de * (de/d)²` when the connection is less
than `5d` from the member end. At least `5d` from the end, Eq.3.4-7 omits
the squared reduction. Here `de` is the beam depth less the distance from
the unloaded edge to the nearest bolt center. The nominal untrimmed
cleat has `b=38.1`, `d=139.7` and `de=95.25` mm. The rear-loaded upper
group after trimming has local `d=133.247832` and `de=88.797832` mm.
The additional stock-depth screen retains `d=139.7` mm while reducing
only `de`; it gives the lower 1130.940-N reference.

The current [AWC March 2026 errata](https://awc.org/wp-content/uploads/2026/03/2024-NDS-Errata-and-Addenda-03.23.26.pdf)
explicitly directs perpendicular-grain fastener connections to §3.4.4.1
and explains `de`. The existing authenticated
[Chapter 3 PDF](https://web-media.awc.org/wp-content/uploads/2021/12/17210019/AWC_NDS2024_withCommentary_20240718_AWCWebsite_Chapter-3-Design-Provisions-and-Equations.pdf),
printed page 21 and Figure 3E, was checked visually. Primary industry
practice also uses this method: the
[MTC Solutions Beam Hanger Design Guide v4.0](https://mtcsolutions.com/wp-content/uploads/2024/02/BHDGvU4.0_Web.pdf),
page 123, applies the NDS near-end calculation outside its tested hanger
positioning cases. That supports the method choice; MTC product capacities
and positioning tables do not transfer to these Eoere joints.

The demand for this shear check is recovered on **grain-normal sections**
immediately outside each lower and upper bore-support band. Complete own
point forces, free moments and member selfweight remain in the cut
wrenches. The independent group-force replay differs by at most
1.002e-10 N. The previously reported 27.769-N force-only tensile opening
across a **Y-normal plane between bolt columns** checks another mechanism.
It is not substituted as the shear demand or divided by these resistances.

Appendix E.3 single-bolt parallel row tear-out uses the existing helper,
`Fv * t * loaded_end_distance`. The upper rear bolt's positive-grain ray
shortens from 87.3125 to 45.284053 mm. The encountered end normal is
50 degrees from grain. Substituting that shorter ray is a recorded
geometric sensitivity; it does not dispose the actual sloping fracture
paths, neighboring bolts, oblique components or simultaneous moments.

Net tension reuses the existing exact current CAD section areas and
same-cut demands. No second section export or rebuild is performed.
These area-based parallel references remain distinct from local split
resistance and a combined bending/tension check.

## Washer-support warning resolved

Previously, any service cut in a host member made its washer landing
conditional, even when the cut was far from the washer. The current
cached finished solids prove full support for all 44 flagged seats on
eight hosts. Each probe spans a 0.1-mm depth into the wood from the own
washer support face. Its annulus contains every nominal and catalog
corner profile: largest outer diameter and smallest supported inner
diameter. Bore subtraction and actual service cuts are present in the
cached solids. The smallest volume fraction is
0.999999999999734; the absolute full-support tolerance is 1e-4 mm³.

The calculation reuses 60 previous full-landing proofs on byte-identical
finished timbers and eight current trimmed-cleat footprint receipts.
Together these establish nominal geometric eligibility for all 112 wood
washer seats. The other 88 end seats are steel. This does not inspect
actual cuts or hardware, establish deeper timber stress distribution,
qualify pressure/contact stiffness, or introduce a rotational clamp.

## What remains active

Finite component references should be retained. The 44 service-cut
geometry warnings need not remain null once this scoped evidence is
reviewed. Complete-joint resistance stays open: the current trimmed
cleat requires a justified method for its nonrectangular, simultaneous
forces and moments; oblique group and mixed shared-stack resistance
cannot be obtained by assigning a generic factor or adding interface
capacities. Actual washer pressure moments, minimum delivered dimensions,
grade and combined metal strength remain unobserved.

These wood calculations do not resolve the preserved heel comparison,
where the nominal 6.35-mm-thick/6.35-mm-radius scenario has a 0.9983
stress/reference ratio, or the preserved panel/screw exceedances. No
geometry remedy, physical work, candidate selection, new native solve
or blanket approval/test prerequisite is introduced by this followup.

## Reproduction and retention

Run the owned `analyze.py` with `uv run python`, supplying `--output-dir`
under the existing ignored
`fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/bounded-strength-v1/resistance-followup-v1/`
directory. The issued output is `attempt02/`. Supplying `--compare` with
that directory recomputes and compares both serialized outputs without
writing a second detailed copy. `inputs.json` pins the original admitted
case packet, original section evidence and primary source files. The
complete 1071-pin map is in `attempt02/details.json`; sources are checked
before and after calculation. Exact byte reproduction, known-answer and
negative-control checks, and 52 affected library tests pass.

Keep the compact five-file packet, issued raw details, six existing admitted
fields, original frozen four-study evidence and shared primary sources
active. `attempt01/` is a superseded local-depth-only calculation; its
exact input and script bytes are retained in `source-at-first-run/`.
The superseded attempt and temporary source-survey exports may be archived
after checking ownership and consumers through the repository's archive
workflow. Nothing is pruned here. No copied solver, dependency installation,
mesh or large permanent raw report is added.
