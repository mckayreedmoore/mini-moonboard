# Current base: finite resistance and demand handoff

**The current ML24Z detail cannot be released from the inspected published
provisions alone.** The independent steel-calculation alternative also needs
product-specific material inputs that the nominal CAD does not supply. This
review preserves the selected `round-structural-development` geometry and
provides a concrete four-bolt leg-group demand calculation. It assigns no new
capacity and requests no physical floor test.

## What the manufacturer's provisions resolve

On September 12, 2026, both pages of the manufacturer's
[L-C-MLZ25 letter](https://ssttoolbox.widen.net/content/iczmiabsx6/pdf/L-C-MLZ25.pdf)
were downloaded and inspected, including the installation drawings. The bytes
match the existing reference SHA-256
`88d9051a9eadc08508a1a1c591914217309d6a2c1a281b375149d0cc57e584ff`.
The bearing illustration has a horizontal bend and timber end bearing, with
the supported member's grain horizontal. The current rim's grain is inclined;
rigidly rotating the illustration cannot match both its grain and its bearing
plane to the current assembly. The bearing row omits F2; the single/end row's
450 lbf F2 is consequently not a solution to this mounting. No independent
couple allowable is supplied. ML24Z loads cannot be increased for duration.

The [manufacturer's general wood-connector notes](https://www.strongtie.com/products/connectors/wood-construction-connectors/technical-notes/general-notes)
say steel is selected for each product and direct the designer to obtain
product-specific steel information. Their separate 33 ksi yield/52 ksi tensile
minimum concerns specified **noncatalog products**, not an ML24Z declaration.
Therefore neither those numbers nor generic structural-steel properties may be
silently used to qualify this purchased angle.

An independent calculation retaining ML24Z requires its minimum base-metal
thickness, yield/tensile strengths, applicable formed-bend properties and
toleranced hole/bend geometry. It must check flange/bend flexure, prying/contact,
net section, fastener-hole bearing/tear-out and screw/wood resistance under the
same simultaneous wrench. The nominal 2.55524 mm thickness in
[the geometry reference](ml24z-reference.json) is insufficient by itself.
This is a specific missing input, not evidence of failure or a requirement to
perform a new test program. Manufacturer applicability for the exact detail
remains the shorter route identified in [the base review](round-structural-base-review.md).

## A specific supplemental uplift candidate: H3

**Follow-up: H3 is rejected as a direct add-on to the unchanged base.** The
[current US-dimension placement check](round-structural-h3-fit.md) finds
insufficient rear reach and complete kicker interference at the front header
face. The candidate investigation below is retained for its source and load-path
reasoning; it is not a current hardware selection or an uncompleted fit task.

The **H3 hurricane tie** is a better bounded candidate than a generic strap:
the manufacturer explicitly identifies its
[single-plate attachment](https://seblog.strongtie.com/2023/12/second-day-of-trivia-hurricane-ties/).
Its tabulated uplift direction could provide a separate tension path while
retaining the existing ML24Z. This is a candidate for placement and analysis,
not selected hardware or a complete moment connection.

The [2026 catalog](https://ssttoolbox.widen.net/content/orplhjaqw1/pdf/C-C-2026.pdf),
pages 288–289 and 299–301, gives H3 DF/SP uplift of 400 lbf with four
0.131 × 1.5-inch nails into each member. Page 300 footnote 15 permits SD9112
connector screws for that nail size. That means **eight specified fasteners per
H3**, not the six SDS25112 screws used by ML24Z. The load is at duration factor
1.6; a normal-duration comparison is 250 lbf (1.112 kN), before any other required
adjustments. The short-nail uplift column does not establish its lateral
allowables. The catalog requires 3.5-inch rafter overhang for an exterior
installation and consideration of cross-grain effects. Paired connectors need
noninterfering fasteners; do not assume doubled resistance.

A feasible placement must put the lower flange against a **vertical header
face**, with all four lower holes inside the 38.1 mm header thickness, and the
upper flange against the rim side with all four upper fasteners contained.
It cannot simply occupy the ML24Z's header-top plane. The current rim is 50°
above horizontal; verify the production H3 hole pattern against that rim,
the horizontal bearing cut, existing SDS screws, post clips and panel/access
envelopes. An interior placement avoids assuming an exterior overhang that the
current model does not provide. No manufactured part may be bent to make it fit
unless its instructions allow that bend. These are definite geometric checks;
they have not been completed here.

There is also a definite mechanics limitation. A vertical tension force T at
offset `(x,y,z)` supplies `(Mx,My,Mz) = (y*T,−x*T,0)` about the base reference.
Thus separated H3 tension paths plus compression bearing can form some
overturning couples, but **vertical ties cannot supply Mz**. One tie cannot be
assigned an independent three-axis moment capacity. After obtaining current
simultaneous demands, solve for nonnegative tie tensions and compression-only
wood contact forces with their actual lever arms, leaving only supported
directional forces and admissible force application at ML24Z. Check the tied
receiver and its header/post continuation as well. If that decomposition
requires an unsupported residual couple, H3 supplementation has not closed
the problem. The former rigid-angle screw model must be revised to represent
the selected detail; attaching a tie does not retroactively qualify its old
moment demand.

This identified a specific part, fasteners, conditional uplift reference,
placement constraints and a load-path test. The subsequent necessary placement
check rejected this unchanged-base option. Any reconsideration requires an
explicit receiver/panel revision and then the actual hole and load-path checks;
the current evidence does not support installing H3.

## The actual leg groups and their minimum calculation

There are **two four-bolt groups**, one per leg, with eight bolts total. Each
group joins one rim to one leg through two 38.1 mm members. Two rows within one
group are not two independent two-bolt joints. The following coordinates were
read from the current model's connection objects, using the same rim endpoint
as [the existing demand extractor](../fea/round_member_connection_assessment.py).

The right group centroid is `(1219.2, 984.612524, 1556.537416) mm`; the left
group mirrors X. Each bolt has the following Y/Z offset from that centroid:

| Bolt suffix | Y offset (mm) | Z offset (mm) |
| --- | ---: | ---: |
| 1 | −6.964179 | −52.945928 |
| 2 | 25.175201 | −14.643706 |
| 3 | −25.175201 | 14.643706 |
| 4 | 6.964179 | 52.945928 |

For each accepted load case, retain all four signed force vectors on the same
member, their physical force-application points, and that member's grain axis.
Recover `F = sum(f_i)` and `M = sum(r_i cross f_i)` about this centroid.
The existing spring model places both endpoints at the common interface;
do not invent separated spring forces. For each member's section check,
translate this interface wrench to that member's centroid. The 38.1 mm
separation of member centroids generates eccentric lap loading. Merely negating
one member-centroid moment without translating the origin loses that effect.
These vector sums are equilibrium identities, independent of a wood design code.

For a transparent, equal-isotropic-stiffness *comparison* in the Y/Z joint plane,
`J = sum(y_i² + z_i²) = 7400 mm²` gives:

```text
fy_i = Fy/4 − Mx*z_i/J
fz_i = Fz/4 + Mx*y_i/J
```

The corresponding signed axial-force comparison is
`fx_i = Fx/4 + a*y_i + b*z_i`, where:

```text
[1364.581102   0.133369] [a] = [−Mz]
[   0.133369 6035.418898] [b]   [ My]
```

These are equilibrium-preserving minimum-norm allocations, not demonstrated
load sharing, washer contact, or bolt resistance. Do not replace recovered
individual spring forces with them simply because they give smaller demands.
The current diagonal shear and axial stiffness assumptions, contact conditions
and timber compliance must be assessed before choosing a design allocation.

Two useful necessary bounds require no equal-sharing assumption. If the four
bolt forces alone carry the group wrench, at least one bolt's lateral magnitude
is at least `max(hypot(Fy,Fz)/4, abs(Mx)/165.052692 mm)`. At least one bolt's
absolute axial force is at least
`max(abs(Fx)/4, abs(My)/135.179269 mm, abs(Mz)/64.278761 mm)`.
These follow directly from the triangle inequality. They are **lower bounds
on required bolt force**, not capacities; face contact sharing the wrench must
be accounted for separately. They can reject an inadequate detail early but
cannot establish adequacy.

Check individual bolts plus the complete group: directional dowel yield,
axial bolt/nut/thread strength, washer bending and timber bearing, spacing and
loaded end/edge distances, row/group wood failure and splitting, eccentric lap
loading, and the residual rim/leg section. Existing single-bolt lateral
references do not complete these checks. The distinction between fastener
yield, detailing and local wood failure is also explained in
[AWC's bolted-connection guidance](https://web-media.awc.org/wp-content/uploads/2021/12/17210649/StructureMag-NDS2015-PracticalSolutions-1611.pdf).

## Why whole-wall equilibrium cannot finish this connection check

A floor-contact equilibrium solution establishes one possible support-force
distribution. It does not establish the bracket or bolt forces of this
internally redundant frame. Self-equilibrated internal forces leave the total
external wrench unchanged; global statics alone therefore does not give a
finite upper bound for every connection force without further load-path and
compatibility assumptions. An arbitrary conservative-looking split of the
climber load is not a connection-demand envelope.

The minimum next demand artifact is one source-matched, equilibrated case with
all six signed screw forces per base angle, four signed bolt forces per leg,
actual application points, timber-contact reactions, and force/moment sums on
each receiver. It must keep simultaneous components together and distinguish
the current clamped-foot diagnostic from a support model using the stated
installation assumptions. Further load cases must then cover the intended
loading envelope. A complete resistance calculation and that demand envelope,
not a geometry pass or a single diagnostic solve, close this gate.
