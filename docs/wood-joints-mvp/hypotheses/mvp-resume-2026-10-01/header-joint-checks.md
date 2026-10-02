# Six current block/header joints

The current six-case nominal-gap response gives a finite conditional strength
and transfer result for the six header interfaces and their twelve end-grain
bolt axes. The largest same-state lateral reference, including the declared
steel reserve and conservative two-fastener group sensitivity, is **0.259870**.
The largest washer wood-bearing reference is **0.398422**. All 36 interfaces
and 42 complete body balances close. The four center layouts clear the stated
end/edge/spacing envelope. The two knee layouts retain a specific loaded-edge
interpretation exception, described below; no adopted NDS detailing failure or
required model change is established by a component-only 20 mm comparison.

This result is usable for the parent's conditional engineering integration:
the forces, wood-bearing demands, local header cuts and all face/bolt couples
are supplied together. It does not qualify local splitting, hole-ligament load
sharing, torque interaction, delivered hardware or fabrication. Those flags
remain false; solver or historical acceptance is not substituted for them.

## Frozen input and scope

Only `all-outer-corner-frame-attempt01/response.npz` arrays named
`case_id + '_gap_raw_force_n'` are used. The cases are `a12-rear`,
`a12-forward`, `a12-left`, `k12-right`, `k12-rear` and `a1-rear`.

| Input | SHA-256 |
| --- | --- |
| `all-outer-corner-frame-attempt01/comparison.json` | `ec69b49c821a56fdde76d94148405f9f743e4f72add17c89d35af512be76f6a3` |
| `all-outer-corner-frame-attempt01/response.npz` | `aa70480aa18c33bb1cbd7d3a53ff582a0c7a90c93487f92721619474ec251901` |
| `end-grain-route-attempt02/route.json` | `f95fdb55eeee89d68be2e516e017d8d40d1ef4f7f9960c93e4895f53541c7f28` |
| `corner-frame-attempt01/model.json` | `d17dadd7c999e4a1634f53226cf63e131f547cd9cf5d46d87d75c935f2dc807e` |
| `corner-frame-attempt01/row-identities.json` | `bec1feb75be61b321220a047a652cc42f09c4c11d1d3c66377c4035bde4826d5` |
| `corner-frame-attempt01/operators.npz` | `f40bf53412afb400df23ff108e90bac66db3c493da26a19af5c05de329c165ad` |
| `member-screen-attempt02/all-outer-clearance01/action-section-arrays.npz` | `20298c4191d579a06577f877411287febbec60c56d21ba0d31a1e2511f01fd02` |
| `member-screen-attempt02/all-outer-clearance01/geometry.json` | `ecfeee2627fc67d91ce89acd5253bf99a4d79b06451c94ced6b915a664009f9d` |
| `member-screen-attempt02/all-outer-clearance01/member-results.json` | `7f120364d2fc027bee85d7516581a130e7a05728fb9d7de2460978ddea451e01` |
| `remaining-joint-screen-attempt03/grade5-92ksi/screen.json` | `c3615182a2e0fa8eb8d1da96648b01c27531ab9f710ab1498961ec1b46b10de8` |

[source-pins.json](header-joint-attempt01/source-pins.json) also binds the
consumed raw model inputs, seven finished STEP receivers, frozen material
scenario, support geometry and reused code. Each restored connector action is
checked against the frozen physical `D` operator and the current raw force.
Earlier native forces and source acceptance labels are not imported.

The end-grain main blocks have grain **+Z**, the header has grain **+X**, and
these bolt axes are **±Z**. The header's actual source reporting dimensions are
**section_u = Y, 139.7 mm** and **section_v = Z, 38.1 mm**. NDS
§12.3.3.4 `Fe_perp = 4450 psi` and §12.5.2.2 `Ceg = 0.67` are the already
established individual route. They are reused once. No Y-grain stock proposal
or changed stiffness model is selected.

## Component and placement results

The material scenario is the source conditional DF-L No. 2 row, with the
existing member-specific size factors, dry service and normal duration.
The steel scenario is the existing nominal Grade 5 92 ksi yield hypothesis
and smooth 6.35 mm bearing diameter. It does not qualify an actual bolt's
bending yield, shank transition, nut engagement or head/nut strength.

Each named pair ends in `_1`, `_2`. Values below are envelopes of separate
complete states; columns are not combined into a synthetic load case.

