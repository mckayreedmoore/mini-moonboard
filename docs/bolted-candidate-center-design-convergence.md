# Center connection: numerical reference and concept decision

Status: diagnostic design work only, **not** a bolt demand, joint rating, or drilling release.
The physical build is kerf-right, the lumber is uncut and undrilled, and all 66 panel/kicker
screw axes and the existing twelve frame-bolt arrangements remain protected. No custom steel
or manufacturer inquiry is authorized. The full source-bound case record is
[center-reference-diagnostic.json](bolted-candidate-prototypes/center-reference-diagnostic.json).

## What the numerical model actually represents

The current kerf-right frame was prepared with its six narrowed panel meshes checked against
the actual panel solids. The native diagnostic deliberately retains the *old* ML24Z/SDS
connector arrangement and its assumed stiffness. It therefore shows how that reference load
path distributes force between timber contact and clips; it does **not** predict loads in
the proposed ABB AB205 bolts. The existing six 250-lb load definitions were unchanged.

Five default cases converged with global and member equilibrium: `a12-rear`, `a12-left`,
`k12-right`, `k12-rear`, and `a1-rear`. `a12-forward` did **not** converge its unilateral
contact state under the default search, two alternate update schedules, a same-model accepted
seed, or the tested lower/higher face-contact penalties. Its intermediate forces are excluded.
This is a numerical-model failure for that case, not a physical hardware verdict. The packet
retains exact case settings, source/report/input digests, signed same-case wrenches, and local
residuals. The full raw solver directories remain local, separate from candidate acceptance.

The largest observed left-center vertical interface actions among the five accepted default
cases occur in `a1-rear`. The signs below are force **on the named timber**, at each recorded
angle origin; moments are about those same origins. `Direct` is the modeled timber-contact
contribution and `clip` is the old ML24Z/SDS path, not an AB205 bolt force.

| A1-rear, default proxy | Total force XYZ (N) | Total moment XYZ (N·mm) | Direct Fz (N) | Clip Fz (N) |
|---|---:|---:|---:|---:|
| Left principal/header | (70.8, 93.4, 623.3) | (48,830, −5,806, −406) | +561.4 | +62.0 |
| Left post/header | (46.0, −69.1, −645.3) | (−30,470, 7,439, 608) | −599.8 | −45.5 |

Both a softer (`0.1×`) and a stiffer (`10×`) setting of the proxy's panel/SDS
connection-spring analogies converged for this same A1-rear case; the explicit retained
frame-bolt stiffness was not scaled. Across those *tested settings*, the left post's total
Fz changed from −734.1 to −594.7 N, and the left principal's total Mx changed from
+46,398 to +60,656 N·mm. Those are sensitivity points, **not** bounds for a different
bolted topology. Contact opening, fastener clearance, flange flexure, and bolt-group coupling
may redistribute loads again.

## First actual-topology diagnostic (one load case only)

A separate *provisional* model replaces only the two left-center old clips with two
nominal rigid AB205 angle bodies and two shared through-header bolt bodies. Each header
bolt has two distributed lateral-only wood-bore springs and free bending tilts; each
angle has four sampled compression-only contacts against the header. The remaining
stations retain the old ML24Z/SDS proxy. Existing twelve frame bolts and all 66
panel/kicker screws remain. The old two clips and screws still contribute surrogate
gravity mass; the new steel/bolt masses are not substituted. Angle flexure, hole
clearance, nonlinear bore pressure, washers, preload, prying, and resistance are not
resolved. Thus even a converged result is **not a qualified bolt demand**.

For `a1-rear` only, the native contact set, global/member equilibrium and MPC checks
passed at three explicitly assumed uniform connection/contact stiffnesses. Values are
forces on named wood members or, in the last column, force from the upper steel flange
on shared bolt 0. Each row is one simultaneous solve, not an independent peak envelope.

| Assumed joint spring (N/mm) | Principal total Fz / via angle (N) | Post total Fz / via angle (N) | Bolt 0 upper-flange force on bolt XYZ (N) |
|---:|---:|---:|---:|
| 1,000 | +548.6 / +32.2 | −573.8 / −31.3 | (−35.2, −49.2, +5.6) |
| 10,000 | +602.0 / +54.2 | −635.4 / −136.4 | (−49.4, −128.9, +29.6) |
| 100,000 | +634.5 / +38.3 | −681.9 / −219.2 | (−56.9, −172.7, +161.4) |

At 10,000 N/mm, the principal/header total at the legacy station origin is
`F=(98.0, 72.9, 602.0) N`, `M=(48,279, −2,622, −2,894) N·mm`; direct timber
contact supplies +547.8 N of its Fz. The post/header total is
`F=(70.5, −16.0, −635.4) N`, `M=(−31,091, 2,249, −738) N·mm`; direct contact
supplies −499.0 N of its Fz. The two outside actions on each shared bolt are
unequal in this solve, so the symmetric double-shear shortcut is not established.
Stiffness variation materially changes bolt sharing; these three points are not
physical stiffness bounds or a capacity envelope.

