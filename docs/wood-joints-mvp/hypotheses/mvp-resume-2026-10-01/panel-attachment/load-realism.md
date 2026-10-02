# Climber load realism: a bounded comparison basis

## Decision

The owner's October 2 clarification is **140 lb actual body weight, with a
250 lb intended upper limit including dynamic moves**. The 140 lb comparison
does not replace the 250 lb requirement. Ordinary 1g loading can help explain
the model, but cannot qualify that dynamic requirement.

The frozen `250 lb × 2 + 300 N horizontal + 100 mm hold offset` cases are
an inherited combination of explicit sensitivities. They are not measured
loads for this climber. **No concrete repeated climber load, repeated 2×
factor, repeated 100 mm lever, pound conversion error or outward-direction
error was found in the inspected current load path.** That finding does not
prove every physical force-sharing assumption, or establish that this
particular compound load is either unrealistic or a sufficient dynamic bound.

Compare 140 and 250 lb on the same frozen mounting, retaining the original
six-case envelope. Scaling the complete climber load by `140/250 = 0.56`,
including `300 → 168 N`, is a valid **same-acceleration hypothesis**. It is
not the original fixed-300-N sensitivity policy or a measured horizontal
force. A separate 140 lb/fixed-300-N comparison distinguishes those meanings.

## Where the numbers came from

The [historical load-basis record](../../../../history/hybrid-load-basis.md)
and [implemented weight envelope](../../../../history/user-load-envelope.md)
record one climber and a user-selected 250 lb maximum. They identify the
following as project sensitivities:

| Quantity | Recorded origin | Physical meaning in the current cases |
| --- | --- | --- |
| 250 lb | Intended maximum; 300 lb was a separate weight sensitivity | 113.3980925 kg; static weight 1112.055404 N |
| Factor 2 | Illustrative magnitude sensitivity, not a verified dynamic amplification | Total downward climber force 2224.110808 N; includes the static weight, rather than adding a second weight afterward |
| 300 N horizontal | Illustrative force over horizontal azimuths; the historical weight sweep kept it at 300 N for both weights | An additional component of the one applied resultant at the selected hold; not another climber |
| 0/50/100 mm offset | Guessed hold-leverage comparisons, not measured hold dimensions | Current force point is 100 mm outward from the explicit hold-face datum |
| 20 mm patch | Frozen load-distribution override | Size of the load patch; unrelated to the 100 mm force-point offset |

The current [load contract](../../evaluation-resume-2026-09-24/current-load-cases.json)
freezes the 2×/300-N/100-mm combination at A12, K12 or A1, with six specified
horizontal directions. It is implemented independently in
[`scripts/wood_joint_current_load_cases.py`](../../../../../scripts/wood_joint_current_load_cases.py).
The historical batch requested 250 lb; the response preparation supplied
its default factor 2 and 100 mm lever. This is source provenance, not proof
that the owner prescribed each sensitivity as a measured use condition.
The later owner requirement to include dynamic moves remains binding.

The 100 mm is **hold contact leverage**, not a climber-center-of-gravity
offset. About the panel midplane the lever is `100 + 18.25625/2 = 109.128125`
mm. Its moment is `lever_vector × force`. Adding the explicit half-thickness
changes the reference plane; it does not apply the 100 mm twice. A real
climber's body center, hand/foot positions and motion would determine a
different whole-body load distribution.

## Direction and the inspected current load path

The outward panel normal is `n = (0, sin 50°, −cos 50°)`. For a downward
force `(0, 0, −P)`, `F·n = P cos 50° > 0`. Gravity on this overhanging
panel therefore tends to separate it from its backing. Timber compression
contact alone cannot supply its inward tie reaction.

Read-only arithmetic on the saved frame's `W` matrix found:

- Twelve separate columns: gravity and climber load for each of six cases.
- Each climber column carries one live force, on only its loaded panel:
  `Fz = −2224.11080763025 N`, with the contract's signed 300 N component.
- The gravity-column resultant is `Fz = −2206.005479281 N`; the current
  producer multiplies this column by `1.1111358300342407` for its proportional
  25 kg accessory allowance. It adds the climber column once, without that
  gravity multiplier. Changing climber weight must leave this dead load alone.
