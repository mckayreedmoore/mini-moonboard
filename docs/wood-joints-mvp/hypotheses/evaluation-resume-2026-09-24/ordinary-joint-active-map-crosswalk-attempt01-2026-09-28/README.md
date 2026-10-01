# Ordinary-joint active-map crosswalk, attempt01

## Status and scope

This append-only packet binds the frozen A09 `n_plus` static input to the
four source-bound fitted nut-axis maps present in its include chain. It also
expresses the A09 port motion and the only qualified A00 fixture in the same
local/global coordinate basis. The machine-readable record is
[`crosswalk.json`](crosswalk.json); exact source pins are in
[`SOURCE-SHA256SUMS`](SOURCE-SHA256SUMS), and the packet-file hashes are in
[`SHA256SUMS`](SHA256SUMS).

The crosswalk establishes input composition, map identity, coordinate
transforms, and the scope difference between the two frozen inputs. It does
not establish a current-joint response, dynamic history, map equivalence,
force transfer, capacity, criterion disposition, or release. No source input,
geometry, task queue, run ledger, plan, or criteria file was changed. No
solver was run.

## A09 deck and active input maps

The frozen [`port_motion_n_plus.inp`](../ordinary-port-motion-attempt09-common-map/port_motion_n_plus.inp)
includes both `nut-coupling.inp` and `rigid-carriers.inp`. The source-bound
axis inventory in
[`current-map-remaining-scope-attempt01`](../current-map-remaining-scope-attempt01/decision.md)
joins the four ordered `per_nut` rows to these physical axes and carrier sets:
The `n_plus` case lock binds its exact deck digest to the external-port bundle
lock; the bundle lock binds the base input-freeze digest. This replay also
rechecked all 14 artifacts in that base freeze against their recorded hashes.

| Map | Joint axis | Shaft body | Nut carrier | Head-to-nut direction in global XYZ | Direction in local X/T/N | Fit support |
| --- | --- | --- | --- | --- | --- | --- |
| A00 | rail 1 | `M00_A00_BOLT_HEAD_PLUS_SHAFT_UNION` | `M03_A00_NUT` | approximately `(0, −0.642788, −0.766044)` | approximately `(0, +0.173648, −0.984808)` | 251 nodes; 754 terms per equation |
| A01 | rail 2 | `M04_A01_BOLT_HEAD_PLUS_SHAFT_UNION` | `M07_A01_NUT` | `(0, −0.642788, −0.766044)` | approximately `(0, +0.173648, −0.984808)` | 258 nodes; 775 terms per equation |
| A02 | principal 1 | `M08_A02_BOLT_HEAD_PLUS_SHAFT_UNION` | `M11_A02_NUT` | approximately `(−1, 0, 0)` | approximately `(−1, 0, 0)` | 254 nodes; 763 terms per equation |
| A03 | principal 2 | `M12_A03_BOLT_HEAD_PLUS_SHAFT_UNION` | `M15_A03_NUT` | approximately `(−1, 0, 0)` | approximately `(−1, 0, 0)` | 259 nodes; 778 terms per equation |

The frozen carrier include has one matching `*RIGID BODY` card for each
carrier. The source map audit reports rank six and rigid-field reproduction
for each map, while the supports, equation rows, pivots, and dependent DOFs
differ. It reports no exact transformed coefficient equivalence. These are
four input-bound maps; similar axes or rigid-field checks do not transfer the
A00 fixture result to A01–A03.

## Coordinate transform and `n_plus` history

The source frame origin is `(106.79565359345115, 23.277700668948203,
462.86318625581265) mm`. Its columns, expressed globally, are

```text
X = (1, 0, 0)
T = (0, c, −s)
N = (0, s,  c)
c = 0.6427876096867989
s = 0.7660444431187603
```

Thus the global-from-local matrix and its inverse are

```text
B  = [[1, 0,  0], [0, c,  s], [0, −s, c]]
Bᵀ = [[1, 0,  0], [0, c, −s], [0,  s, c]]
v_global = B v_local
v_local  = Bᵀ v_global
```

