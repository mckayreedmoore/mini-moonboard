# Current BG001 conditional bolt screen

**Result: bounded, conditional individual-bolt lateral references and a signed
equal-stiffness demand map for current BG001. Mechanical acceptance remains
false.** This screen does not assign a frame force or establish a group
capacity.

BG001 is the current two-bolt geometry for `base_post_outer_left` and
`knee_outer_left_spine`, using `knee_outer_left_post_1` and
`knee_outer_left_post_2`. The source inventory gives 6.35 mm modeled shafts,
42.05 mm center pitch along proposed grain Z, and 38.1 mm (1.5 in) modeled
receiver intervals in each member. Bolt axes are global X, perpendicular to
both proposed Z grain axes. The group centroid used for the demand map is
global `(-1208.151, -137.600, 192.475) mm`. Receiver order and delivered stock
remain unverified.

## Conditional individual-bolt scenarios

The source-pinned calculation reuses `calculate()` from the reviewed NDS screen
and the `fea/dowel_yield.py` TR12 single-shear helper. For both members it uses
the modeled 38.1 mm bearing length, 0 gap, assumed full-body 1/4 in shank,
45,000 psi bolt bending yield strength, and a conditional wood scenario of
specific gravity 0.50 with explicit rounded `Fe` assumptions of 5,600 psi
parallel to grain and 4,450 psi perpendicular to grain. These are assumptions;
the actual wood and delivered bolt have not been observed.

| Lateral load direction | `Fe` in both members | Governing NDS/TR12 mode | Individual-bolt reference |
|---|---:|---|---:|
| Global Y, perpendicular to proposed grain | 4,450 psi | IV | 127.657 lbf = **567.848 N** |
| Global Z, parallel to proposed grain | 5,600 psi | IV | 179.007 lbf = **796.262 N** |

Each value is the minimum of the six single-shear yield modes, before joint,
geometry, service, or other adjustments. It is not an adjusted resistance and
cannot be multiplied by two to claim group capacity. The two receiver lengths
and `Fe` values are symmetric, so the unresolved main/side order does not
change these scenario values. These axis-aligned scenarios do not define a
combined Y/Z interaction.

## Equal-stiffness demand map

Let signed `V_y` and `V_z` be in N and `M_x` in N·mm at the group centroid;
positive moments follow the right-hand rule about global X. Bolt 1 is the
lower-Z axis and bolt 2 the higher-Z axis. Under the stated equal-lateral-
stiffness rigid-group assumption:

```text
bolt 1: F_y = V_y/2 + M_x/p       F_z = V_z/2
bolt 2: F_y = V_y/2 - M_x/p       F_z = V_z/2
p = 42.05 mm
```

Thus each bolt receives 0.5 N of `F_y` per 1 N `V_y`, and 0.5 N of `F_z` per
1 N `V_z`. A positive `M_x = 1 N·m` adds `+23.781 N` to bolt 1 `F_y` and
`-23.781 N` to bolt 2 `F_y`. The generated packet independently checks that
the assigned bolt forces recover `V_y`, `V_z`, and `M_x` for pure torsion and
two mixed signed examples.

For an individual bolt, the two direction-specific reference ratios are
`|F_y| / 567.848 N` and `|F_z| / 796.262 N`. Their sensitivity coefficients
are 0.00088052 per N `V_y` and 0.0418795 per N·m `M_x` for the Y component,
and 0.000627934 per N `V_z` for the Z component. These are separate
component-to-reference sensitivities; do not add or interpret them as a
combined interaction or pass ratio. No frame demand is supplied here, so no
current bolt demand ratio is populated.

## Missing signed wrench and unresolved checks

The exact missing input is the accepted, signed BG001 cut wrench on
`knee_outer_left_spine` from `base_post_outer_left`, with equal-and-opposite
action on the other side, at global `(-1208.151, -137.600, 192.475) mm`:

```text
[F_x, V_y, V_z, M_x, M_y, M_z]
 units: [N, N, N, N·mm, N·mm, N·mm]
 axes: global X/Y/Z; right-hand positive moments
```

All six signed components are missing for each of `a12-rear`, `a12-forward`,
`a12-left`, `k12-right`, `k12-rear`, and `a1-rear`. The source load wrenches
are upstream panel loads, not BG001 actions. The available c11 one-case output
is a diagnostic active-set branch and is not an accepted demand. The current
demand-coverage register records no path-complete joint demand subset.

This map uses only the lateral projection `[V_y, V_z, M_x]`. `F_x` is
bolt-axis tension/separation or compression/contact, outside the lateral
helper. `M_y` could kinematically create an axial tie couple across the Z
spacing, but bolt tension, washers, anchorage, contact, and transfer are
unqualified. The collinear-Z axes provide no axial-force lever arm for `M_z`;
any `M_z` transfer needs unresolved bearing/contact or other geometry.

| Check | Present evidence | Missing evidence |
|---|---|---|
| Group action and sharing | Two modeled axes and 42.05 mm center pitch; source leaves `Cg`/force null and NDS row unassessed | Verified hole stations, loaded-row orientation, applicable group factors, and defensible stiffness/clearance load split |
| Spacing, end, and edge distance | Modeled center pitch only, along proposed Z grain | Verified hole positions and all end/edge distances on both actual receivers for each load direction |
| Splitting, row shear, tear-out, net section | None established by the geometry grouping | Receiver-specific geometry, material basis, signed demand, and applicable checks |
| Washers and local bearing | No washer/head/nut qualification in the single-shear calculation | Delivered dimensions and material, seating/areas, local bearing and washer-bending demand |
| Fit and engagement | Modeled 1/4 in shaft envelope and 38.1 mm receiver intervals | Delivered shank/thread layout, hole/gap, shear planes, and usable engagement through both members |
| Wood adjustments | Conditional SG/`Fe` scenario | Actual species, grade, moisture, and applicable load-duration, wet-service, temperature, and other factors |
| Complete transfer | Geometric association between the two members | Validated bearing/seat/bolt route for the full wrench into both connected members and downstream supports |

## Reproduction and scope

The result JSON pins the geometry inventory, its observed upstream input
hashes, the reviewed NDS producer and reference scenario, `fea/dowel_yield.py`,
and the six-case demand-coverage register. The NDS Chapter 12 PDF hash is
carried forward from the reviewed scenario artifact. Regenerate or verify with
the Python standard library:

```sh
python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-knee-post-conditional-bolt-screen-attempt01/produce.py --write
python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-knee-post-conditional-bolt-screen-attempt01/produce.py --verify
```

This packet reports sensitivity coefficients and conditional individual-bolt
lateral references for a current modeled group. It does not establish group
capacity, axial resistance, splitting resistance, hardware conformity, a
complete load path, or acceptance of BG001.
