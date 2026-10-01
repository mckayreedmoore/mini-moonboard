# Uppermost frame-block review, September 30, 2026

September 30 follow-up: the [service-upper review](../service-upper-frame-joint-review-2026-09-30/README.md)
adds the other four service cleats and an explicit partial-thread comparison.
Its [method correction](../service-upper-frame-joint-review-2026-09-30/method-correction.md)
supersedes the generic oblique-loading/shear-area wording below. Grain-angle
interpolation remains a declared historical-method sensitivity, with exact
2024 Commentary verification open. This packet's frozen numerical records
remain unchanged.

The upper blocks are useful parallel MVP work while the main worker resolves
the lower corner assembly and remaining floor-support cases. Earlier
[top outer](../top-outer-integration/README.md) and
[top center](../top-center-integration/README.md) studies established local
geometry, with stated limits. They did not establish current joint strength.
This packet completes a bounded extraction of current upper-joint actions,
signed outer-boundary classifications and conditional component comparisons.
It accepts no complete joint and closes no formal strength criterion.

The geometry is `led-clearance-2x6-runner-seated-blocks-v1` in
`compact-floor-flush-wood-joints-development`. Scope is the two top outer
cleats and two top center cleats: sixteen existing bolts, four per block.
Other upper service-level blocks, including the shortened upper-right G7
cleat, remain outside this packet. No reviewed geometry, panel outline,
Hillman screw axis or original leg/runner bolt arrangement changed. No native
solve ran. The selected angle-frame candidate and historical evidence remain
separate.

## Current actions and what they imply

The three authenticated conditional responses are A12-rear, A1-rear and
K12-rear. Each has seven printed increments. The table gives the largest
sampled individual-bolt lateral force and largest sampled axial tension for
each block across those histories. These maxima can belong to different
bolts; they must not be combined into an invented simultaneous load.

| Current block | Peak lateral force | Controlling bolt and case | Peak axial tension | Largest demand / unadjusted hypothetical lateral reference |
| --- | ---: | --- | ---: | ---: |
| Top outer left | 1,074.79 N | `side_2`, A12-rear, full load | 481.68 N | 1.520 |
| Top outer right | 1,264.69 N | `side_2`, K12-rear, full load | 535.39 N | 1.786 |
| Top center left | 157.97 N | `rail_2`, A12-rear, full load | 194.04 N | 0.217 |
| Top center right | 164.16 N | `rail_2`, K12-rear, full load | 226.68 N | 0.225 |

The last column uses the explicitly unadopted nominal-diameter bearing /
typical-thread-root yield convention below. It is a scouting comparison,
not an adopted design utilization or a joint pass/fail. The alternative
root-diameter bearing convention gives peak ratios 1.570, 1.844, 0.224 and
0.233 in the same block order. The outer `side_2` bolts deserve priority in
the upper resistance evaluation. Smaller center-block bolt actions do not
establish center-joint acceptance.

All four blocks have conditional grain along their recorded source `N`
axis and 88.9 × 88.9 × 119.7 mm envelopes. Rail and center-principal stacks
have 127 mm nominal wood grip and 152.4 mm modeled shafts. Outer-side stacks
have 177.8 mm wood grip and 203.2 mm modeled shafts. These are analysis
envelopes, not purchase lengths, drill instructions or delivered shank.

## Directional geometry findings

The signed lateral action is applied separately to each wood member in its
own current grain frame. The equal-and-opposite force on the second member
is retained. Both outer bounds are recorded, and a loaded boundary is chosen
from that member's signed component rather than an unsigned force magnitude.

The top center principal members have only **27.9 mm** from `principal_2`
to their grain-positive terminal boundary. Current full-load responses point
a grain component toward that boundary in A12-rear and K12-rear on the left,
and in all three cases on the right. For example, K12-rear right
`principal_2` has a +108.97 N grain component and a −1.37 N cross-grain
component on the principal. The pure softwood parallel-tension 7D reference
is 44.45 mm for nominal D = 6.35 mm. Under that specific applicability,
27.9/44.45 = 0.628 is the conditional end-distance geometry-factor comparison.
It exceeds the corresponding 3.5D lower geometry threshold. This is an
applicability/reduction issue to resolve, not an automatic adopted failure.
Oblique loading still requires the applicable NDS shear-area and detailing
interpretation; the script does not apply this factor to resistance.

The common cleat rail rows have a 43.35 mm short grain end, 1.10 mm below
that 7D reference. Signed current actions point a grain component toward the
short end at each outer `rail_1` and each center `rail_2`. Under a pure
parallel-tension interpretation the separate comparison is 0.975. This
current source binding matters: the preserved top-center integration study
described a different rail-row arrangement and its 45.45 mm end result must
not be carried into the reviewed geometry.