For six-component coordinates ordered as
`[u_X, u_T, u_N, theta_X, theta_T, theta_N]`, the same orthonormal basis acts
on translations and infinitesimal rotation vectors:
`q_global = diag(B,B) q_local`. Translation components are millimetres and
rotation components are radians. At a remote port, the source also includes
the rigid offset `u_port = u_joint + theta_global × (r_port − r_joint)`;
the frozen `n_plus` rotation is zero, so this offset term contributes zero
for this path.

The frozen target is local relative translation `[0, 0, +1] mm` with zero
rotation. Applying `B` gives global relative translation
`[0, +0.7660444431, +0.6427876097] mm`. The deck controls the rail port at
local N `+0.5 mm` and the principal port at local N `−0.5 mm`, so rail minus
principal is the specified `+1 mm` local N displacement. The input uses a
linear amplitude from static step pseudo-time 0 to 1; this is not a physical
transient duration. The twelve boundary scalars in the deck match the port
control values in `port-motion_n_plus.json`.

The global shaft-axis directions transform with `Bᵀ` as listed above. In
particular, the rail bolt direction has local components about
`(0, 0.173648, −0.984808)`, while the principal bolt directions are about
`(−1, 0, 0)`. These are direction cosines only; they do not describe bolt
elongation, displacement, demand, or force.

## Comparison with the qualified A00 fixture

The completed
[`implicit-current-map-known-answer-attempt01` fixture](../implicit-current-map-known-answer-attempt01/RESULTS.md)
passes three cases—direct, mapped without carrier, and mapped with carrier—
with ten accepted states per case. It tests `M00_A00` and, in the carrier
case, `M03_A00`. Its prescribed forcing is a small global-Y angular
acceleration `alpha_y(t) = 1.2 t rad/s²`, applied through the recorded
rotational body-force field. In the X/T/N basis, the global Y rotation axis is
`(0, 0.6427876097, 0.7660444431)`; the local angular-acceleration coefficient
is approximately `(0, 0.7713451316, 0.9192533317) t rad/s²`.

That fixture is rotational and dynamic. A09 `n_plus` is a translational,
displacement-controlled static input. Their coordinates can be transformed
to one basis, but their imposed DOFs, time histories, and response questions
differ. The A00 result therefore does not qualify this `n_plus` path or any
of A01–A03.

## Run outcome and remaining gates

The A09 run record reports a 900-second wall-clock timeout (exit 137) with
frozen inputs unchanged. Its attempt report records deck assembly followed by
33 Newton iterations in the first `0.001 mm` increment, with no accepted
increment. The `.dat` and `.sta` files are empty; the `.frd` file is only
80 bytes. The run did not reach the nominal centered CAD radial bolt-to-wood
gap of `0.575 mm`. Preserve this failed static attempt; it is not a physical
joint failure or a response result.

The follow-on physical-mass N+ transient remains **unselected and unfrozen**.
The attempt09 note mentions about `1.3 mm` relative N travel only as a
possible nominal geometry target for a future bounded observation. It is not
a selected time history, service demand, or conservative physical bound.

The current-map audit qualifies only A00 in its small one-axis fixture and
does not establish exact coefficient equivalence for A01–A03. T02's
instrumentation production build and capture coupon remain outstanding; T03
attempt07 is an unrun small static shared-slave penalty coupon, not the full
ordinary joint. This packet closes **no T02 or T03 mechanics or acceptance
gate**. It does not supply the accepted ordinary-joint response, equilibrium,
contact transfer, engagement, sensitivities, or demand/capacity evidence.

## Offline replay and integrity

The source-binding and transform replay uses Python's standard library only.
It checks the frozen include chain, four axis-index joins, matching carrier
cards and shaft sections, twelve deck boundary values against the port
manifest, orthogonality and handedness of `B`, local/global translations and
map directions, the A00 fixture pins, and the no-accepted-increment output
record. The replay passed. It ran no solver or geometry operation and does
not evaluate mechanical behavior.

`SOURCE-SHA256SUMS` pins the inspected inputs. `SHA256SUMS` pins the three
packet artifacts and can be checked from this directory with
`sha256sum -c SHA256SUMS`; source pins can be checked from the repository root
with `sha256sum -c <packet-path>/SOURCE-SHA256SUMS`.
