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

Therefore, `nds_fyb_basis_status` accepts a numeric Fyb only when caller also
records one of those test routes, an evidence reference, and that evidence's
applicability to the delivered fastener. It does not derive Fyb from a catalog
grade, proof stress, or minimum tensile strength. For the F606 route, the
supporting record must show how tested tensile yield was evaluated into Fyb.
No average-of-yield-and-ultimate formula is applied automatically.

AWC TR12-2026 Appendix A Table A2 lists a 45,000 psi reference Fyb for the
specified bolt/lag-screw class with diameter at least 3/8 inch; the row names
SAE J429 Grade 1 as its carbon-steel example. That row does not establish Fyb
for a proposed 1/4-inch Grade 5 bolt. We assign neither 45 ksi nor a Grade 5
value to that hardware without an applicable test/evaluation record
([AWC TR12-2026](https://awc.org/wp-content/uploads/2026/06/TR-12_2026_formatted.V3.pdf)).

## NDS full-body or thread-root diameter

NDS-2024 §§12.3.7.1–12.3.7.2 use root diameter `Dr` for threaded fasteners,
with a limited full-body exception. A threaded full-body bolt may use full-body
diameter `D` only if thread bearing occupies no more than one quarter of the
complete bearing length in every member holding those threads. Otherwise use
`Dr`, unless a more detailed threaded-section analysis is supplied. The
selector in `nds_effective_bolt_diameter_in` checks each wood member separately
from measured bearing and thread-bearing lengths. It does not infer delivered
thread placement from bolt length or nominal thread callout.

Selected `D` or `Dr` applies to NDS wood lateral-yield calculations only. It
does not select bolt tensile or shear area. If the selected diameter is below
1/4 inch, caller must also use the applicable sub-1/4-inch NDS reduction term
when calculating the yield modes; this module only flags that condition.

## Separate bolt tension and shear references

`bolt_first_yield_reference` requires all of these for each physical bolt:

- signed axial force in N (tension positive);
- two-dimensional lateral shear vector in N at the relevant plane;
- minimum tensile area in mm² for the controlling section;
- actual shear-plane area in mm², identified as shank or thread-root section;
- certified minimum material yield strength in MPa;
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
actual loaded sections must come from delivered bolt geometry. Catalog nominal
diameter does not establish either area.

Combined axial tension and lateral shear remain unresolved. ANSI/AISC 360-22
§J3.7 defines a named interaction for bearing-type connections designed under
its structural-steel provisions ([AISC 360-22](https://www.aisc.org/aisc/publications/current-standards/aisc-360/)),
but its use for this timber-to-timber bolt joint has not been established. This
module returns separate component utilizations and `interaction_rule:
unresolved`; neither utilization alone can close the bolt check. No preload,
friction, fatigue, thread stripping, or head/nut pull-through resistance is
credited.

## Washer bearing

`wood_washer_annulus_reference_lbf` reuses the repository's DF-L No. 2 helper
with NDS Supplement Table 4A compression-perpendicular-to-grain reference
`Fc⊥ = 625 psi` ([2024 NDS Supplement, Chapter 4](https://awc.org/wp-content/uploads/2026/08/AWC_NDS2024-Supplement_20240719_Chapter-4-Reference-Design-Values_Website-1.pdf)).
The method computes a uniform-pressure reference over the circular annulus
outside the larger of the wood bore and washer opening. It assumes the full
washer footprint bears on sound wood. It omits bearing-area increase and
preload.

That value is only a conditional wood-bearing component reference. It does not
establish actual contact or load distribution. No washer steel bending,
spreading, dish, local yield, or through-hole resistance method is established;
those fields stay unresolved until the delivered washer and a supported model
are identified. A wood annulus reference is not a bolt tension or complete-joint
capacity.

## Machine-readable boundary

The module is [wood_joint_bolt_resistance.py](../../mini_moonboard/wood_joint_bolt_resistance.py).
Missing Fyb, yield strength, or actual section areas produce unresolved
results. A basis string records caller evidence but does not authenticate it.
Combined tension/shear and washer steel resistance always remain unresolved in
this bounded implementation.