The original three runs used one **historical common-scale diagnostic** knob:
vertical wood/bolt axial and lateral, steel-flange/bolt axial and lateral, each
of two header-bore point springs, and each flange contact all received the
listed value. The [runner](../scripts/bolted_center_native_diagnostic.py) now
accepts those consequential mechanisms independently. Its header-bore input
is the **total** lateral stiffness per shared bolt, split equally between the
two point springs; the historical 10,000 N/mm per-point case therefore means
20,000 N/mm total. These are specified diagnostic inputs, not measured
stiffnesses or clearances. No new independent-parameter native result is
claimed here, and no few-point sensitivity is an uncertainty envelope.

The [grain-direction classifier](../scripts/bolted_center_load_classification.py)
uses the authenticated final input's actual member axes, not a guessed vertical
grain. At the principal bolt closest to the oblique end, its lateral action on
wood has parallel/perpendicular magnitudes of `+37.4/22.4`, `+93.2/85.4`, and
`+149.1/160.0 N` at 1,000/10,000/100,000 N/mm, respectively. The parallel
component is signed along the member's upward grain axis; the perpendicular
number is a magnitude. One near-hole branch and three header-bore branches
switch which component dominates across these assumed settings. The farther
principal bolt's parallel component changes sign (`+5.1`, `−4.8`, `−57.0 N`).
These observations do **not** select a favorable NDS end/edge loading category:
the actions are oblique, other load cases are unresolved, and the actual steel
and contact stiffnesses are not established.

The [source-bound extractor](../scripts/bolted_center_candidate_extract.py) validates
the final input, all artifact/source hashes, solver acceptance, exact case and branch
equilibrium before returning same-case actions. Local raw native directories are kept
outside Git; the following SHA-256 pairs identify the accepted report and final-cycle
input, respectively:

- 1,000 N/mm: `ceda84155adfe90aabbc91c30ff6b05e3eb52f9263d00202db6afb6888db62b4` /
  `2a2940f4bd7b8e0245971ed2ea6fadba10517d16b5f31e64d8e4f36128120eb5`.
- 10,000 N/mm: `85f7ac80a4d0c65d4c2b8d8ee3f26e10a42dd57ca3d5c02a5ca12af040d1a63d` /
  `7b39dacae4368c99dda6fb4eee877507e24f90e90b059534724a4369d2ab8c0c`.
- 100,000 N/mm: `be494b9405ecd68bb6de0efa992b45287b740a2877e84754a8edf723443828fe` /
  `799b532a8fa730369b6d83fcae2f580b8c2f1287a660f6046f2ce3fb6f3eea00`.

The [small replayable A1-rear 10k evidence bundle](bolted-candidate-prototypes/center-evidence-bundle.md)
contains the original report, the final input, scoped parameters, authenticated
source snapshots and the extracted actions; it does not rerun the native solve.

A separate bounded `a12-forward` run at 10,000 N/mm stopped after 17 cycles:
`Contact active set repeated without convergence`. Its global/member equilibrium
checks passed for the intermediate cycles, but the contact acceptance gate did
not; **none of its forces are used**. The local report SHA-256 is
`a0cdeab984c7860fa10a58502062dbe6046908c9b8b03be909f683b97df8043b`.
No alternate contact schedule is being tuned here to turn that failure into a pass.

The compact failure diagnosis is an **algorithmic active-set cycle**, not an
established physical instability. Cycle 16 was solved, but its contact update
would return to the active set of cycle 11, so cycle 17 was not solved. Late
active-contact counts for cycles 11–16 were `136, 139, 140, 133, 140, 137`;
none passed the unilateral check. In cycles 14/15/16, lower-left AB205 flange
contact 0 switched on/off/on, as did a left floor/leg contact, while a neighboring
left floor/leg contact switched off/on/off. Cycle 16 still had ten unilateral
violations (five active, five inactive). Global/member equilibrium and MPC passed
for that trial state, but contact convergence and numerical acceptance failed;
there is no qualified `a12-forward` force. The local final trial report and input
SHA-256 values are `fc5c8469ae0f6e4f66710936e194d784f6826f703603e452eaed1204fd2758f9`
and `236515d6affac92543bcda530f878e1f13ed80e5ac83bbbcac1488ed8a98b8ba`.

Next: establish defensible connection slip/contact assumptions, complete the other
unchanged load cases, and check the same joint's wood/bolt/formed-steel resistance
and installed fit before any station replication or drilling decision.

## Representative connection decision

