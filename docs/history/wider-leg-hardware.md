# Wider-leg catalog hardware and local screens

The six-bolt option uses ordinary catalog hardware, without fabricated brackets,
custom plate washers or machined spacers. The model requires twelve complete
stacks, six at each leg. These are fresh-stock holes; do not enlarge or combine
old holes to reproduce this pattern.

## Purchase schedule

| Part | Per bolt | Total | Catalog selection |
| --- | ---: | ---: | --- |
| ½-13 × 5-inch partially threaded Grade 5 hex cap screw | 1 | 12 | [PECO 12X5HBG5USSZ](https://www.pecofasteners.com/details/item?itemid=12X5HBG5USSZ), explicitly 1¼-inch thread |
| ½-13 Grade 5 finished hex nut | 1 | 12 | [FMW Grade 5 zinc nut](https://www.fmwfasteners.com/products/1-2-13-grade-5-finished-hex-nut-zinc-plated), require SAE J995 Grade 5 |
| 2 × 2 × 3/16-inch bearing plate, 9/16-inch hole | 2 | 24 | Simpson **BP1/2**, one against each wood face |
| ½-inch SAE extra-thick hardened flat washer | 3 | 36 | [Wrought MCX 014943](https://www.wroughtwasher.com/standard-washers/extra-thick-mil-carb-mcx/), all three between nut-side plate and nut |

The order along the bolt is **head → BP plate → leg → rim → BP plate → three
MCX washers → nut**. Mirror the stack on the other side so heads remain outside.
Both square plates align with the leg axis. The three MCX washers provide
standard-stock spacing so the nut seats on complete threads after the smooth
shank has crossed both pieces of wood. They do not act as a composite plate.
No clamp-friction resistance or bolt preload is credited. Seat the assembly
snugly without crushing wood; do not apply a steel-to-steel torque-table preload.
Use dry interior service and recheck seating after wood shrinkage.

## Dimensions and receipt requirements

The [cap-screw dimensional sheet](https://www.valuefastener.com/documents/products/capscrewgr5-8.pdf)
gives a 1¼-inch thread reference, 0.385-inch maximum transition length and a
0.10-inch negative length tolerance for this bolt. The conservative minimum
smooth body is therefore **82.931 mm**, including the full negative length
allowance. Smooth body is the cylindrical portion before thread transition,
not merely the underhead distance to the first complete thread.

Each wood member must measure **37.5–38.5 mm** thick. The BP plates must measure
**4.5–4.9 mm** thick. Require a minimum **17.759 mm head and nut bearing-circle
diameter**, a nut no higher than **11.5316 mm**, an unobstructed 9/16-inch plate
hole and an unthreaded shank through both members. These are project acceptance
dimensions; do not substitute a fully threaded tap bolt. The dimensions refer
to installed parts, including coating.

MCX 014943 published ranges are OD **1.057–1.077 inches**, ID **0.526–0.546
inches**, thickness **0.156–0.188 inches**. Nominal modeled thickness is their
midpoint, **4.3688 mm**. All stock and thickness tolerance corners pass:

| Minimum reserve | Result |
| --- | ---: |
| Smooth body beyond second wood member | 1.031 mm |
| Nut seat beyond maximum thread gaging length | 0.637 mm |
| Tip beyond nut, in excess of two full pitches | 7.895 mm |

[Simpson C-C-2026, pages 53–54](https://ssttoolbox.widen.net/content/orplhjaqw1/pdf/C-C-2026.pdf)
provides BP1/2 dimensions and the bolt-plus-1/16-inch hole. It does **not** publish
a plate load rating or a guaranteed steel yield strength there. Its general
note on page 21 directs product-specific material inquiries to Simpson.
Consequently **plate yield ≥33 ksi is an explicit material requirement**, not
an assertion that the BP catalog establishes this property. Retain a supplier
material declaration for that requirement; a dimensionally matching plate alone
is not sufficient. The same deliberately low 33 ksi floor is used for the
MCX washer calculation; the manufacturer identifies those washers as hardened
Grade 8, HRC 38–45. No manufacturer contact or purchase has been made.

## Local calculation

[Reusable calculations](../mini_moonboard/wider_leg_hardware.py) accept the
current six bolt points and the force vector; the final assessment supplies
actual revised geometry and loads. The skew-group axial force solution uses
both moment components and the complete two-dimensional covariance. The
member-centroid separation is conservatively **38.5 mm**. Positive and negative
couple polarity are enveloped. The **2× prying amplification remains an explicit
assessment assumption**, not an independently established nonlinear contact
upper bound. It does not turn the physical lap joint into a hinge.

For illustration, **4.5 kN** along the leg produces a maximum **1.3125 kN** bolt
tension after that amplification in the 66/84 mm six-bolt pattern. Moving the
whole group does not change this local couple allocation.

The BP calculation distributes force uniformly over its square net area, then
checks independent radial cantilever wedges at the longest square-corner
radius. It ignores beneficial circumferential plate action and includes the
corners rather than silently using an inscribed-circle footprint. The support
radius uses the minimum bolt-head bearing circle even on the nut side.
Plate-strip strength uses the rectangular plastic section modulus
`t²/4` per unit width and a 1.67 factor; the elastic first-yield result is also
reported. This is an analytical plate model, not a Simpson rated assembly.
The rectangular-strip plastic criterion follows the yielding form of
[AISC 360, F11](https://www.aisc.org/globalassets/aisc/publications/standards/a360-16-spec-and-commentary_march-2021.pdf).
Uniform bearing and strip load distribution are assessment assumptions.

At the illustrative load and minimum 4.5 mm thickness:

| Local criterion | Ratio |
| --- | ---: |
| Plate plastic bending, including 1.67 divisor | 0.871 |
| Elastic stress / actual assumed yield | 0.782 |
| Douglas Fir–Larch wood bearing, 625 psi | 0.126 |
| Each separate MCX washer, elastic bending including 1.67 divisor | 0.139 |

The elastic **allowable-stress** comparison would be 1.307; this selection uses
the plastic strength criterion and must not be reported as passing that elastic
allowable-stress comparison. Actual service elastic stress remains below the
assumed yield in this illustration. Plate yield below approximately **28.75 ksi**
would fail this plastic comparison at 4.5 kN compression.

[SAE J429 Grade 5](https://www.portlandbolt.com/technical/specifications/sae-j429/)
at ½-inch diameter supplies minimum yield **92 ksi**, tensile strength
**120 ksi**, and proof stress **85 ksi**. Direct combined tension/shear is
screened by von Mises stress against half the yield stress, using tensile
stress area 0.1419 in² and a conservative thread-root shear section. The
independent wood-dowel lateral calculation retains only 45 ksi bending yield;
the residual bolt yield after axial tension must remain above that value.
This keeps bolt axial tension separate from, but compatible with, the existing
NDS bending/embedment calculation. It is not a claim of a manufacturer-tested
combined connection rating.

These local checks supplement the current member, splitting, placement and CAD
checks. They do not establish a whole-frame rating or reopen panel/floor scope.

## Follow-up material and prying audit

A targeted search for the exact **BP1/2, 2 × 2-inch** plate did not locate a
primary manufacturer report establishing its steel yield floor. ESR-4294 and
IAPMO ER-238 identify **BP1/2-3**, a different 3 × 3-inch product. A Simpson
response identifying BP7/8 as A36 likewise does not identify this product.
None of those values transfers to BP1/2. The explicit 33 ksi requirement
therefore remains to be confirmed by product-specific supplier evidence.

The 2× prying factor cannot be established from force equilibrium and nominal
geometry alone. Equilibrium fixes net force and moment, but does not determine
the bolt-tension/wood-contact distribution or the local member flexibility.
A stiffness-compatible unilateral-contact model or applicable validated
connection method would be needed to establish a mechanical bound. The current
calculation deliberately labels 2× as an assessment assumption; it must not be
reported as a proven maximum or as a completed physical prying qualification.
Changing an owner's assumption cannot supply that missing mechanical evidence.

`bolt_combined_screen(..., lateral_ratio=...)` now also reports an explicit
linear interaction: NDS lateral utilization plus axial stress divided by half
Grade 5 yield stress. Require that sum and the direct von Mises comparison each
be at most one. This conservative additional assessment rule does not claim to
be a manufacturer rating or an NDS-prescribed combined-action equation. Omitting
`lateral_ratio` produces no combined lateral/axial result, rather than silently
claiming completion from the residual-yield diagnostic alone.
