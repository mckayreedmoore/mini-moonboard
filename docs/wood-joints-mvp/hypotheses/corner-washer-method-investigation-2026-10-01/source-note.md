# Conditional corner washer and bolt-bending method note

**Checked:** 2026-10-01. **Disposition:** method path identified; no joint
resistance, acceptance, or pass is established. No native analysis was run.

## Washer metal demand

The existing [washer-method review](../evaluation-resume-2026-09-24/current-washer-bending-method-attempt01-2026-09-28/README.md)
found no washer-specific product rating or accepted plate/contact resistance
method. The [generic annular-plate helper](../evaluation-resume-2026-09-24/current-washer-plate-response-helper-attempt01-2026-09-28/README.md)
is verified only for uniform pressure on a thin, isotropic annulus clamped at
both radii. It returns deflection and slope, not stress or strength; its
benchmark is not the washer/head-or-nut/wood-seat boundary condition.

A conditional **metal-demand** calculation does not need a catalog yield
value. With the assumed washer geometry, actual bearing-face footprints and
support/contact geometry, elastic steel properties, timber-seat compliance,
and signed action bound to each state, an elastic contact analysis can recover
the washer stress field. For first-yield screening, report the maximum
equivalent stress and its location; the required minimum yield for the stated
model is `Fy_required = max(σ_vm)` at unity. A model envelope may instead
report the maximum across explicitly bounded footprint, tolerance, support,
stiffness, and action cases. Neither quantity is an adopted resistance or a
pass. Without evidence that the geometry/contact/action envelope bounds the
physical assembly, call the result a conditional scenario, not a conservative
bound. In particular, the source tie scalar alone does not bound local
washer pressure or additional prying/bending in a physically coupled
bolt/washer assembly.

