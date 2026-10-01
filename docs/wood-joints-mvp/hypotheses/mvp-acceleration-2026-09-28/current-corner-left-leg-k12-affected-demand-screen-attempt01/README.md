# K12 left LEG affected-demand screen

This packet applies the existing original LEG per-bolt methods to the seven
fresh, source-bound K12 states for only `lumber_leg_bolt_left_1` and
`lumber_leg_bolt_left_2`. The K12 forces come from the authenticated
`current-corner-k12-rear-case-bound-export-attempt01` report; the A12 values
are same-load-factor force comparators from the original onward-action
register. No A12 response, ratio, resistance, or case status is transferred.

At the full load factor, the signed axial tie forces on `base_side_left` are
`[-241.9659, 0, 0] N` and `[-530.5748, 0, 0] N`; positive axial tension is
defined along the original `[-1, 0, 0]` bolt axis. The corresponding A12
values were `[-262.7068, 0, 0] N` and `[-529.4394, 0, 0] N`. Thus bolt 1
changes by `-20.7409 ± 0.0001 N` (`-7.8951%`) and bolt 2 by
`+1.1354 ± 0.0001 N` (`+0.21445%`). These bounds are sums of the source
printed-token rounding radii for the K12 and A12 rows; they are not engineering
uncertainty bounds.

The corresponding full-factor lateral-plane forces on `base_side_left` are
`[0, -23.39143, 298.0269] N` and `[0, -143.7603, 334.2164] N`. The same-factor
A12 vectors were `[0, 103.9978, 1178.753] N` and
`[0, -790.4834, 1531.061] N`. K12 resultant demands are `298.94346 N` and
`363.82362 N`; the same-factor A12 resultants were `1183.33181 N` and
`1723.08206 N`. Exact seven-state vectors, row IDs, source rounding radii,
per-state deltas, and action-reaction pairs are recorded in
[`affected-demand-screen.json`](affected-demand-screen.json).

The unchanged original single-bolt lateral method uses the recorded fixed
`Ktheta = 1.25`. At the governing full-factor state, its original lateral
references and demand/reference ratios are `3289.3274 N / 0.0908829` for bolt
1 and `3025.0875 N / 0.1202688` for bolt 2. The maximum provisional-hardware
component ratios are:

| Original axis | Lateral reference ratio | Direct steel interaction | Washer wood bearing | Washer elastic bending |
| --- | ---: | ---: | ---: | ---: |
| `lumber_leg_bolt_left_1` | 0.090883 | 0.021284 | 0.072028 | 0.169227 |
| `lumber_leg_bolt_left_2` | 0.120269 | 0.030034 | 0.157941 | 0.371076 |

These are individual-component screens using the original reviewed method and
provisional Grade 5/washer assumptions. They do not establish joint capacity,
net-section/group tear-out/splitting resistance, actual hardware conformance,
or design acceptance. The original method's nominal-diameter bearing check
also remains conditional on the existing partial-thread criterion in the
source record.

The baseline evidence map confirms the two named bolt axes, receiver pair,
station and hardware schedule remain the original retained arrangement. It
also records ten new candidate bores in `base_side_left`, with none added in
`lumber_leg_left`. Their local net-section, group tear-out/splitting and
remaining-section effects are unresolved for the changed receiver geometry;
the legacy external stock-edge screen does not include these bore interactions.
No other ten original LEG/FLOOR-RUNNER arrangements are reopened here, and the
92 new candidate axes remain separate from the twelve retained arrangements.

`produce.py --verify` reproduces the output from its SHA-pinned inputs. The
producer does not launch a solver.