**Set aside the fixed flush-bend AB205 center pose from the next qualification
target.** Its short-vertical orientation fails the explicitly conservative
3.5D *grain-ray search filter* by 17.510 mm of ray (13.413 mm of vertical
factory-hole offset); its long-vertical orientation leaves only 0.148 mm of
conditional 4D row-position window before tolerances. Neither result is a
formal NDS oblique-end or complete-joint verdict. The fitting also lacks a
published guaranteed steel strength and applicable wood-joint resistance.
The existing diagnostic actions remain useful for understanding the shared
steel–wood–steel topology, but more native runs on this unchanged fitting pose
would not close those decisive gaps.

The next factory-made angle lead needs a documented near-hole offset of at
least 34.051 mm *for this conservative proxy*, a tolerable two-hole row within
the actual principal and header, product-specific steel and formed-angle
inputs, and complete installed stack/access checks. This is a search filter,
not a requested custom hole pattern or drilling dimension. If a different
factory fitting meets those inputs, its shared through-header bolt must be
checked as one unequal-side-action three-member stack. Timber-to-timber
bearing remains a separate compression-only path. All frozen panel screw axes
and twelve original frame-bolt arrangements stay protected.

Do not advance the distinct-row stagger as the default answer. Its maximum nominal row
separation is 29.518 mm; the conditional perpendicular-loading minimum in the current
geometry screen is 39.688 mm. That is a 10.170 mm shortfall even before tolerances. The
parallel-only interval does not justify it while reversible local loading is unresolved.
The alternative paired straight-strap idea was also rejected because it did not positively
connect the header. This keeps the concept set bounded rather than restarting catalog search.

The AB205 shared concept has **not** passed G1. Its top row has only 4.887 mm nominal reserve to
either side of the conditional reversible 4D band, and the principal's nearest grain-parallel
ray reaches its oblique end after 26.940 mm; neither is a verified installed end/edge margin.
The alternate long-vertical AB205 orientation has only a 0.148294 mm total nominal
two-edge 4D row band. The [row-allowance screen](../scripts/bolted_candidate_ab205_center_fit.py)
shows that any symmetric lateral row-position allowance above 0.074147 mm closes that
*conditional* band. This is a geometric threshold, not a chosen product/shop tolerance or
a declaration that both edges govern every load case. For the short-vertical orientation,
an illustrative 1 mm lumped lateral allowance still leaves 7.773898 mm in that band,
but does not resolve its oblique end cut or qualify the joint.
The [oblique-end pattern filter](../scripts/bolted_candidate_ab205_center_fit.py)
also makes the smallest nominal factory-pattern change explicit. The [2024 NDS
bolt end-distance definition](https://awc.org/wp-content/uploads/2026/08/AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-%E2%80%93-Dowel-type-fasteners.pdf)
addresses a square-cut end, so the actual oblique-cut 26.940 mm grain ray is
**not** an NDS end-distance verdict. If the 3.5D reduced-value softwood tension
threshold is imposed as a conservative *ray-only search filter*, this fixed
flush-bend geometry needs a nearest vertical factory hole at least 34.051 mm
(1.341 in) above the bend. AB205's short-vertical near hole is 20.638 mm,
13.413 mm short of that filter. Its long-vertical near hole clears the ray
filter, but the competing two-edge row band is only 0.148 mm wide. This
identifies a needed factory-hole-pattern change; it does not classify the cut,
check splitting or load direction, or authorize moving the bend off its bearing
surface to manufacture the offset.
The separate [nominal washer screen](bolted-candidate-prototypes/center-washer-envelope.json)
uses a Lowe's-listed 1/2-inch washer with a 34.925 mm outside diameter and
3.175 mm listed thickness. On the two shared-header axes its ideal cylindrical
envelopes leave 12.7 mm between washers and 3.175 mm to each nominal angle
side; they intersect no raw wood or retained panel/frame-bolt axis. The wood
plus two nominal steel flanges is 50.8 mm thick, or 57.15 mm with one such
washer outside each flange. This closes only that illustrative washer-envelope
question. It does not establish washer strength, exact bolt grip/thread exposure,
nut/head/tool access, delivered tolerances, or panel seating.
The AB205 material and formed-bend resistance, unequal two-flange bolt action, group/wood
failure modes, bolt-axis action, real grip, and disassembly access still need a supported
calculation or an exact concept change. A single DF-L bearing stress or bolt-shaft rating is
not a joint capacity. Use the [2024 NDS/Supplement](https://awc.org/resources/2024-nds-supplement/)
consistently for the next wood-joint calculation; keep steel/formed-angle resistance separate.

The first left-center shared-bolt model above is a diagnostic topology, not an installed
detail. A different factory fitting would need its own geometry, slip/contact
inputs, same-case native actions and applicable wood/bolt/formed-steel checks.
Do not replicate AB205 to all 24 stations or issue machining coordinates.