The method basis is classical plate mechanics where its assumptions apply:
the official MIT 2.080J plate note gives
`Mαβ = D[(1−ν)καβ + ν κjj δαβ]`, `D = E t³/[12(1−ν²)]`, and the plate
equilibrium equation on PDF page 1; its annular example is on page 2 and its
radial/circumferential moment relations are Eqs. 5.6–5.7 on page 5
([MIT OCW Recitation 5](https://ocw.mit.edu/courses/2-080j-structural-mechanics-fall-2013/de27f1d8f647ff995771d4b8d48d34bc_MIT2_080JF13_Recitation5.pdf)).
For thin plates, the corresponding surface bending stresses follow from
linear through-thickness stress: `σr = 6 Mr/t²` and `σθ = 6 Mθ/t²` (with the
analogous twisting term). For multiaxial steel stress, the plane-stress von
Mises measure is `σvm = √(σx² − σxσy + σy² + 3τxy²)`; see MCEER-08-0012,
Eq. 3-10, PDF page 55 ([NIST-hosted report](https://nehrpsearch.nist.gov/static/files/NSF/PB2009106744.pdf)).
These sources support the mechanics and a generic check, not a washer contact
boundary or design resistance.

Thin-plate applicability is doubtful for the current Type A Wide dimensional
lead: the sourced OD/ID bounds imply about 0.200–0.221 in radial annulus
width, while the sourced thickness is 0.051–0.080 in (`t/width ≈ 0.23–0.40`;
see [fastener/material screen](../hardware-material-specification-2026-09-30/fasteners.md)).
The washer is not selected, these are not delivered dimensions, and the
unsupported bending span may be smaller still. A candidate model should
therefore use a three-dimensional elastic solid/contact formulation unless a
separate applicability check justifies a shear-deformable plate idealization.
It must represent the actual head/nut bearing face and washer
profile, unilateral washer-to-wood support over the finished seat polygon,
cuts/gaps/flatness, and declared friction/preload assumptions. Mesh and
contact convergence, stress recovery at real radii/edges, and a matching
known-answer check remain necessary. A sharp idealized contact edge can create
a nonconvergent peak stress and cannot be used as a yield threshold without
resolving the physical radius/contact detail.

The [three-case axial-seat register](../mvp-acceleration-2026-09-28/current-corner-three-case-axial-seat-register-attempt01/README.md)
provides 126 signed tie states and 252 seat states. Its largest reported
three-case scalar is 119.343 N at BG045 `inner_header_1` (A12-rear); both outer
seats on a tie carry that same axial scalar with opposite receiver-force
vectors. This is only the A12-rear/A1-rear/K12-rear set, not a six-case
envelope. The register's `T/222.726212 mm²` is an ideal full-CAD-annulus
average, not a contact-pressure field. Bind each state/action and any
co-located prying or bending to the submodel before interpreting stress.

The current conditional `25NWUS` listing supplies a low-carbon-steel
description and dimensions but no numeric yield; the `25NWUS8Z` listing gives
hardness, not a yield minimum. Do not convert hardness, infer yield from bolt
proof strength, or adopt a washer capacity. A computed `Fy_required` can
inform a later material requirement, but comparison/acceptance still needs an
independently supported minimum yield or applicable product resistance plus
the bounded contact/action model.

## Quarter-inch bolt bending distinction

The [fastener source screen](../hardware-material-specification-2026-09-30/fasteners.md)
records a conditional J429 Grade 5 minimum tensile yield `Fy = 92 ksi` for
1/4–1 in, separate from `Fu = 120 ksi`. This is a direct steel material
property when the analyzed bolt is explicitly assumed to meet that standard
and size band; no current corner bolt is selected or delivery-qualified.

For a separate **bolt-material first-yield** check, use that minimum directly
with the actual controlling net section: e.g. elastic bending
`σb = M c/I` (or `M/S`) plus co-located axial and shear stresses, evaluated
with an explicitly stated yield criterion. This can report a conditional
first-yield reference, not a bolt or joint design resistance. It needs the
same-state bolt force, shear, moment and section/thread location; the axial
seat `T` alone is insufficient. Do not relabel this check as NDS `Fyb`.

For NDS lateral-yield calculations, the normative route is different. NDS-2024
§12.3.6.2 (official Chapter 12 PDF page 17) bases `Fyb` on ASTM F1575 bending
yield or tensile yield determined under ASTM F606. ASTM F1575/F1575M-24
§1.1 expressly covers bending-yield moment and calculation of `Fyb` for
dowel-type threaded fasteners ([ASTM F1575](https://store.astm.org/f1575_f1575m-24.html)).
NDS Commentary Appendix I.4 (PDF page 20) specifies the 5%-diameter offset
for bending-test data and says tensile-test data are evaluated to estimate
`Fyb`; its bolt approximation `(Fy + Fu)/2` is empirical. Thus I found no
source basis to simply set NDS `Fyb = 92 ksi` from the J429 minimum, nor to
call `106 ksi` a guaranteed value. A candidate-specific F1575 result, or
F606 tensile-yield evidence with a reviewed applicable evaluation into
`Fyb`, is the supported NDS path. ASTM F606 is a test-method standard, not a
product property assignment ([ASTM F606](https://store.astm.org/standards/f606)).

## Remaining closure inputs

- Bound the bolt/washer action envelope, including any force/moment coupling,
  prying, and head/nut tilt; the present three-case tie values are not by
  themselves that bound.
- Bind washer, bolt head/nut, finished wood support geometry, tolerances,
  material elastic assumptions, and contact/preload/friction conditions.
- Select and independently support a washer minimum-yield or product-rating
  basis before any strength comparison; obtain a candidate-specific NDS `Fyb`
  basis before using bolt dowel bending in NDS lateral yield equations.
- Verify contact/model applicability, discretization, stress recovery and
  sensitivity over the stated physical bounds. Keep timber bearing, thread
  engagement, bolt tension/shear/fracture, and complete-joint checks separate.

This note neither adopts a resistance nor closes `washer_bending`, NDS `Fyb`,
or any complete-corner criterion.
