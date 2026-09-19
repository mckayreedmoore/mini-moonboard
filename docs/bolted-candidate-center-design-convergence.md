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

Next: establish defensible connection slip/contact assumptions, complete the other
unchanged load cases, and check the same joint's wood/bolt/formed-steel resistance
and installed fit before any station replication or drilling decision.

## Representative connection decision

Retain the **shared-header AB205 arrangement solely as the next representative calculation
concept**, not as a selected build detail. It has two through-header bolt axes shared by the
upper and underside factory angles; the force on each single steel–wood–steel stack must be
resolved as a whole. Timber-to-timber bearing is a separate compression path, not a tension
or reversal path. The nominal protected-screw screen finds space around four left-center
screw paths, but real shaft/head/washer/tool envelopes and tolerances remain unverified.

Do not advance the distinct-row stagger as the default answer. Its maximum nominal row
separation is 29.518 mm; the conditional perpendicular-loading minimum in the current
geometry screen is 39.688 mm. That is a 10.170 mm shortfall even before tolerances. The
parallel-only interval does not justify it while reversible local loading is unresolved.
The alternative paired straight-strap idea was also rejected because it did not positively
connect the header. This keeps the concept set bounded rather than restarting catalog search.

The shared concept has **not** passed G1. Its top row has only 4.887 mm nominal reserve to
either side of the conditional reversible 4D band, and the principal's nearest grain-parallel
ray reaches its oblique end after 26.940 mm; neither is a verified installed end/edge margin.
The AB205 material and formed-bend resistance, unequal two-flange bolt action, group/wood
failure modes, bolt-axis action, real grip, and disassembly access still need a supported
calculation or an exact concept change. A single DF-L bearing stress or bolt-shaft rating is
not a joint capacity. Use the [2024 NDS/Supplement](https://awc.org/resources/2024-nds-supplement/)
consistently for the next wood-joint calculation; keep steel/formed-angle resistance separate.

The first left-center shared-bolt model above is a diagnostic topology, not an installed
detail. Its slip/contact and local bearing idealizations still need support; then compare
all unchanged same-case actions with the reference packet and complete applicable
wood/bolt/formed-steel and geometry checks. Do not replicate it to all 24 stations or
issue machining coordinates before the representative connection is viable.