- Recovering physical moments with the documented 1000 mm rigid-rotation
  scale, all six global live moments agree with `r_force × F`; maximum
  discrepancy is `2.794 × 10⁻⁹ N mm`. The original standoff wrench is present
  once. This is an applied-load arithmetic check, not a new frame solve.

No climber force was applied independently at all holds in these cases.
Their limitation is the chosen **single-hold concentration**, not a demonstrated
repetition of that force. Dead-load inventory, real dynamics and connection
resistance were not independently qualified by this arithmetic.

## What the single-hold load represents

For forces on the board, whole-body translation gives
`Σf = (−m ax, −m ay, −m(g + az))`. A downward 2mg resultant can represent
an instant with upward body acceleration g. It is not a two-climber case,
a rope fall factor, a time history, or a demonstrated upper bound on a catch.
The 300 N global horizontal resultant corresponds to horizontal acceleration
of magnitude 2.646 m/s² for 250 lb if all relevant contacts are included.

A hand can also exert a horizontal force that is opposed by a foot. Those
forces have little net horizontal resultant but can form a substantial
couple. The present isolated 300 N component has no opposing foot load: it
models a net horizontal force at that instant. It must not simultaneously
be described as an equilibrated static hand/foot interaction.

Likewise, concentrating the total resultant at one high hold is a useful
load-path sensitivity, but does not describe every dynamic stance. Multiple
contacts can reduce a selected hand's force, increase other local forces,
and shift moments. A useful future multi-hold case needs explicit contact
locations, a body resultant and moment, and an allocation satisfying both
`Σf` and `Σ(r × f)`, with any contact couples included. Equal division over
holds or screws does not establish that physical scenario. No such reduced
allocation is adopted here.

The reported screw peaks also contain the frame's response to the applied
wrench. Compression behind one part of a panel and tension at another can
form a prying couple, so an individual tie can exceed the free-load normal
projection. Backing, panel/contact compliance and the unmeasured Hillman
axial/lateral laws determine this allocation. Load arithmetic alone cannot
validate it. Moving four upper screw axes requires a fresh compatible
response for those stations; it does not correct any load number by itself.

## Smallest useful weight comparison

Keep the same mounting, backing, properties, screw laws, load patch, gap
conditions, dead load and accessory allowance across the comparison.
Retain all six original directions/locations; use distinct scenario labels.

| Scenario | Downward force | Horizontal magnitude | Face offset | Role |
| --- | ---: | ---: | ---: | --- |
| `250-dynamic-original` | 2224.111 N | 300 N | 100 mm | Preserve the original conditional envelope for the intended upper limit |
| `140-dynamic-same-acceleration` | 1245.502 N | 168 N | 100 mm | Actual-weight hypothesis; scale the entire climber force and its wrench by 0.56, preserving accelerations |
| `140-dynamic-fixed-horizontal` | 1245.502 N | 300 N | 100 mm | Separate fixed-horizontal sensitivity; scale vertical force and recompute the entire wrench, rather than multiplying the original wrench by 0.56 |

The first two scenarios answer the parent's proposed constant-acceleration
weight comparison. The third is the smallest additional comparison that
isolates the changed horizontal policy. Historical 300 N was independent
of weight; available sources do not choose either horizontal hypothesis as
the actual force during this owner's dynamic moves. At 140 lb, fixed 300 N
corresponds to 4.724 m/s² horizontal acceleration if treated as a net resultant.

For the rear-direction cases, force projections and the local midplane
moment illustrate why a lighter or less horizontal force does not uniformly
scale every demand:

| Applied climber force scenario | Outward projection | Up-slope component | Local X moment |
| --- | ---: | ---: | ---: |
| 250 lb, 2×, +300 N Y, 100 mm | 1659.444 N | −1510.931 N | −164.885 N·m |
| 140 lb, 2×, +168 N Y, 100 mm | 929.289 N | −846.122 N | −92.336 N·m |
| 140 lb, 2×, +300 N Y, 100 mm | 1030.407 N | −761.274 N | −83.076 N·m |
| 250 lb, 2×, zero horizontal, 100 mm | 1429.631 N | −1703.768 N | −185.929 N·m |