| Block / exact axis prefix | Main/header bearing lengths, mm | Y pair pitch, mm | Cg row sensitivity | Maximum simultaneous lateral reference | Maximum washer wood-bearing reference | Maximum header connection-zone \|VY\|, N |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `center_post_cleat_left` / `center_post_header_left` | 128.9 / 38.1 | 35.00 | 0.995508 | 0.245864 | 0.398422 | 308.708 |
| `center_post_cleat_right` / `center_post_header_right` | 128.9 / 38.1 | 35.00 | 0.995508 | 0.208784 | 0.311848 | 285.261 |
| `center_principal_cleat_left` / `center_principal_header_left` | 134.7 / 38.1 | 65.00 | 0.991599 | 0.259870 | 0.341053 | 116.189 |
| `center_principal_cleat_right` / `center_principal_header_right` | 134.7 / 38.1 | 65.00 | 0.991599 | 0.224201 | 0.309744 | 114.974 |
| `knee_outer_left_inner_frame_block` / `knee_outer_left_inner_header` | 139.0 / 38.1 | 93.35 | 0.987911 | 0.200079 | 0.200390 | 63.495 |
| `knee_outer_right_inner_frame_block` / `knee_outer_right_inner_header` | 139.0 / 38.1 | 93.35 | 0.987911 | 0.204400 | 0.134281 | 65.993 |

The governing lateral state is `center_principal_header_left_2`, `k12-rear`:
146.621 N lateral force, zero simultaneous outer tie, and original
`V/(Ceg Z) = 0.257668`. Reserving steel yield for the simultaneous direct axial
stress and assumed parabolic circular-shank shear, then applying the Cg
sensitivity, gives 0.259870. This is an explicit stress-field scenario, not an
NDS through-bolt interaction equation.

For D = 6.35 mm, `1.5D = 9.525`, `3D = 19.05`, `4D = 25.4`,
`5D = 31.75`, and `7D = 44.45 mm`. The closest header grain end is
133.35 mm away. Pair pitches exceed the parallel row full-value spacing and
the largest perpendicular between-row comparator. The twelve header axes
span 93.35 mm across Y, below the 127 mm cross-grain shrinkage limit for these
sawn-lumber fasteners. Both X and Y external block-face distances at the four
center pairs are at least 26.95 mm. Thus the center component envelope needs
no CΔ reduction. A grainwise end distance is not invented by treating the
center of a through end-grain bolt as a transverse fastener.

NDS §§12.1.2.4 and 11.3.6.2 define rows by load alignment. The current pairs
carry unequal, oblique signed forces and moments. Their actual projected
pitches, signed inter-bolt angles and adjacent-row merger triggers are retained
in each state's `pair` record. Two states trigger the merger geometry
diagnostic; this does not establish uniform force sharing. The Cg numbers
above reuse Eq. 11.3-1 with a two-fastener surrogate row, its actual Y pitch,
and 4D equivalent widths for both wood members. They are conservative
component sensitivities, not complete oblique-group adjustment factors.

## The knee 20 mm question

The finished-source knee block bounds are Y = −175.7…−42.35 mm.
Axis 1 lies at Y = −62.35, 20 mm from +Y. Axis 2 lies at Y = −155.7,
20 mm from −Y. Their X edges are 44.45 mm away. These are raw geometry
measurements, not inspected lumber.

The existing `directed_hit` helper is evaluated with the **current** force on
each block. Five states first reach the short Y face:

| Case | Axis | Signed block Fx, Fy, N | First face | Face-normal distance, mm |
| --- | --- | ---: | --- | ---: |
| `a12-forward` | `knee_outer_left_inner_header_2` | +16.497725, −19.703382 | −Y | 20.0 |
| `a12-forward` | `knee_outer_right_inner_header_2` | −2.492707, −13.028969 | −Y | 20.0 |
| `a12-left` | `knee_outer_right_inner_header_2` | +4.832347, −11.815771 | −Y | 20.0 |
| `k12-right` | `knee_outer_left_inner_header_2` | +13.393942, −8.022328 | −Y | 20.0 |
| `a1-rear` | `knee_outer_left_inner_header_1` | +23.962683, +18.448326 | +Y | 20.0 |

Across all states, fifteen knee Y-component comparisons are below 4D;
ten of those still first reach an X face under the full vector. Four header
Y-component comparisons are below 4D, with force opposite the block force.
Every full header lateral force is oblique to its X grain. The table above
therefore cannot be replaced by a fixed loaded face, a group resultant, an
absolute-force envelope, or a rule requiring every face to be 4D.

NDS §12.1.2.1 identifies the loaded edge from the direction in which the
fastener acts; Table 12.5.1C gives 4D for a perpendicular loaded edge and 1.5D
for its opposite unloaded edge. The block action is perpendicular to its Z
grain, so that branch applies. The official 2024 specification does not define
the first-ray versus component-face construction for an oblique force in a
multi-face end-grain block. It also does not provide an oblique header edge
interpolation. The ray only identifies a candidate face; its travel length is
not substituted for the NDS edge distance. Consequently:

