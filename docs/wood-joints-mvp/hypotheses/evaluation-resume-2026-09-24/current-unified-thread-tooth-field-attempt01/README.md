# Conditional Unified 1/4-20 thread-tooth field

**Prepared:** 2026-09-25. **Status:** runnable conditional elastic response
sensitivity; no accepted hardware law, physical bound, or capacity result.
This artifact advances the earlier
[current-thread engagement audit](../current-unified-thread-engagement-attempt01/README.md)
from applicability review to a reproducible ideal-profile calculation. It
does not change or qualify the current joint model.

## Result and use boundary

For the current four-stack patch
`bottom_center_right_cleat / base_rail_bottom_right /
base_principal_center_right`, the frozen geometry has four identical
unthreaded 6.35 mm bolt-shaft envelopes, 152.4 mm underhead-to-tip length,
127.0 mm nominal wood grip, and a gross nut display interval of
131.064–136.8044 mm from the underhead datum. The modeled nuts are solid
display envelopes without internal bore walls. The contact deck has no
thread pair, engagement card, or tie. These are geometry facts, not proof of a
1/4-20 delivered thread.

The four input axes are `bottom_center/clip_horizontal_bottom_right_1/rail_1`,
`rail_2`, `principal_1`, and `principal_2`, all under the current
`bottom_center_right_cleat / base_rail_bottom_right /
base_principal_center_right` patch. Their frozen geometry inputs and no-thread
contact contract are linked in [the inventory](../ordinary-patch-inputs-attempt01/inventory.json)
and [contact manifest](../ordinary-patch-contact-deck-attempt01/contact-manifest.json).