No recorded loaded outer-box edge is below the conditional pure
perpendicular 4D = 25.4 mm comparison in these three histories. That says
nothing about oblique-rule applicability, nearer shoulders, intersecting
bores, washer support, splitting, row/group failure or fabrication tolerance.
The box classifier does not inspect those features. Each bolt's signed
grain/cross-grain components and named loaded end/edge are in the report.

## Component assumptions and unresolved strength

The conditional wood lateral calculation reuses the six-mode single-shear
equations and DF-L bearing helper already in the repository. It binds each
current bolt's two bearing lengths and actual unsigned load-to-grain angles;
it does not reuse an old angle sample, equal bolt share or station capacity.
The two bearing conventions remain separate, following the preserved
[thread-root reference method](../wj04-thread-root-lateral-reference.md).
The typical 0.189-in root is an explicit hypothetical section throughout
both bearing regions, not a class tolerance or delivered dimension.
Fyb = 106 ksi is the Grade 5 Commentary estimate, not a normative test-derived
value or guaranteed lower bound. The [conditional property boundary](../evaluation-resume-2026-09-24/ordinary-bolt-resistance-boundary-attempt01/README.md)
continues to govern it.

The wood reference assumes contacting member faces with zero gap. The
whole-frame spring/contact recovery does not establish that NDS applicability
under loaded opening, or a physical bound on bolt distribution. No duration,
moisture, temperature, geometry, group or other end-use adjustment is applied.
The two bolt references in an interface are not added into a capacity.
An above-one scouting ratio flags follow-up under those assumptions; a
below-one ratio establishes no complete-joint pass.

Separate direct-steel references use hypothetical Grade 5 Fy = 92 ksi,
nominal 1/4-20 tensile stress area 0.0318 in² and an assumed circular
0.189-in root shear section. The maximum separate tension and shear ratios
are 0.0411 and 0.1908. They exclude bolt bending, strength adjustments,
thread-strip/nut/head failure and an established co-located axial/shear
interaction. The ideal fully supported washer-annulus wood comparison peaks
at 0.582 using the recorded representative dimensional envelope and
Fc-perpendicular = 625 psi. Washer steel bending/spreading and actual
supported contact are unresolved. None of these component numbers closes
bolt, washer or joint resistance.

## Completed evidence and replay

[freeze.json](freeze.json) pins all three existing model JSONs, input decks,
native DAT files, parent terminal decisions, independent all-body audits,
the accepted response renderings and method/hardware sources by SHA-256.
A1 uses its accepted zero-displacement-token rendering; K12 retains its
case-specific SPR489 direct-master recovery. Neither method correction is
generalized to another case. The producer checks candidate/revision/case,
all seven strict response gates at every increment, source hashes and the
unchanged 92 new / 12 retained / 66 panel-fastener inventories before export.

[upper-joints.json](upper-joints.json) contains 336 individual bolt action
records, 672 signed member-direction records and 84 block equilibrium
reconstructions. Each block reconstruction includes all sixteen incident
connection rows: four lateral planes, four outer-seat tension ties and
eight finite wood-face contact cells. It includes the source discrete
body loads at that increment, including the block's self-weight. Axial
forces use their respective outer-seat points; lateral and contact forces
use their own source points. Opposite endpoints are not double-counted.
Receiver resultants preserve force and moment at the named block datum.

All 84 force/moment reconstructions reproduce the accepted response audits
and satisfy their unchanged 0.1 N / 2 N·mm checks and propagated RF-rounding
interval checks. The maximum raw block residuals are 0.000151 N and
0.004135 N·mm. These verify extraction and equilibrium bookkeeping; they
do not validate the physical stiffness/contact model or establish strength.

[bolt-actions.csv](bolt-actions.csv) is a compact comparison table suitable
for later reporting. Reproduce from repository root:

```sh
OPENBLAS_NUM_THREADS=1 .venv/bin/python docs/wood-joints-mvp/hypotheses/upper-frame-joint-review-2026-09-30/produce.py --verify
```

The verification mode is read-only and requires byte-identical report/CSV
replay. Changed frozen inputs stop it. The independent review and focused
numerical checks are recorded in [verification.md](verification.md).

## Recommended next work

Keep the main worker on the lower BG001/BG003/BG045 assembly and support-case
blockers. Integrate this packet as current upper action evidence, without
promoting any resistance or six-case status. Prioritize the upper outer
`side_2` bolts' applicable lateral/bending/group behavior and the top center
principal terminal-end interpretation. Bind conditional thread extents,
Fyb method, contacting-face applicability, washer/nut transfer and the actual
shared-member cuts to those simultaneous source actions.

The remaining three whole-frame cases and response sensitivities still limit
the upper demand envelope. The shortened upper-right G7 block is a separate
next upper task because its geometry differs from the four common blocks
here. Any proposed geometry change should be reported against the reviewed
model before being made. No candidate selection, fabrication, drilling,
physical inspection, floor qualification or climbing release follows from
this packet.