- **Adopted actual detailing failures: none established.** The five full-vector
  face diagnostics are real conditional short comparisons, not an adopted
  universal NDS face-selection rule.
- **Exact remaining detailing fact:** which loaded-edge construction applies
  to the five listed end-grain states. Selecting the first-face normal-distance
  interpretation makes them 5.4 mm short. The component-only comparisons do
  not independently establish that requirement.
- Ceg does not waive placement. CΔ is not set to 20/25.4 to waive an edge
  minimum. This sheet does not give the knee placement an unconditional pass.

No axis adjustment is established as required, and none is made. If the parent
adopts the first-face normal-distance interpretation, the smallest dimensional
remedy to these diagnostics is the following **conditional proposal**:

| Axis | ΔY, mm | Proposed source-axis point X, Y, Z, mm |
| --- | ---: | --- |
| `knee_outer_left_inner_header_1` | −5.4 | −1085.850, −67.750, 338.499 |
| `knee_outer_left_inner_header_2` | +5.4 | −1085.850, −150.300, 316.401 |
| `knee_outer_right_inner_header_2` | +5.4 | +1082.675, −150.300, 316.401 |

These prospective changes affect both the header and the named inner block
receiver for each axis. They give 25.4 mm at the implicated Y edge; the left
pair pitch becomes 82.55 mm and the right pair pitch 87.95 mm. Stock envelopes
and Z bearing lengths remain unchanged in this coordinate proposal. Header
near-edge distances become 31.75 mm for left axis 1 and 25.4 mm for both
axis-2 moves. The maximum 11.0652 mm washer sweep fits within these external
face distances; a moved-footprint BRep check is not claimed.

Left axis 1 would move toward the existing X-axis
`knee_outer_left_side_2` bore: its Y web between 7.5 mm bore envelopes would
shrink from 7.452644 to **2.052644 mm**. The axis-2 moves retain at least
36.571913 mm Y web to the companion side bores. The 2.052644 mm web needs its
own local load-transfer/detail treatment before calling the proposal a fix.
The proposal would replace source bores, not add neighboring holes to an
already drilled part. It changes force application points, bolt couples and
receiver sections; current forces cannot qualify it. A symmetric four-axis
move would also change right axis 1 although none of the five first-face
diagnostics requires that extra move. No new material orientation, CAD,
operator, model or authority is written here.

## Washer wood bearing and complete joint transfer

All 144 seat-state evaluations use the **same-state outer tie** and the
minimum displaced supported washer area. The existing remaining-seat packet
supplies twenty seats. It excludes the primary left knee; its four seats are
supplied by the existing geometry-only
`/tmp/mini-moonboard-eccentric-parent-check-2026-10-01.json`, SHA-256
`0ae0af403cd99b323f0deb489e64bdf7cf94e0d32f0b84f0a9344efda2369354`.
Its raw model binding and 7.5 mm bore scenario match these unchanged receivers.
No old force or primary-corner acceptance is consumed.

Z-axis axial pressure is perpendicular to the header grain and parallel to
block grain. Thus the header uses **Fc⊥ = 4.309223 MPa** and each block uses
its source size-factor Fc∥ scenario. No bearing-area, preload or friction
credit is taken. The governing header head seat is
`center_post_header_left_1`, `a12-forward`: tie 356.809863 N,
supported area 207.823202 mm², pressure 1.716891 MPa, ratio 0.398422.
The largest timber-face pressure/reference is 0.027622. These mean-pressure
references do not establish washer-metal spreading, eccentric pressure peaks,
head/nut resistance or a coupled local wood failure surface.

Each interface records its four lateral component actions, two axial ties
at their actual outer seat points, and four compression-only contact cells.
The same datum is used for the reciprocal header and block wrenches. Role
wrenches sum to the complete interface force and moment; no pure couple is
discarded or replaced by equal bolt sharing. Every block's other interfaces
and dead-load actions remain in its complete body accounting. Zero-force
contacts and free couples remain present. Maximum body residuals are
**1.10845×10⁻¹² N** and **4.78504×10⁻⁹ N·mm**, within the existing 0.1 N /
2 N·mm limits. The largest interface moment component is 12,777.872 N·mm;
the JSON identifies its simultaneous force and the contributing bolt/face
terms. Parent owns the integrated panel stiffness and contact sensitivity.

## Header splitting and local sections

The worksheet includes cuts immediately outside each full contact footprint
and **every saved cut inside it**. Boundary-only demand would miss the
308.708331 N Y-shear demand within the left center-post footprint in
`a12-forward`. Its complete saved wrench at station 983.320892 mm, after the
cut, is `(N,VY,VZ,T,MY,MZ) = (−8.034647, +308.708331, −189.525034,
+2142.335485, −4460.273818, −30110.832094)` in N and N·mm.
`header_connection_zone_signed_peaks` records a simultaneous six-component
wrench for each component's extremum; different extrema are not summed.

