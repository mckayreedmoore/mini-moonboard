# Bolt and washer resistance basis

## Scope

This note defines inputs for the proposed timber-to-timber bolted joints. It
covers the bolt's steel material properties, the NDS lateral-yield diameter,
separate axial and shear first-yield references, and the wood bearing beneath a
washer. It does not rate a complete joint or establish a safe load.

The controlling wood standard for the candidate lane is ANSI/AWC NDS-2024.
AWC identifies the 2024 NDS as its current ANSI-approved wood design standard
and references it in the 2024 IBC ([AWC 2024 NDS](https://awc.org/resources/2024-nds/)).

## Dowel bending yield strength, Fyb

NDS-2024 §12.3.6.2 requires Fyb used in lateral-yield calculations to be based
on either bending yield derived by ASTM F1575 or tensile yield derived using
ASTM F606 procedures. ASTM F1575 applies to dowel-type threaded fasteners and
calculates Fyb from static bending tests ([ASTM F1575/F1575M-24](https://store.astm.org/f1575_f1575m-24.html));
ASTM F606 covers mechanical-property testing of threaded fasteners
([ASTM F606/F606M](https://store.astm.org/standards/f606)).

NDS `Fyb` and direct steel yield strength are separate inputs. NDS-2024
§12.3.6.2's test-derived route requires an applicable F1575 bending-yield
basis or an F606 tensile-yield basis with a supported evaluation into `Fyb`.
`nds_fyb_basis_status` now records the specified scenario, recognized NDS test
basis, and delivered-fastener conformance separately. A source-backed scenario
can be recorded before receiving evidence exists. ASTM F606 also requires a
separate reference to the supported evaluation that derives `Fyb`; a tensile
test reference alone does not complete that route. Any delivery status is
retained as a caller record with a source reference, not independently
authenticated by this helper.

The explicitly stated Grade 5 project minima from the cited supplier sheet can
support a conditional direct steel yield reference; they do not automatically
establish NDS `Fyb`. The NDS Commentary
Appendix I gives the approximate bolt estimate `Fyb ≈ (Fy + Fu)/2`. Applying
the documented 1/4-in Grade 5 scenario values `Fy = 92 ksi` and `Fu = 120 ksi`
yields a **106 ksi Commentary estimate** for an explicitly labeled engineering
scenario. It is not a product-standard minimum, measured bending yield,
normative/test-derived `Fyb`, or guaranteed lower bound. Do not use that
estimate to mark an NDS or project criterion passed without a reviewed method
basis. The source scope, calculation, and limitations are recorded in the
[conditional ordinary-bolt boundary note](hypotheses/evaluation-resume-2026-09-24/ordinary-bolt-resistance-boundary-attempt01/README.md)
and [steel-reference calculation](hypotheses/evaluation-resume-2026-09-24/ordinary-bolt-steel-reference-attempt01/README.md).

The conditional source records support explicitly specified Grade 5 project
property minima for a hypothetical conforming fastener, not the current
unselected hardware. No actual product conformance is inferred. The
Commentary's separate 45 ksi
Table I1 / TR12-2026 example still applies only to bolt/lag-screw diameters
`D ≥ 3/8 in`; it does not establish `Fyb` for a 1/4-in Grade 5 bolt.

## NDS full-body or thread-root diameter

NDS-2024 §§12.3.7.1–12.3.7.2 use root diameter `Dr` for threaded fasteners,
with a limited full-body exception. A conditional thread-root scenario may
derive `Dr` from the specified Unified thread class and assume that root
section across the wood-bearing and shear-plane regions; it must label that
thread-placement assumption. A threaded full-body bolt may use full-body
diameter `D` only if thread bearing occupies no more than one quarter of the
complete bearing length in every member holding those threads. Selecting that
exception for an actual candidate requires product/drawing dimensions or
measurements that establish the thread-bearing extents; a conditional model
may instead state and analyze explicit extents. The selector in
`nds_effective_bolt_diameter_in` checks each wood member separately and does
not infer thread placement from nominal bolt length or thread callout.

Selected `D` or `Dr` applies to NDS wood lateral-yield calculations only. It
does not select bolt tensile or shear area. If the selected diameter is below
1/4 inch, caller must also use the applicable sub-1/4-inch NDS reduction term
when calculating the yield modes; this module only flags that condition.

## Separate bolt tension and shear references

`bolt_first_yield_reference` requires all of these for each physical bolt:

- signed axial force in N (tension positive);
- two-dimensional lateral shear vector in N at the relevant plane;
- minimum tensile area in mm² for the controlling section;
- shear-plane area in mm², identified as shank or thread-root section with a
  conditional-scenario or actual-part basis;
- minimum material yield strength in MPa with its conditional-scenario or
  actual-part evidence basis identified;
- traceable material-property and area-basis descriptions.

It reports separate first-yield references:

```text
T_y = Fy × A_t
V_y = Fy × A_v / √3
```

The shear expression is the pure-shear first-yield stress under the von Mises
criterion ([NIST-hosted technical report](https://nehrpsearch.nist.gov/static/files/NSF/PB91217984.pdf)).
MPa × mm² gives N. These are unadjusted material references; they are not
NDS-adjusted capacities, AISC design strengths, or acceptance checks. The
areas require an explicit section basis. In a conditional scenario, a declared
Unified thread class can supply standard thread geometry, including standard
tensile stress area and a thread-root shear section if thread root is assumed
at the shear plane. The current ordinary-patch reference uses nominal
1/4-20 `At = 0.0318 in²`; see the linked calculation above. Claiming the
actual shank/thread section at a particular plane, using a larger smooth-shank
`Av`, or selecting the NDS full-body-`D` case requires product/drawing geometry
that locates the transition and the thread-bearing extents. Delivered
measurements are needed only for claims about actual received dimensions or
conformance, not to run a labeled conditional geometry scenario.

The helper can calculate a **nominal material first-yield interaction** for
simultaneous axial and lateral shear only when the caller identifies one
co-located section area and its basis:

```text
sigma = |N| / A
tau   = V / A
sigma_vm = sqrt(sigma^2 + 3 tau^2)
utilization = sigma_vm / Fy
```

This applies the von Mises material-yield criterion for plane stress
([NIST technical report](https://nehrpsearch.nist.gov/static/files/NSF/PB2009106744.pdf));
the shear stress is an average over the declared section. Separate minimum
tensile and shear-plane areas do not prove that the stresses act at the same
section. Without the common-section input and source basis, interaction stays
unresolved even when the separate component references are available. This is
not an AISC connection interaction or a bolt design strength. ANSI/AISC 360-22
§J3.7 is not applied because its use for this timber-to-timber bolt joint has
not been established
([AISC 360-22](https://www.aisc.org/aisc/publications/current-standards/aisc-360/)).
Bolt bending remains unresolved and is not included in the nominal interaction.
No preload, friction, fatigue, thread stripping, nut/head pull-through, or
load-sharing resistance is credited. Neither this material utilization nor
the separate component references close the connection check.

## Washer bearing

`wood_washer_annulus_reference_lbf` reuses the repository's DF-L No. 2 helper
with NDS Supplement Table 4A compression-perpendicular-to-grain reference
`Fc⊥ = 625 psi` ([2024 NDS Supplement, Chapter 4](https://awc.org/wp-content/uploads/2026/08/AWC_NDS2024-Supplement_20240719_Chapter-4-Reference-Design-Values_Website-1.pdf)).
The method computes a uniform-pressure reference over the circular annulus
outside the larger of the wood bore and washer opening. It assumes the full
washer footprint bears on sound wood. It omits bearing-area increase and
preload.

That value is only a conditional wood-bearing component reference. It does not
establish actual contact or load distribution. `washer_steel_resistance_status`
now records a specified washer scenario separately from delivered-washer
conformance, including standard/product definition, material basis, dimensions,
yield input, and source reference. Even a complete scenario returns the named
`washer_steel_bending_and_load_spreading_on_timber` method gap. Additional
catalog sourcing cannot close that gap: a reviewed method is still needed for
plate bending/spreading with the washer's support contact on timber. Until then
the steel-side resistance is not calculated, and the wood annulus reference
cannot close washer failure, bolt tension transfer, or complete-joint capacity.

## Machine-readable boundary

The module is [wood_joint_bolt_resistance.py](../../mini_moonboard/wood_joint_bolt_resistance.py).
Missing property-scenario values, source references, or component section bases
produce unresolved component results. `bolt_first_yield_reference` accepts a
specified minimum yield scenario and keeps delivered conformance in a separate
record. Its optional nominal von Mises interaction requires one common section
area and basis; it does not calculate bolt bending or a code design strength.
The washer helper accepts scenario and receiving inputs but returns the exact
steel bending/spreading method gap even when those inputs are complete. Basis
strings and caller conformance records are not independently authenticated.