The last row is explanatory arithmetic, not a required extra frame run.
Removing +300 N Y decreases outward force but **increases the magnitude
of this local moment**. A claim that a smaller horizontal input necessarily
reduces every joint demand would be incorrect. These moments are applied
hold wrenches; they are not local bolt bending or individual screw demands.

If offset sensitivity later matters, retain the same 250 lb dynamic force
and compare a clearly hypothetical 50 mm offset against 100 mm. This changes
the applied couple without reducing the force resultant. Actual hold contact
geometry is not established by choosing either number. A 1g case remains
an explanatory diagnostic; passing it cannot cover dynamic moves.

## Primary-source context and limits

The CWA [General Specification, first edition January 2009](https://www.cwapro.org/file/secure/cwadesignpecfinal2022.pdf)
lists 1.2 kN for an unroped climber in Table 1 and directs surface-load
application to relevant locations in §5.5. Its §1.4 scope concerns structures
fixed in place and stationary in use. This gives a published comparison
reference, not adoption of 1.2 kN, deletion of the owner's dynamic requirement,
or qualification of this relocatable frame. The 2022 filename does not make
it a new edition.

Donath and Wolf's [2015 instrumented-hold study](https://edoc.unibas.ch/entities/publication/5fddf6ee-f521-40b5-9351-ef5b7c34d50b)
measured dynamic climbing interaction forces at four holds, with force
metrics varying across familiarization conditions. Bonelli et al.'s
[primary stationary-stance study](https://colombo.faculty.polimi.it/papers/Climbers%20muscle%20excitation%20and%20force%20distribution%20at%20different%20wall%20angles%20and%20body%20positions%20%5BBonelli25b%5D.pdf)
measured hand and foot forces and found changes with posture and wall angle;
its tested angles were near vertical, not this 40° overhang, and it did not
test dynamic catches. These sources support examining contact distribution
and motion. Their reviewed material does not establish this exact compound
load or a transferable peak factor for this board. No empirical hand/foot
fractions or lower dynamic factor have been imported.

## Input receipts and handoff

| Frozen input | SHA-256 |
| --- | --- |
| [Applied-load contract](../../evaluation-resume-2026-09-24/current-load-cases.json) | `9c7c43c51ce635ebfeaeddabdbbe2a0ac80dfd7819ec357662dd132db648b83a` |
| [Reduced static model inputs](../../mvp-acceleration-2026-09-28/reduced-static-attempt01/model-inputs.json) | `178ab4f9352c8b1f11525ffc6680efa5733ba74cedd609874e9a1966624740f9` |
| [Current original-station comparison](../two-receiver-frame-attempt03/comparison.json) | `0ff0dfc00c112a906910641141fd242f4a58295aa3324ca569132a3fa2d388a5` |
| [Its response](../two-receiver-frame-attempt03/response.npz) | `774c3bbddf8061f6b9d1cfdd5f22efbeb1025bd57431a249912ae8e60a731f52` |
| [Applied-load operators](../corner-frame-attempt01/operators.npz) | `f40bf53412afb400df23ff108e90bac66db3c493da26a19af5c05de329c165ad` |
| [Node geometry for moment recovery](../corner-frame-attempt01/model.json) | `d17dadd7c999e4a1634f53226cf63e131f547cd9cf5d46d87d75c935f2dc807e` |
| [Separate gravity/live-column producer metadata](../corner-frame-attempt01/frame-results.json) | `34eb66332a655244a4018e1b77344985e4c145fc946cb2028405a437003d0c41` |
| [Rigid-coordinate scale definition](../../mvp-acceleration-2026-09-28/current-frame-free-body-condensation-preflight-attempt01/condensation.py) | `7a887915cf84bcfef94c204baa2f47e428f81cead5c220101d9c225d2838de63` |

Only this leaf was added. No geometry/axis edit, frame/native solve, software
test, staging or commit was performed. The parent owns relocation, compatible
comparison runs and publication. The original response is preserved, and
neither a 140 lb result nor a new mounting comparison establishes a 250 lb
dynamic joint pass. The 47-criterion authority and joint/release HOLD
boundaries are unchanged.
