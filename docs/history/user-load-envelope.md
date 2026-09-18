# One-person load and three-dimensional tipping sensitivity

Intended use is **one climber, 250 lb (113.40 kg) maximum**. The **300 lb
(136.08 kg) case is a sensitivity, not an increased rating**. Their static
gravity forces are 1112.06 N and 1334.47 N respectively. Neither weight is
a validated load rating for the current design.

## Results

Each candidate has 48 combinations. The table reports minimum dead/live
moment factor over all hold locations and horizontal azimuths:

| Construction | 250 lb, static, full mass, no projection, 300 N horizontal | 300 lb, same conditions | Worst 250 lb sensitivity | Worst 300 lb sensitivity |
|---|---:|---:|---:|---:|
| 2×8, incomplete timber-only | 1.813 | 1.783 | 1.100 | 1.032 |
| 2×10 | 2.044 | 2.010 | 1.241 | 1.164 |
| 2×12 | 2.183 | 2.147 | 1.325 | 1.244 |

The worst combinations use 80% mass, twice gravity force, 100 mm hold
projection and 300 N horizontal force toward the climber. Row 12 and the
leg-side tipping edge govern; all columns on that row tie for this edge
(the record names A12, the first encountered). Lateral/oblique edges do not
govern these particular cases, but they are evaluated and retained.

None of these specified combinations produces a negative net restoring
moment, but **all three fall below the 1.5 project target in some sensitivities**.
The incomplete 2×8 reaches only 1.032 in the worst 300 lb case, close to the
ideal rigid-body tipping threshold of 1.0. This does not clear the separate
legacy normal-force cases that previously indicated uplift.

At full modelled mass, the 2×12 retains the 1.5 screen in every evaluated
250/300 lb case. The 2×10 falls below it for the 300 lb, twice-gravity,
100 mm projection, 300 N horizontal case. The incomplete 2×8 falls below it
even at full mass in the 250 lb twice-gravity/100 mm projection/300 N case.
Thus 300 lb is not automatically free of design consequences, and reducing
frame mass can materially reduce tipping margin. These findings support
comparing a revised footprint and actual connection inventory before selecting
the smaller construction—not simply approving a larger board section.

## Method and scope

Run `uv run python -m fea.user_load_envelope` to reproduce
[`user_load_envelope.json`](../fea/results/hybrid/user_load_envelope.json).
The record hashes the calculation and geometry sources. It evaluates:

- Static gravity force and twice that force; the latter is an illustrative
  magnitude sensitivity, **not a prescribed or verified dynamic factor**.
- 100% and 80% of modelled frame mass, with the same centre of gravity and
  support geometry. Uniform mass scaling is not a substitute for remodelling
  an actual lighter frame or an altered material distribution.
- 0, 50 and 100 mm hold projection, normal to each climbing face: main holds
  project forward **and downward**; vertical kicker holds project forward.
- Each of 132 main hold centres and ten kicker foothold centres, individually
  carrying the specified resultant. This envelopes those point positions,
  not independent hand/foot force couples or a climber's body trajectory.
- No horizontal force and 300 N horizontal force over **every azimuth**,
  including lateral and oblique directions. The 300 N is illustrative, not a
  sourced governing climbing force. It remains 300 N in both weight cases.

The floor support polygon is the convex hull of actual CAD floor-contact
face vertices, **not the assembly's rectangular bounding box**. Each polygon
edge is a possible tipping axis. For its inward unit normal, let `d` be signed
horizontal distance from the edge and `z` the force application height:

```
dead restoring moment = frame weight × d(frame CG)
live signed restoring moment = downward force × d(hold) + z × dot(horizontal force, inward)
net restoring moment = dead + live
```

The worst horizontal azimuth for each edge is exactly its outward normal.
Evaluating that direction per edge envelopes all azimuths analytically; it
does not miss directions between sampled angles. Negative net moment indicates
that compressive floor support alone cannot provide static equilibrium.

Where the live moment overturns, the reported factor is dead restoring moment
divided by live overturning moment, matching the previous screen. A JSON `null`
factor means the live resultant restores about that edge, not missing data.
The **1.5 comparison target is a project screening choice, not a demonstrated
code requirement or approval threshold**. Each case retains the governing hold,
edge, load position, force direction, and moments for independent audit.

This extends the earlier sagittal screen using standard rigid-body force and
moment balance; tipping and sliding are separate possible loss-of-equilibrium
modes. See the open textbook's [rigid-body equilibrium](https://engineeringstatics.org/Chapter_05.html)
and [slipping versus tipping](https://engineeringstatics.org/Chapter_09-slipping-vs--tipping.html)
chapters. These mechanics references do **not** prescribe MoonBoard design loads.

## Inventory differences

The 2×10 and 2×12 reuse the published drilled-timber/custom-angle mass and
fore-aft CG, verifying agreement with current CAD; transverse CG and floor
contact polygon are calculated from CAD. Wood density remains the assumed
600 kg/m³ and steel 7850 kg/m³. Fasteners, holds, wiring and glue are omitted.

**The 2×8 is an incomplete, hypothetical timber-only construction.** Its
existing angle arrangement does not fit. Its inventory uses undrilled timber,
with incompatible angles and all hardware omitted, consistent with its
ideal-bonded stiffness experiment. It is not a completed lighter alternative;
a viable connection redesign will alter its mass, CG, stiffness and possibly
footprint. See [2×8 feasibility](2x8-feasibility.md).

## What this cannot establish

The friction number is only `horizontal force / total downward force`: a
necessary aggregate translational demand with no assumed friction coefficient
or friction safety factor. It is not a sliding pass, and is not physically
sufficient when tipping is indicated. Yaw moment, local friction distribution,
floor unevenness/compliance, rocking dynamics and individual foot reactions
are not solved. No anchors or ballast are assumed.

This is **not new FEA**, connection-capacity analysis, construction approval,
or evidence that a climber can safely load the frame. Existing exploratory
normal-force cases remain in the [previous footprint study](hybrid-footprint-study.md);
these user-weight cases do not silently replace or resolve them. Agreeing the
governing load envelope and validating buildable joints remain necessary.