The conditional thread family below is the current ordinary-hardware catalog
lead: K.L. Jack [25C600HCS5Z](https://www.kljack.com/products/25c600hcs5z/)
(1/4-20, 6 in, Grade 5, zinc, listed 3/4 in thread length) with K.L. Jack
[25CNFH5Z](https://www.kljack.com/products/25cnfh5z/) (1/4-20 Class 2B,
Grade 5, zinc, 7/16 in across flats). These are not selected or received
parts. The supplier
thread-length field does not locate first full-form thread. A provisional
placement of that field gives only 3.4544 mm overlap with the gross modeled
nut envelope; it is an **example active length input**, not measured
engagement. The current hardware receiving gate still requires functional
full-height engagement through the nut ([ordinary hardware basis](../../../current-ordinary-hardware-basis.md)).
This partial-overlap case does not pass that gate.

The default `result.json` gives, for that named example, the following
conditional outputs:

| Quantity | Result | Meaning |
| --- | ---: | --- |
| Local paired-tooth stiffness density `k_u` | 345,375.7 N/mm² | Lu ideal local tooth law per axial engagement length; excludes bolt/nut body EA. |
| Stiffness for one pitch `P k_u` | 438,627.1 N/mm | Uniform-field one-pitch illustration. |
| Optional Eq. 57 thread-connection measure `K_c` | 535,697.0 N/mm | Bar-EA-informed load-sharing integral for Lu's uniform local field; not a demonstrated complete end-to-end bolt/nut tangent. |
| H28 midpoint full flank-reversal band | 0.079187 mm | Historical Class 2A/2B limit comparator, with relative rotation fixed. |
| Selected unpreloaded phase gap at `phase_fraction=0.5` | 0.039594 mm each direction | A neutral scenario parameter, not measured installed phase. |

The `k_u` field is the candidate local property for a future declared
distributed-spring sensitivity alongside explicit elastic bolt and nut bodies.
After the selected local fit gap is taken up, its assumed transfer density is
`q(x)=k_u Δu_local(x)` N/mm, where `Δu_local` is the relative axial opening at
that engagement location. A discrete axial slice `Δx` therefore has local
stiffness `k_u Δx` N/mm. Keep the bolt and nut bodies elastic so their body
deformation remains in those solids. This is a conditional local relation; it
does not supply a complete force-versus-end-displacement law for the whole
threaded subassembly, and the current solid nut has no bore or thread surface
to receive it.

`K_c` is an auxiliary value from Lu Eq. 57: its separate bolt/nut bar `EA`
terms determine the load-sharing function `f(x)`, and the equation integrates
`f(x) k_u(x)` over active length. It is therefore a bar-informed
thread-connection measure, not a standalone local spring and not established
here as complete end-to-end bolt/nut compliance. Do not apply that scalar
alongside explicit bolt/nut solids or substitute it for the distributed local
law. Neither result supplies radial centering, bending, torsion, loosening,
wood bearing, washer-seat compliance, or thread strength.

The script also exposes active length, friction, material moduli, Poisson
ratios, nut radial-equivalent diameter, nut across-flats proxy, bar root/bore
diameters, loaded direction, initial fit phase, and whether relative rotation
is held fixed. For scale, the same code produces `K_c = 761,391.6 N/mm` for a
5.7404 mm full-gross-nut-length comparator, but that is a separate
full-height hypothetical, not the current catalog-reference overlap or a fit
pass. At the partial-overlap length, Lu's own friction sweep endpoints
`μ=0.01` and `0.30` give `K_c = 529,643` and `552,720 N/mm`, respectively;
that source sweep is only a numerical sensitivity, not a friction interval
for the zinc-finished candidate. Using an equal-area circle instead of the
hex circumscribed diameter in the nut radial-expansion term changes this
example `K_c` from 535,697 to 531,280 N/mm. These variants show parameter
dependence; none is a physical lower/upper bound.

## Law and component boundary

Lu et al.'s [2019 article](https://onlinelibrary.wiley.com/doi/10.1155/2019/8424283)
models each engaged tooth as a tapered cantilever and sums its
deformation terms under the thread-flank axial line load `w_z` on a
unit-width slice along the helical contact coordinate. For one external
thread and one internal thread, the model
computes bending, tooth shear, root inclination, radial deformation, and root
shear. Lu's `α=30°` is the thread-flank half-angle in the force resolution;
`β=atan(P/(π d_p))` is the thread lead angle introduced in Eq. 38. At
unit-width line loading `w_z=1 N/mm`, each side gives a `δ_b1` or `δ_n1` tooth
compliance in mm²/N. In Eqs. 36–37 these compliances act against the force
gradient along helical coordinate `r`; Eqs. 38–44 apply `sin β` to express
the resultant stiffness per axial engagement length. The paired local axial
stiffness density is

```text
k_ub = 1 / (δ_b sin β)
k_un = 1 / (δ_n sin β)
k_u  = 1 / ((δ_b + δ_n) sin β)
```

Thus `k_u` has units N/mm², and multiplying it by an active axial length
produces an axial spring stiffness in N/mm. The implementation evaluates Lu
Eqs. 9–16 and 31–44, with the actual conditional profile geometry below.
This local tooth field includes Lu's bending, shear, root-inclination,
root-shear, and thread radial expansion/shrinkage (`δ_4`) terms. It excludes
the axial bolt/nut body `EA` extension. A future smooth-body plus connector
model must not add a second reduced thread-root/radial spring; any model with
resolved thread contact must replace or validate this local law to avoid
duplicating the same interface compliance.

Lu's additional load-sharing reduction uses thread stiffness density and
separate axial bars:

```text
λ² = (1/(A_b E_b) + 1/(A_n E_n)) (k_ub k_un)/(k_ub + k_un)
η(x) = F(x)/F_b = sinh(λ (L-x)) / sinh(λ L)
K_c = ∫₀ᴸ η(x) k_u dx
    = (k_u/λ) tanh(λ L/2)       [uniform tooth field]
```

Here `η(0)=1` at the loaded first thread and `η(L)=0`; `λ` uses separate
bolt/nut body areas and elastic moduli through Lu Eqs. 45–51 to set the force
sharing. The loss of bolt force along the length is the thread load-transfer
density `λ cosh(λ(L-x))/sinh(λL)`, which integrates to one. `K_c` is the Eq. 57
integral of load-share fraction times local tooth stiffness. In this artifact
it is an auxiliary bar-EA-informed thread-connection measure; the derivation
does not establish that it includes complete end-to-end bolt/nut extension.
It is **not** a thread-only local pair spring and must not be substituted
alongside explicit elastic bolt/nut solids. The code reports both the closed
form and a Simpson-rule integration of Lu Eq. 57 as an independent arithmetic
check.

For the ideal no-preload clearance scenario, the assumed local distributed
branch is
```text
q(x) = 0                                      while movement remains inside g_side
q(x) = k_u sign(Δu_local)(|Δu_local|-g_side) after that flank engages
```
Here `q(x)` is axial force transferred per unit axial engagement length, so an
interval `Δx` transfers `q(x)Δx`; the result is a distributed local spring
field, not a scalar whole-connection force law. This deadband is parameterized,
not a measured current fit. If relative nut / bolt rotation is free, thread
lead gives `Δz = P Δθ/(2π)` and the class-fit limits alone do not bound axial
movement. No rotation restraint is inferred from the wood hole or the separate
modeled washers.
The producer exposes this relation as `local_thread_transfer_density_n_per_mm`
and the `k_u Δx` slice stiffness as `local_thread_slice_stiffness_n_per_mm`;
the transfer function rejects an unbounded (`None`) gap rather than treating
free rotation as zero backlash.

## Unified profile substitution

Lu states that its detailed substitutions are for ISO metric threads and
publishes rounded normalized values in Eqs. 17 and 24. This artifact does not
silently label a Unified product as ISO. Instead it derives the ideal basic
60° Unified flank segment from the
[NBS Handbook H28 (1969), Part I](https://nvlpubs.nist.gov/nistpubs/Legacy/hb/nbshandbook28-1969p1.pdf),
Table 2.1 and Fig. 2.2, using pitch `P=1.27 mm` for the conditional 20-TPI
thread:

| Lu beam variable | External bolt thread | Internal nut thread |
| --- | ---: | ---: |
| `b/P` at pitch line | 1/2 | 1/2 |
| `c/P`, radial root-to-pitch depth | `1/(2√3)` = 0.288675 | `3√3/16` = 0.324760 |
| `a/P`, ideal sharp-root width | `5/6` = 0.833333 | `7/8` = 0.875000 |

The external depth follows from half the basic pitch-to-minor-diameter
difference; the internal depth follows from half the basic pitch-to-major-
diameter difference. At the pitch line the basic thread width is `b=P/2`.
The 60° flank slope gives `a=b+2c tan(30°)`. The resulting ratios round to
Lu's published ISO metric substitutions. This is a geometric basis for an
idealized beam-profile calculation, not evidence that the actual Unified
roots, truncations, radii, tolerances, coatings, lead, or thread angles equal
the ideal profile. The standard allows rounded root forms; Lu's beam uses a
sharp trapezoid and does not resolve that contact geometry.

H28 Section 9 relates 60° functional pitch-diameter change to axial pitch
change using `ΔE=1.7321 Δp`. For historical H28 UNC-2A/2B pitch-diameter
endpoints, the script calculates four endpoint pairings and a full axial
flank-reversal comparator `(D2−d2)/1.7321 = 0.01613–0.14224 mm`. Its
midpoint pair gives 0.079187 mm. The default 0.5 phase fraction assigns half
to each force direction. With unknown unpreloaded phase, a fixed-rotation
one-way gap can range from zero to the full band. With relative rotation
unrestrained, the axial shift is not bounded by that band. These 1969 limits
are historical inputs; they are not a current ASME B1.1 limit check or a
received-part fit measurement.

## Conditional inputs and exact current geometry

The default calculation uses the following named values:

| Input | Default | Basis and limit |
| --- | ---: | --- |
| Nominal major diameter / pitch | 6.35 / 1.27 mm | Conditional 1/4-20 UNC catalog family; the model's 6.35 mm shaft is an unthreaded occupancy envelope. |
| Basic pitch diameter `d_p` | 5.5251109 mm | Computed from the 60° basic Unified profile `D−0.6495190528P`; not a part measurement. |
| Active full-form length `L` | 3.4544 mm | Gross envelope intersection if K.L. Jack's listed 0.75 in thread-length reference were provisionally placed from the 152.4 mm tip; first full thread, nut chamfers, and active length remain unknown. |
| Nut radial `D_0` | 12.8316 mm | Circular surrogate equal to the circumdiameter of a nominal 7/16 in regular hex. Lu's nut radial equation is axisymmetric; the real candidate nut is hexagonal. |
| Nut across-flats proxy | 11.1125 mm | Catalog 7/16 in nominal hex; not a delivered or CAD inner-profile measure. |
| Bolt bar root diameter proxy | 4.76504 mm | H28 historical UNC-2A minimum minor-diameter endpoint, 0.1876 in; used only in optional `A_b` bar. |
| Nut bar bore proxy | 5.1181 mm | Midpoint of H28 historical UNC-2B minor-diameter endpoints 0.196–0.207 in; used only in optional `A_n` bar. |
| `E_b`, `E_n` | 200,000 MPa | Generic steel elastic reference in the project steel scenario and Lu's steel calculation; no actual alloy/property assignment. |
| `ν_b`, `ν_n` | 0.30 | Generic elastic reference only. |
| Thread friction `μ` | 0.08 | Lu's steel calculation/FE comparator input; not a zinc-finished current-part measurement. |
| Initial phase | 0.5 of the H28 midpoint reversal band | Analyst convenience case. It does not claim a half-seated installed thread. |
| Relative rotation | Fixed for finite clearance gap | Required mathematical condition; no physical restraint is established for the current patch. |

The nuts and bolts remain separate elastic bodies in the current input, and
the two washer roles remain separate modeled bodies. This analytical law
contains no washer, head, shaft, wood, bearing-seat, or hole-clearance
compliance. It cannot yet be mapped onto current mesh attachment points:
the current nut body has no internal bore, and neither part has actual thread
surfaces. No whole-body tie follows from this calculation.

The material reference is generic isotropic steel `E=200 GPa`, `ν=0.30` only
([AISC 360-22 material reference](https://www.aisc.org/aisc/publications/current-standards/aisc-360/);
project input note: [steel elastic scenario](../../../steel-elastic-material-scenario.md)).
It does not assign 254SMO or any specific delivered bolt/nut/washer alloy,
heat treatment, strength, yield behavior, or capacity. No 254SMO property is
used or transferred. The values are a generic elastic reference only; no
WJ04 hardware result or acceptance is transferred to this WJ24 patch.

## Applicability and next validation

Lu's [paper](https://onlinelibrary.wiley.com/doi/10.1155/2019/8424283)
supplies an engineering form for local tooth bending/shear,
radial compliance, and load sharing, but its physical evidence does not
validate this current candidate. Its own FEA examples include M6×1, M8×1.25,
and M10×1.5 metric pairs; its reused experimental tensile data are M36
metric-brass pairs. The paper reports its predicted stiffness above measured
values and gives no uncertainty interval for a Unified 1/4-20 pair. The
target has `D/P=5.0`; the paper's cited FE examples are about 6.0–6.67 and the
reused M36 tests have `D/P=9`. Profile mapping and analytical correctness do
not create a validated physical bound.

The nine focused tests establish the profile-ratio transcription, H28
endpoint arithmetic, force boundary conditions, Eq. 57/Eq. 58 agreement,
modulus scaling, length monotonicity, direction-specific deadband, and refusal
to report finite axial clearance when rotation is free. Those checks can
catch formula/unit/indexing errors before a parent native run; they cannot
establish predictive error for a real Unified thread pair.

A physical use of the finite coefficient needs an applicable independent
source validation for UNC 1/4-20 profile/material/engagement or a bounded
validation of this exact reduced law. A minimal isolated check, if no
applicable source exists, is one measured bolt/nut axial coupon with recorded
thread class/profile, actual active engagement, finish, relative rotation
restraint, and elastic material inputs. Measure the force–relative-displacement
slope after the measured flank gap is taken up; subtract or independently
measure the bolt/nut body extension so it is compared with the thread-pair
term. To validate the distributed load-sharing field rather than only its
end tangent, add thread-length-resolved bolt strain (or test more than one
engagement length). This is a route to establish applicability, not a
universal coupon prerequisite for running a clearly labeled numerical
sensitivity. Until a validation source or such evidence bounds model error,
the result remains a conditional diagnostic and supplies no conservative
resistance or physical stiffness bound.

## Reproduction and pins

Run with Python 3, no external packages:

```sh
python3 lu_unified_thread_field.py --output result.json
python3 lu_unified_thread_field.py --active-length-mm 5.7404 --output /tmp/full-height-comparator.json
python3 lu_unified_thread_field.py --active-length-mm 3.4544 --mu 0.01 --output /tmp/mu-001.json
python3 lu_unified_thread_field.py --active-length-mm 3.4544 --mu 0.30 --output /tmp/mu-030.json
python3 lu_unified_thread_field.py --active-length-mm 3.4544 --nut-d0-mm 11.66895995 --output /tmp/equal-area-D0.json
python3 test_lu_unified_thread_field.py
```

`artifact-pins.json` binds the code, test, generated default result, current
input inventory, contact manifest, and local source-reference files. The
source PDFs are primary-source editions; the local Lu PDF is an inspection
copy of the open-access article. No CAD, native CalculiX solve, geometry
change, capacity check, or physical examination was performed for this
artifact.
