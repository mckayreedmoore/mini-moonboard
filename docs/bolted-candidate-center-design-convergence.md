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

Next, model **one** left center principal–header–post connection with the actual shared
bolt/angle/contact topology and explicit provisional slip/contact parameters. Compare its
same-case actions with the reference packet, complete its applicable wood/bolt/steel and
geometry checks, then decide whether this factory connector is viable. Do not replicate it
to all 24 stations or issue machining coordinates before that representative result exists.
