# Four bounded strength studies

The owner authorized four further checks: timber bolts and splitting, the
bracket heel, washers and timber seats, and member stability/net sections.
This packet completes those bounded calculations. It prioritizes ordinary
equilibrium, connection detailing, section checks and hardware information,
reusing existing admitted fields and methods. No global response, native
mechanics run, frame redesign or physical test was performed.

The [inputs](inputs.json), [calculation](analyze.py) and [result](result.json)
are the reproducible record. Detailed rows stay in ignored output.

## Geometry and load identity

The local geometry is `eoere-grid-aligned-wire-cutouts-v1`: the two trimmed
cleats and six recut rails in the [current geometry receipt](../occupied-aligned-wire-v1.json).
All 100 bolt and 66 screw records compare exactly with the older evaluated
geometry. The six authenticated force fields belong to the preserved
**untrimmed raised-rail** revision, `eoere-bottom-rail-tnut-clearance-v1`.
They do not evaluate the revised cleat/rail geometry. No matching revised
operator or response was available.

Consequently, changed-geometry calculations below hold the old actions fixed.
They quantify local sensitivities; redistribution from the new cuts, changed
mass/centroids and local stiffness is unknown. Unchanged geometry and the old
fields are independently source-authenticated, rather than selected by a
document's title or a historical pass.

The six cases are A12 rear/forward/left, K12 right/rear and A1 rear. Each uses
one 250-lb climber multiplied by two: **500 lbf / 2224.111 N downward**, with
**300 N simultaneous horizontal force** and a **100-mm outward hold offset**.
All recorded gravity and the 25-kg allowance remain in the fields. The
multiplier is an equivalent static assumption, not an impact simulation or
validated dynamic limit. The no-slip floor assumption remains unverified.

## 1. Timber bolts and splitting

The 552 supported single-bolt component comparisons retain the six-mode
yield reference. The governing old-case component is the left rear-leg bolt
`lumber_leg_bolt_left_2`, A12 rear: **1561.214 N** lateral demand against an
unadjusted **2233.165 N** reference, ratio **0.699104**. For that component,
the required product `Cg × Cdelta` at CD1 is therefore at least 0.699104.
The previously published arbitrary 0.5 factor sensitivity gives 1.398208;
it is not the actual factor. Eight mixed/shared stacks per case still lack
an applicable complete lateral reference. None of the 276 recorded signed
receiver pairs establishes the existing helper's uniform load-aligned row
prerequisite. Actual group/geometry factors and complete joint resistance
remain unresolved.

The trim changes the upper rear cleat bore's grain-positive ray from
**87.3125 to 45.2841 mm**. Its transverse ray toward the trim changes from
**44.4500 to 37.9978 mm**. Both now meet an oblique boundary, whose normal
is 50 degrees from grain. These are center-to-silhouette rays, rather than
the previously reported minimum bore-edge distance perpendicular to the
cut. A square-end factor or perpendicular-edge benchmark cannot qualify
this oblique, eccentric connection.

A new force-only splitting check cuts each cleat between its two Y bolt rows,
at Y = -105.85 mm. Complete nominal bore supports are clear of the plane;
all other recorded cleat external actions have zero Y component. Summing
the high-Y portion's own forces establishes a necessary integrated
perpendicular-to-grain tensile demand under these fixed actions. It is
positive in **all twelve cleat/case combinations**, ranging from
**1.576 to 27.769 N**; the maximum is the left cleat in A12 forward.
This is a force-only lower bound, not a peak stress or failure load.
Moments, shear and other crack planes can require more tension. The retained
X-axis bolts lie parallel to this crack plane; their existing clamp forces
cannot be counted again as a direct tie across it.

