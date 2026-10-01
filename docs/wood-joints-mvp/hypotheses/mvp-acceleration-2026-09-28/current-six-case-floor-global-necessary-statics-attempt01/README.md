# Six-case floor global necessary-statics screen — attempt 01

This packet asks one narrow question: can a nonnegative set of vertical floor-normal reactions on the pinned support footprint match the source load's total vertical force and its overturning moments about global X and Y? It is a solver-independent necessary screen for gross global overturning. It does not evaluate a local contact state or accept a load case.

## Source and geometry

The inputs are the six-case load-only register and the validated gravity/climber source decomposition. Each combined wrench is independently summed from the 50 source physical-body force and first-moment rows in its case model, then checked against (1) the source model's complete physical nodal load map and node coordinates, (2) the case assembly audit, and (3) the validated gravity-plus-climber decomposition. Moments are about the source model's global origin `[0, 0, 0] mm`; source axes are global X/Y horizontal and +Z upward. The load register and the six input models explicitly state that no native solve or rejected response forces are used. No response force or contact mask is consumed here.

Before computing a CoP, the replay checks the floor geometry in every case model. It finds 100 uniquely named physical `floor_normal` contact owners, 100 matching unilateral normal bindings, and 100 unique support nodes. The support-node coordinates exactly match the physical owner points. All 100 points have global `Z = 0 mm`, and all 100 physical and carrier normals are exactly `[0, 0, +1]`. The full point, normal, area, and source patch-index inventory is included in [screen.json](screen.json). The 100-point support geometry is identical across the six load-only models. Its plan-view convex hull has eight vertices.

The independent input pins are in [source-pins.json](source-pins.json); the manifest SHA-256 is `c2a99b84a2e98dbd69d1819e6193b56e81a70b1bcaee447be6be71f291d892bb`. It pins the load register, validated decomposition and verifier, upstream source inventory, and all six load-only models and their audits. The decomposition is bound to register SHA-256 `7a638a49fc5086b4d5fed52148286a300b8b271f7d380b1a131ea8e17b094508` and upstream pin-manifest SHA-256 `80c8c8c2159bfe98669a2c65e269ffe8bbf4211f43a1b609e630f74ca62c2c24`.

## Method and result

For external global-origin wrench `F = (Fx, Fy, Fz)` and `M = (Mx, My, Mz)`, upward normal reactions on the flat `Z = 0` plane have resultant `N = -Fz`. Their support moment is `[Σ(yi Ni), -Σ(xi Ni), 0]`, so matching the external X/Y overturning moments requires

```text
CoP = (My / N, -Mx / N)
```

Every nonnegative normal-reaction distribution has its CoP in the convex hull of its application points. Thus a CoP outside this hull would rule out normal-only vertical/overturning balance on the pinned footprint. A CoP inside only passes this global necessary condition. The replay uses a pure-Python monotone-chain convex hull and runs a rectangular-footprint oracle for known inside, boundary, and outside points before classifying the source cases. It uses no LP solver.

| Source case | `F = (Fx, Fy, Fz)` N | `M0 = (Mx, My, Mz)` N·mm | Required CoP `(x, y)` mm | Minimum signed hull-edge distance mm | Result |
|---|---:|---:|---:|---:|---|
| A12 rear | `(0, 300, -4424.926817)` | `(-5578985.457, -2270433.059, -305760.000)` | `(-513.101, 1260.809)` | `343.169` | Inside |
| A12 forward | `(0, -300, -4424.926817)` | `(-4385485.379, -2270433.059, 305760.000)` | `(-513.101, 991.087)` | `612.891` | Inside |
| A12 left | `(-300, 0, -4424.926817)` | `(-4982235.418, -2867183.098, 464866.130)` | `(-647.962, 1125.948)` | `478.030` | Inside |
| K12 right | `(300, 0, -4424.926817)` | `(-4982235.418, 2774538.596, -464866.130)` | `(627.025, 1125.948)` | `478.030` | Inside |
| K12 rear | `(0, 300, -4424.926817)` | `(-5578985.457, 2177788.556, 294240.000)` | `(492.164, 1260.809)` | `343.169` | Inside |
| A1 rear | `(0, 300, -4424.926817)` | `(-1895019.327, -2270433.059, -305760.000)` | `(-513.101, 428.260)` | `569.035` | Inside |

The smallest signed margin is 343.169 mm, for A12 rear and K12 rear. For every case the normal resultant closes `Fz` and the reaction moment computed at the CoP closes `Mx` and `My` to floating-point roundoff. The remaining `Fx`, `Fy`, and `Mz` values are recorded in `screen.json`; normal reactions cannot balance them. They require separate tangential/yaw treatment, and this packet does not qualify floor friction or tangential capacity.

The body-sum to complete source nodal-map closure is at most `1.82e-11 N` in force and `1.49e-8 N·mm` in first moment over the six cases. Body sums also close against the load-only case audit and the validated gravity/climber totals within the replay's `1e-8 N` and `1e-6 N·mm` roundoff guards. These guards are source arithmetic checks, not engineering acceptance tolerances. The rectangular oracle passes all three classifications.

Therefore these source loads show no global normal-resultant overturning obstruction on the pinned flat footprint. That finding cannot distinguish local contact/history bookkeeping from a locally incompatible frame response: inside-hull CoPs do not prove displacement compatibility, a valid active/open state, contact-law consistency, force transfer at joints, or actual floor support. The minimum remaining local gate is a source-compatible frame equilibrium state with the 100 unilateral floor-normal gaps/reactions mutually consistent with their contact law and load path. Tangential equilibrium remains separate and unqualified.

## Reproduction and limits

From the repository root:

```sh
python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-six-case-floor-global-necessary-statics-attempt01/replay.py --verify
```

The verifier checks every direct source hash, reassembles the six combined wrenches, confirms all 100 floor points/normals and the rectangle oracle, recomputes all CoPs and hull distances, then byte-compares the report with [screen.json](screen.json). To intentionally regenerate the report after changing a source pin, use `--write` and update the packet pins and findings together.

This is not a contact/displacement compatibility solution, friction or tangential-capacity check, actual floor verification, anchorage analysis, timber/joint/hardware strength screen, structural acceptance, physical-failure finding, or climber rating. No native solve, geometry/model change, floor experiment, support mask, or rejected response force is used.
