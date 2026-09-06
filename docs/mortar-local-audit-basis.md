# CalculiX 2.21 mortar: defensible local audit basis

Research only; no solver changes or new physical acceptance. The existing
[cube](contact-shear-coupon.md) and [inclined-leg](leg-shear-coupon.md) endpoint
global checks remain useful, but do not validate the local mortar law.

## Recommendation

Implement an archive-only **coverage and deformed-geometry diagnostic** first.
Do not implement `CPRESS = -K*COPEN`, pointwise Coulomb acceptance, or a
zero-penetration requirement using the mortar FRD fields. A genuine discrete
weak-law audit needs internal coupling matrices, multiplier and increment-state
data that these archives do not contain. Keep its status **NOT VALIDATED**.

This conclusion is stronger than a generic warning about weak enforcement:
the exact source uses different transformations for the internal law and the
exported stresses. The displayed opening is also a dual-integrated quantity,
not an independently measured point-to-surface distance.

## Exact-version evidence

Evidence is the official [2.21 source archive](https://www.dhondt.de/ccx_2.21.src.tar.bz2)
and [2.21 HTML manual archive](https://www.dhondt.de/ccx_2.21.htm.tar.bz2), inspected
locally under `/tmp/contact-source-2.21/CalculiX/ccx_2.21/src` and
`/tmp/contact-manual-2.21/CalculiX/ccx_2.21/doc/ccx`. The browser could not render
the compressed archives; conclusions below come from those local exact-version
files, not a moving online manual. Line references are within those archives.

| Evidence | Consequence |
| --- | --- |
| Manual `node144.html:61–90` | The stress/penetration relation is weak; MORTAR uses dual multipliers. Quadratic shape functions have negative regions. LINMORTAR omits midside multipliers; it is a different formulation. |
| Manual `node144.html:135–143` | Normal/tangent directions and segmentation are frozen during an increment. Endpoint current geometry need not equal the geometry of the discrete constraint. |
| `createbd.f:223–230`, `bdfill.c:424–434` | The dual gap accumulates shape-function × geometric gap × quadrature weight × surface Jacobian. It is not a raw nodal clearance. |
| `stressmortar.c:285–336,391–431` | Relative displacement is assembled through `Dd` and `Bd`; internal normal/tangent multiplier components use `Ddtil*cstress`. |
| `stressmortar.c:438–464,640–672` | Exported slip uses the assembled displacement history; opening generally uses `gap-ddispnormal`. Inactive branches zero slips/stresses, and excluded-node branches can zero every output. |
| `stressmortar.c:984–1017` | Before FRD output, stresses are overwritten by projections of `T*cstress` onto `slavnor/slavtan`. These are not the preceding `Ddtil*cstress` components used for complementarity. |
| `mortar_prefrd.c:45–57`, `frd.c:1598–1642` | The six values are copied into the CONTACT record and named COPEN, CSLIP1/2, CPRESS, CSHEAR1/2. ASCII numbers are float-cast then formatted `%12.5E`. No internal active-state or basis vectors accompany them. |

In particular, the FRD label COPEN does not establish units of millimetres for
this mortar path: the source expression retains the dual integration weighting.
Do not divide by a guessed nodal area, especially at quadratic corners or
partially covered faces. CPRESS is a transformed traction representation,
not a nodal force and not the internal weighted normal multiplier.

Positive **internal** normal multiplier represents compression, as follows from
the positive-part complementarity expression below. For frictional MORTAR the
ordinary active/inactive output branch uses opening-positive `gap-ddispnormal`;
this remains a weighted sign, not a geometric distance. Other branches reverse
that expression or zero it (`stressmortar.c:759–819`), so a generic parser must
not infer physical separation or activity from sign/zero alone. Tangent
components are in increment-frozen local directions, not global X/Y. The norm
is basis-rotation invariant, but the output transformation still prevents
assuming a pointwise Coulomb cone from that norm.

## Smallest useful check on current archives

1. Verify archive, launched deck, context and output digests. Derive slave
   node IDs and all six-node slave faces from the launched surface definitions;
   derive each corresponding C3D8 master top face from that same deck. Never
   infer patch membership from an FRD pressure value. Require finite values,
   unique node IDs and complete matching-time displacement/contact output.
   Report missing blocks as unavailable, not zero. MORTAR should retain the
   midside nodes; do not apply a LINMORTAR coverage exemption.
2. Match every accepted output time to the solver's accepted increment history.
   Preserve the existing full-step global results separately; do not imply
   that checking just times 1 and 2 covers intermediate increments. Parse FRD
   fixed-width adjacent signed fields and continuation records explicitly.
   Retain full double-precision deck coordinates and use matching DAT U where
   available, rather than rounded FRD coordinates.
3. Form all current positions `x+u`. For each patch represent its deformed
   master surface with the actual four-node bilinear face, not a mean ground Z
   or a plane through three selected corners. It can warp even though initially
   horizontal. Check nondegenerate Jacobians and orient normals away from the
   solid ground interior.
4. Evaluate the actual six-node quadratic slave face at all six nodes and at
   an explicitly recorded quadrature/subdivision sample. Project each sample
   onto its paired deformed master patch, solving the bilinear closest-point
   problem with a bounded domain. Report failed/nonunique projections and
   out-of-patch samples; do not silently clamp them to an apparently contacting
   edge. Signed normal separation is positive above the ground and negative
   for geometric penetration. Report extrema and their locations per patch,
   plus sampling refinement differences. Sampling is not proof of a continuous
   minimum; curved midsides can hide penetration between nodes.
5. Report FRD field extrema and the *diagnostic* quantity
   `hypot(CSHEAR1,CSHEAR2)-mu*CPRESS`, separately for corner/midside nodes and
   each patch. Do not label this a local friction-law pass/failure. Compare
   patterns with independently reconstructed separation, but do not equate
   FRD COPEN to that separation, pressure-zero to open, or CSLIP to global
   sliding distance. Total slip can include reversible tangential compliance;
   stick/slip classification requires the increment history and law state.
6. Propagate output quantization into every reported difference. For an ASCII
   field with exponent `e`, include half a last printed digit
   `0.5*10**(e-5)` plus float-cast error; propagate DAT precision separately.
   Include projection and surface-sampling error. A below-resolution residual
   is unresolved, not zero. No physical tolerance is enlarged to cover it.

The existing LINEAR law deliberately permits finite penetration. Therefore
`geometric_gap >= 0` is not a valid hard-contact acceptance gate. These steps
can reveal bad pairing, missing contact output, escaped patches and large
geometry inconsistencies, but cannot establish the permitted penetration from
FRD pressure. Compare geometry under matched increment refinement without
turning improvement into a material/floor rating.

## What a real discrete-law audit would require

For the currently used LINEAR normal law and ordinary friction regularization,
the source provides an actionable target. Let `L = Ddtil*lambda`, with normal
component `Ln` and tangent vector `Lt`; use the solver's frozen bases. Let
`q = ddispnormal-gap`, and `c = constantn` (the solver algorithmic constant,
not the normal stiffness). `getcontactparams.f:92–99` and
`regularization_gn_c.f:74–78` give `gn(Ln)=Ln/Kn`. The normal residual in
`stressmortar.c:492–499,541–566` is

```text
b = mu * (Ln + c * (q - Ln/Kn))
Rn = mu * Ln - max(0, b)                 # current mu > 0 case
```

At a converged admissible constraint this expresses compression-positive
`Ln >= 0`, regularized opening `s = -q + Ln/Kn >= 0`, and `Ln*s = 0`.
These are **weighted discrete variables**, not raw CPRESS and geometric gap.
For zero friction the source omits the `mu` factor rather than dividing by it.
Only eligible constraints are checked; retain all excluded/no-gap states as
explicit coverage qualifications, not silent passes.

For tangent regularization, `regularization_gt_c.f:62–68` uses the change from
the increment-start weighted multiplier: `gt = (Lt-Lt_start)/Kt`. With the
source's transformed increment-relative tangent displacement `ut`, set
`w = Lt + constantt*(ut-gt)`. The source branches check inactive `Lt=0`,
stick `ut-gt=0`, and slip `Lt-b*w/|w|=0`, alongside the active-set conditions.
At normal convergence `b=mu*Ln`; this is the discrete Coulomb bound and slip
direction. Do not substitute total FRD CSLIP for `ut` or forget `Lt_start`.
Guard zero norm explicitly, rather than evaluating the slipping formula for
an inactive state. Iwan friction or other regularizations need their own path.

The leanest future instrumentation would export, at accepted increments and
full precision, pair/node identity, eligibility/active state, frozen bases,
`Ln`, `Lt`, `Lt_start`, `q`, `ut`, `b`, `constantn/t`, normal/tangent law modes
and parameters. Export `T`, `Ddtil`, `Dd/Bd`, multiplier vectors and segmentation
if the audit must independently reconstruct those quantities rather than only
recompute the solver residual. Such instrumentation is **not implemented or
authorized by this research task**. Rebuilding the full mortar segmentation
from endpoint FRD geometry is not a smaller trustworthy alternative: it would
use the wrong increment geometry and omit redistribution of no-gap constraints.

For independent slave/master force and moment transfer, likewise use the
assembled coupling forces (source `stressmortar.c:856–910`), not a sum of
CPRESS at nodes. Ordinary free-node RF has contact-output semantics already
documented in the formulation study and is not another external support.

## Provenance and boundary

Selected source SHA256 values:

```text
stressmortar.c          d7cc1fa5d73aba85bbec7dd48f839e7b05514d91ab996025d089a12c45e84cd6
bdfill.c               5f7ee998bc0b327e046f44dbfe6ba3b0e671ae227f6ae936dbbd71b5a1a916cd
regularization_gn_c.f  d00205fde57f3bb34d26f5d2abf7a6a9daba75b38d9f3bd96282ad8f1192f0d7
regularization_gt_c.f  d94c65c830b790ccf3423e157c5d3cf433e51ca66bc1b120cccbb913bd276677
mortar_prefrd.c        3cf5cadcec1e862f6cd5d9c05285914a07dc6fd3fabee89bbd99f5d22adad939
frd.c                  9c8214f65fad852496438df1818b31adad6a3339da7ad36ca3c444e4e91c2158
```

No historical endpoint result is reclassified here. The cube supplies actual
sliding evidence and the inclined leg primarily bends; both retain their
published failures and their local-validation caveat. Even successful weak-law
replay would validate the specified numerical law only, not floor friction,
timber joints, free-board stability or engineering capacity.