For a limited in-plane splitting diagnostic, the existing characteristic
reference `F90,Rk = 14 b √[he/(1−he/h)]` is retained with **b = Z = 38.1 mm**,
**h = Y = 139.7 mm**, w = 1 and both possible loaded Y edges. The smallest
characteristic reference at that center-post pair is 5627.580 N, giving
`308.708331/F90,Rk = 0.054856`. This is not an NDS allowable resistance or a
cross-code design utilization. It does not qualify the Z face/washer actions,
the below-neutral-axis concentrated-load provision, or simultaneous torque.
The exact local fact still needed is an applicable resistance/load distribution
for those combined demands; no tensile-perpendicular wood allowable is
invented from Fv or Fc⊥.

The 105 hash-matching finished header section planes are joined to both sides
of all six current cases: **1260 section states**. Their old stock reporting
frame is u = +Z, v = −Y. Its area covariance is rotated into current u = +Y,
v = +Z, and moments are shifted to the actual section centroid. The resulting
connected-section linear normal reference peaks at **0.156970** in
`k12-rear`, station 1419.2 mm; its area is 5135.251826 mm². The net-area shear
proxy peaks at **0.217607** in `a1-rear`, station 22.225 mm. These are
elementary section references, with no hole concentration or stability credit.
Signed header torque reaches **−34,937.382375 N·mm** at that latter cut;
there is no invented torque capacity.

At the six bolt-group stations **133.35, 993.49, 1103.20, 1335.20, 1443.55
and 2301.875 mm**, the source section has three disconnected Y strips.
Their areas are 4751.07 mm² at the knees and 4766.31 mm² at the centers.
All **72** corresponding two-sided case states retain N, VY, VZ, T, MY and
MZ, but normal/shear resistance fields are null. The exact missing local fact
is how the surrounding three-dimensional wood transfers these same-state
actions into each strip. Aggregate area or covariance does not supply that
load division. The remaining 1188 connected states receive the stated proxy;
none is promoted to complete local section acceptance.

## Sources, outputs and reproduction

Placement and group clauses were read from the pinned official
[NDS 2024 Chapter 12](https://awc.org/wp-content/uploads/2026/09/AWC_NDS2024_withCommentary_20260911_Website_Chapter-12-Dowel-Type-Fasteners.pdf)
and [Chapter 11](https://awc.org/wp-content/uploads/2026/09/AWC_NDS2024_withCommentary_20260911_Website_Chapter-11-Mechanical-Connections.pdf):
§§12.1.2, 12.5.1, Tables 12.5.1A–D, §§12.6.2–.3 and §§11.3.6.1–.3.
Local parallel-grain Appendix E limits remain those of the pinned
[2024 Appendix](https://awc.org/wp-content/uploads/2026/09/AWC_NDS2024_withCommentary_20260911_Website-Appendix.pdf).
The established splitting formula and its characteristic-only limits are
reused from `top_corner_actions.py` and its existing source cache. The
[AWC edition page](https://awc.org/resources/2024-nds/) identifies the 2024
package. No new applicability investigation into Fe⊥/Ceg is performed.

- [header_joint_checks.py](header_joint_checks.py) is the executable producer.
- [checks.json](header-joint-attempt01/checks.json) contains the finite result,
  peaks, five knee diagnostics, false qualification flags and output hashes.
- [joint-states.json](header-joint-attempt01/joint-states.json) contains all
  72 bolt states and their two same-state washer seats.
- [joint-actions.json](header-joint-attempt01/joint-actions.json) contains
  36 complete interfaces, signed local header demand extrema and 42 balances.
- [placement.json](header-joint-attempt01/placement.json) preserves every
  signed direction, raw face dimension and component/first-face comparison.
- [header-sections.csv](header-joint-attempt01/header-sections.csv) contains
  all 1260 section states, rotated properties and disconnected-strip flags.
- [source-pins.json](header-joint-attempt01/source-pins.json) binds the actual
  consumed source bytes, including the producer.
- [SHA256SUMS](header-joint-attempt01/SHA256SUMS) lists exact repository paths
  and hashes for both owned source files and all retained output files.

```sh
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  .venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/header_joint_checks.py
```

The producer preserves existing result files; reproduce in a disposable copy
with the same pinned sources and an empty owned output destination. The final
root outputs stay active for parent integration. `header-joint-attempt01/preliminary/`
retains the first calculation and its producer snapshot; it used boundary-only
splitting demands, and is superseded by the root calculation including interior
cuts. It is recoverable history within the same input packet, not an active
consumer target. No archive/prune operation, test, review agent, native solve,
frame solve, CAD rebuild, shared-document edit, staging or commit is performed.
