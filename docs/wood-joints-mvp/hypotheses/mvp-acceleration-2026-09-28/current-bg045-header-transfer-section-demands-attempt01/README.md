# BG045 header transfer-section actions

This packet recovers conditional signed section resultants in `base_header` on
both sides of the left BG045 bolt station. It uses the same point-force and
moment-transport method as the existing conditional section-demand producer,
with the proposed header grain and member axis along global `+X`.

The three accepted rear exports contain the complete base-header cut inventory
for all seven increments. Every increment has 160 report-side header action
rows, matched one-for-one to 160 native-response rows with identical names,
points, owners, and forces. The 212 source header load nodes cover all 212
physical header nodes. The response has no separate active or inactive floor
tangent action owned by `base_header`; its cut inventory therefore closes with
the matched point forces and load-factor-scaled source-discrete body loads. All
116 timber/panel contact rows and all simultaneous bolt and panel-screw rows
are retained in the side sums. The 10 parametric screw-withdrawal rows also
remain in equilibrium bookkeeping despite their explicitly non-qualifying
resistance role.

The cut is normal to proposed grain `+X` at `x = −1085.85 mm`, through the two
BG045 header bolt axes. Its fixed moment datum is
`(−1085.85, −105.85, 257.95) mm`. The only point forces on that plane are the
two BG045 lateral-plane forces and two outer-seat axial ties; no source header
load node is coincident with the plane. The producer assigns those four
actions to the right free body immediately before the station and to the left
free body immediately after it. For each isolated segment, its material
section action is the negative of the full simultaneous external wrench about
the fixed datum.

At the full-factor-one endpoints, the BG045 plane external wrenches are:

| Case | Force `(Fx, Fy, Fz)` N | Moment `(Mx, My, Mz)` N·mm about the cut datum |
| --- | --- | --- |
| A12 rear | `(-113.287780, -19.796462, 139.224710)` | `(4577.439858, -2158.132209, 2662.250568)` |
| A1 rear | `(-32.624400, 132.814660, 107.967338)` | `(-7023.139044, -621.494820, -3257.311402)` |
| K12 rear | `(-59.144720, -6.129723, 38.096890)` | `(361.167294, -1126.706916, 3966.466012)` |

[`section-demands.json`](section-demands.json) carries the 21 signed body
closures and both one-sided left/right resultants at each accepted increment,
with role counts, plane action identities, rounding intervals, and explicit
cut-jump checks. The maximum absolute global-origin header residual over the
21 states is `(0.000044, 0.000034, 0.000131) N` and
`(0.0142, 0.1624, 0.0389) N·mm`; every component lies inside the corresponding
source rounding interval. Complementary segment actions sum to the negative
full-body residual, and the one-sided jumps equal the plane-coincident wrench
with the appropriate sign. A known force/couple transport oracle and the
independent native-response reconstruction both pass; the independent check
matched 84 one-sided segment wrenches with zero difference.

These are member-scale signed force and moment resultants for the analytical
source-discrete load pattern. They supply a boundary action for a compatible
header transfer analysis. They do not identify local tension-perpendicular
stress or strain around the bolt, washer, bearing/contact edge, or any split
plane. The applicable local transfer field and a topology-compatible splitting
method and resistance remain missing; section resultants alone are not a
splitting demand or capacity comparison. The source-discrete nodal distribution
is not a measured physical gravity distribution.

The packet does not change geometry or axes, run a native solve, calculate
resistance, or accept the joint. Reproduce with:

```sh
python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-bg045-header-transfer-section-demands-attempt01/produce.py --verify
python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-bg045-header-transfer-section-demands-attempt01/parent_verify.py
```

[`source-pins.json`](source-pins.json) records the authenticated demand report,
model, native response, and parent acceptance evidence hashes for all three
cases. [`parent-verification.json`](parent-verification.json) contains the
independent reconstruction hashes and check counts.