The [earlier splitting packet](../../../../mvp-resume-2026-10-01/upper-corner-screw-layout/all-joint-splitting/README.md)
supplies useful method/applicability work, but evaluates a different wood-block
layout. Its hypothetical perpendicular tension/fracture properties and
conditional comparisons do not supply this cleat's resistance. The AWC's
[bolted connection guidance](https://web-media.awc.org/wp-content/uploads/2021/12/17210649/StructureMag-NDS2015-PracticalSolutions-1611.pdf)
likewise distinguishes dowel yield, detailing and local group failure, and
explains the absence of an NDS sawn-lumber perpendicular tension design value.
The pinned 2024 NDS sources and existing reviewed methods govern this packet's
calculations; the older article is explanatory guidance.

**Next useful input:** a matching revised field and an applicable complete
eccentric timber-group/splitting route. Another washer or bolt-yield pass
does not resolve this specific timber mechanism. No member enlargement,
new tie or cut revision is adopted here.

## 2. Bracket heel

The owner's **6.35-mm thickness / 6.35-mm inside-radius** scenario is retained.
All 528 nominal comparisons reproduce the existing governing result exactly:
**140.479 MPa**, ratio **0.998300** against the declared **235 / 1.67 =
140.719 MPa** comparison. A12 left, the upper-left angle's arm-z/far-plus
half-band, governs.

With inside radius fixed at 6.35 mm and every root wrench/gravity bound fixed,
the scalar reference is reached at thickness **6.343792 mm**. The difference
from the nominal thickness is only **0.006208 mm**. The corresponding assumed
yield strength needed for that comparison is **234.601 MPa**. Uniformly
scaling every root action and its gravity allowance reaches the reference
after a factor of **1.001703**; this is not a climber load rating.

The same-case arm-z whole-flange wrench includes **30.008 N·m torsion**,
**10.408 N·m out-of-plane bending** and **24.624 N·m in-plane bending**.
The existing straight-plate torsion/warping reference is separate from the
half-band heel analogy. Adding their stress maxima would combine incompatible
representations rather than establish the formed heel's actual combined
resistance. The [existing heel study](../heel-assumptions-v1/README.md) and
[nominal scenario](../heel-assumptions-v1/nominal-scenario.md) remain frozen.

**Next useful input:** actual minimum thickness/radius, bend thinning, grade
and applicable formed-connector resistance. The scalar boundary is not a
receiving tolerance or a qualified 3D strength limit. A further radius grid
with the same unknown inputs has low value. EOTA's
[angle-bracket assessment report](https://www.eota.eu/sites/default/files/uploads/Technical%20reports/eota-tr017-am.pdf)
provides primary guidance on applicable connection models and calculation/
test evidence; capacities from another tested bracket do not transfer.

## 3. Washers and timber seats

The saved end reports include three nominal recipes per case: **176 washers
at 2.6416 mm**, **16 at 2.032 mm**, and **eight at 3.175 mm**. The larger
nominal thicknesses are present in these reports; not every retained stack
uses the same washer. Minimum catalog thickness corners are separate from
these nominal dimensions.

The 1200 own-end/case records and their catalog corners retain a maximum
**axial-only required washer Fy of 72.773 MPa nominal**, rising to
**156.176 MPa** at the worst catalog corner. K12 right, the right rear-leg
bolt's nut washer, governs both. These are prescribed-ring elastic plate
diagnostics; the product's numeric minimum yield strength remains unknown.

The new two-face pressure calculation quantifies an eccentric seating limit.
For the declared affine full-contact rings, allowable eccentricity before
one face requires tensile pressure is **2.783–3.709 mm** across the
positive-load scenarios. At the governing catalog axial-bending corner,
the two-face moment limit is **3017.519 N·mm**, or **3.0175 N·m**, for
**849.882 N** axial compression. This is a contact-field admissibility
limit, not the washer's moment capacity. A unilateral partial-contact field
may carry a different moment; it was not solved.

At each end's two-face contact limit, the largest peak support pressure
comparison on a nominally complete, perpendicular-grain wood ring is
**0.467871** against the unchanged **625-psi / 4.309-MPa** reference. That
result is conditional on the declared ring pressure and support. Forty-four
wood landings per case remain conservatively conditional because of local
cut/near-opening applicability. The new cleat receipt verifies nominal
footprint containment; it does not measure actual contact pressure.

The global capture law transmits **zero seated moment** and supplies no
rotational clamp. Physical moments and non-axisymmetric washer bending are
unknown. Thickening reduces the axial plate diagnostic but does not increase
the rings' geometric eccentricity limit. Therefore washer thickening alone
does not close combined washer/contact/timber resistance.

**Next useful input:** minimum washer dimensions/grade and applicable two-face
seat/contact behavior. No opposite-end or shaft bending moment is substituted
for an unmeasured end pressure couple.

## 4. Member stability and net sections

Across 132 case/member combinations, **23,844 same-cut samples** retain
signed axial forces, bending, shear, torsion, free couples and the recorded
affine gravity. The sampled fully braced gross normal maximum is **0.526047**;
the sufficient equal-shear-modulus gross shear/torsion reference reaches
**0.977592**. The largest full-span K1 normal sensitivity is **0.573935**.
No sampled full-span interaction exceeds one, but that does not qualify
its domain or actual bracing.

Four members exceed the weak-column slenderness domain under some recorded
compression: the header, top rail and both center principals. Their full
spans are **2435.225, 2257.425 and 2474.015 mm** respectively. Each needs
an independently justified weak-column effective length no greater than
**1905 mm** merely to enter that domain. A sensitivity capping only that
effective length at 50 times the short section dimension, while retaining
the original strong-column and beam assumptions, brings every sampled
domain inside its limit; the maximum normal ratio is **0.572863**.
This defines a restraint requirement without crediting an installed brace
or qualifying panel/screw load transfer as bracing.

Exactly **99 cached CAD section planes** cover the eight changed members,
including bore neighborhoods, rail route X coordinates and the cleat trim.
The upper cleat bore plane retains **94.581%** of its old already-bored area;
the lower cleat bolt planes retain **100%**. At sampled relocated wire planes,
current area can be **89.728%** of the old area at that same station; the
smallest sampled rail area remains **85.227%** of its gross rectangle.
The upper free cleat tail retains only **42.938%** near its top, where the
fixed-action average demands are effectively zero. That tail ratio is not
the reduction at the loaded upper bolt.

The necessary average axial and shear comparisons on these sampled current
sections are at most **0.016662 and 0.112722**. These dispose only those
average bounds under the old actions. They do not assess net bending,
torsion, bore/notch stress concentration, a continuous minimum or fracture.

**Next useful input:** actual lateral-restraint load paths and matching
revised member actions, followed by applicable net-section/connection
treatment. Low gross stress is useful evidence, rather than a complete
finished-member pass.

## Practical disposition and verification

The useful priority is now to reconcile the current geometry with its force
field, resolve the narrow heel/material margin, and address the specific
cleat splitting/oblique-end and member restraint questions. These results
do not show that the frame must be enlarged, and do not establish complete
joint strength. Preserved panel/screw exceedances remain recorded; their
owner-stopped remedies remain stopped. Physical testing, candidate selection
and fabrication are outside this reporting packet.

The original admission gate authenticates all six fields. Before/after hash
verification covers the complete inherited source union and every cached
section body. Known answers check opening/compression signs, refusal to cut
through a bore force support, square/oblique silhouette rays, the analytical
annulus eccentricity boundary and an exact CAD rectangle section. The existing
washer, NDS member and own-shaft force-bookkeeping tests passed: **38 tests**.
The owned script passes Ruff and formatting checks. Repeated final output
must match the issued result and detailed-row digests in [verification](verification.json).

Run from the repository root, using a new ignored output location:

```sh
.venv/bin/python -B docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/bounded-strength-v1/analyze.py \
  --out fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/bounded-strength-v1/REPLAY/result.json \
  --details fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/bounded-strength-v1/REPLAY/details.json
```

Keep the input, script, compact result and verification active, together with
the original geometry, admissions and reusable methods. Detailed rows and
superseded calculation attempts remain recoverable in the ignored packet;
no files were pruned. Older splitting results remain historical evidence.
No mesh materialization or viewer change is required by these calculations.
