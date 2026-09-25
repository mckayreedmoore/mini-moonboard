# Conditional thread-fit travel for current WJ24 1/4-20 geometry

**Prepared:** 2026-09-25. **Status:** bounded ideal-fit comparator; not a
measured installed gap, actual WJ24 hardware finding, or capacity check. This
note tests a hypothetical matched `1/4-20 UNC-2A` external / `UNC-2B` internal
thread pair. No vendor part or class is selected for WJ24.

## Result

For full-form, ideal 60° Unified profiles with pitch/lead and flank-angle
errors set to zero and the nut held at a fixed relative rotation, the
NBS Handbook H28 standard-limit values give a total axial reversal-play
comparator of **0.01613–0.14224 mm**. The exact values and assumptions are in
the [attempt 01 calculation](hypotheses/thread-fit-travel-attempt01/README.md)
and [JSON record](hypotheses/thread-fit-travel-attempt01/calculation.json).

This is a useful nominal class-pair scenario, not a finite physical gap for
the current stacks. The numerical dimensions come from the primary [NBS
Handbook H28 (1969), Part I](https://nvlpubs.nist.gov/nistpubs/Legacy/hb/nbshandbook28-1969p1.pdf).
The currently listed ASME authority is [B1.1-2024](https://www.asme.org/codes-standards/find-codes-standards/b1-1-unified-inch-screw-threads-un-unr-thread-form);
its public listing confirms the standard covers Unified forms, series,
classes, allowances, tolerances, and dimensions, but does not expose the
numeric tables. Reconfirm the numbers against the purchased current edition
before using them as current procurement/acceptance limits. H28 §9 also
states that Unified lead error contributes to functional diameter at
`1.7321 × axial pitch error`; the inversion used here is an explicit
geometric derivation for ideal-profile flank clearance, not a quoted
standalone backlash rule.

The interval applies only with relative rotation restrained. A single-start
1/4-20 helix advances **1.27 mm per revolution**. If the nut can rotate, class
fit alone does not limit axial travel: axial translation and relative
rotation are kinematically linked. The thread classes give neither an
installed rotational restraint nor friction, preload, thread-end position,
or stop location. No self-locking assumption is made.

## Defined comparator

For the ideal matched pair, use the class-limit pitch diameters:

| Thread | Minimum pitch diameter | Maximum pitch diameter |
|---|---:|---:|
| External 1/4-20 UNC-2A | 0.2127 in | 0.2164 in |
| Internal 1/4-20 UNC-2B | 0.2175 in | 0.2224 in |

At the closest limit pair, the internal minimum minus external maximum is
`0.0011 in` diametral pitch-diameter clearance. At the loosest pair,
`0.2224 − 0.2127 = 0.0097 in`. For the symmetric 60° flank profile, the
ideal diametral clearance converts to total axial movement from one loaded
flank to the opposite flank as:

```text
b_axial = (D2_internal − d2_external) / 1.7321
```

The factor is the inverse of H28's Unified 60° functional-diameter relation.
The calculation is `0.0006351–0.0056001 in`, or **`0.01613–0.14224 mm`**.
It is the full reversal band between opposing flank contact states. A
centered idealized position would have half that travel to either side, but a
no-preload assembly is not known to be centered; from an arbitrary starting
position, one-direction travel to a flank can be anywhere from zero to the
full reversal value.

For this comparator, assume: standard `1/4-20 UNC` nominal geometry; an
external 2A and internal 2B pair whose final measured effective limits are
inside the cited bands; same-hand, single-start threads; at least one
mutually engaged full-form thread turn; nominal 60° flanks and nominal
single-start helix; no coating or plating outside the final accepted limits;
no pitch/lead, helix-form, flank-angle, taper, or roundness deviation from
that nominal form; and zero relative rotation during the axial
movement. It does not model root/crest interference, friction, preload,
flank elasticity, strength, or stripping. Because the public ASME B1.1-2024
sample omits its numerical tables, the present numerical interval is
explicitly the H28 reference-limit scenario until those table values are
confirmed against the current edition.

## Why this is not the installed WJ24 travel

The current [ordinary hardware basis](current-ordinary-hardware-basis.md)
describes 48 WJ24 candidate axes with 6.35 mm unthreaded CAD cylinders,
152.4 mm modeled length, and 127 mm nominal wood grip. It selects no
delivered bolt/nut pair and has no measured external/internal class, final
thread profiles, thread-start/end location, or assembled rotational state.
The listed finished-hex nut thickness envelope, 5.3848–5.7404 mm, is about
4.24–4.52 nominal pitches. That is the outside nut thickness, not the
full-form internal thread length: entry/exit chamfers and incomplete end
threads are not located in the WJ24 source record. The inherited 3.175 mm
modeled tip projection is also not a measured full-thread projection.

The fixed-rotation interval is applicable only if a full-form flank segment
is engaged and class limits are valid over that active span. The nut thickness
alone cannot prove this condition or identify which turns bear. If a partly
threaded bolt or chamfered nut leaves no complete full-form turn in overlap,
the comparator does not describe the initial engagement; the exact missing
geometry is the axial location of the first and last mutually complete
external/internal thread forms after runout and chamfer.

If relative rotation is free, the ideal screw kinematics are:

```text
Δz = p Δθ / (2π)
p = 1/20 in = 1.27 mm per revolution
```

The thread-class interval then only describes the local flank reversal band;
it does not limit multi-turn travel. A physical bound would require the
installed rotational-restraint condition and the actual thread-start/end and
seat/stop coordinates. Nut/washer friction or self-locking cannot be
assumed from the thread class. The basic-geometry helix angle at the basic
pitch diameter (`0.217524 in`) is about `4.185°`, but self-locking also
depends on friction and load/contact state, neither of which is supplied or
assumed here.

## Use and disposition

Use the **0.01613–0.14224 mm** interval only as a fixed-rotation, ideal-profile
`CLASS_2A_2B_FIT_GEOMETRY_COMPARATOR`. It can inform a named sensitivity or
sanity check without claiming actual WJ24 slack. Keep initial thread travel
for physical WJ24 stacks as `UNRESOLVED_AXIAL_SEATING_TRAVEL`; report the
missing inputs precisely as (a) current-edition table confirmation and
selected/delivered thread class/profile, (b) full-form overlap through the
nut chamfers and bolt runout, (c) initial thread phase/flank state, and
(d) whether rotation is restrained and where the actual axial end stops lie.
Do not turn this fit interval into bolt/nut stiffness, stripping resistance,
pullout capacity, or a pass. No friction coefficient, nut rotation restraint,
external signoff, hardware selection, or fabrication requirement is added by
this method note.
