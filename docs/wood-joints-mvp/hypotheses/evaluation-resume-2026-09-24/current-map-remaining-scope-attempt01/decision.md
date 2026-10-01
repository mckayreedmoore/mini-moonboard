# Remaining current-map scope

Read-only source and result audit. No deck, geometry, solver source, native
run, or freeze was changed or created. [`source-bound-review.json`](source-bound-review.json)
binds the inspected files and records the complete per-axis rows, pivots,
controls, mesh inventories, carrier membership checks, and run references.

The current A09 ordinary-joint packet has four actual six-DOF nut-fit maps.
Each map individually has rank six and its source report reproduces a rigid
field to at most `4.92e-15`; each rigid carrier NSET exactly matches its
carrier C3D10 node set, and none of the 24 dependent shaft nodes appears in
its carrier set. These are useful kinematic and incidence checks. The four
serialized maps have different support populations, term counts, pivots and
dependent DOFs. I found no exact cross-axis coefficient transformation in the
source record, so common rank, similar hardware, and near-identity rigid
reproduction do not establish a reusable A00 dynamic result.

| Current axis | Positive-mass C3D10 body; nodes/elements | Nut carrier; nodes/elements | Global shaft direction, head to nut | Pivot, global XYZ mm | REF / ROT controls | Fit-support nodes / full equation terms per row | Six dependent node:DOF rows |
| --- | --- | --- | --- | --- | --- | --- | --- |
| rail 1, A00 | `M00_A00_BOLT_HEAD_PLUS_SHAFT_UNION`; 11,348 / 5,490 | `M03_A00_NUT`; 1,107 / 519 | `(0, -0.6427876097, -0.7660444431)` | `(134.5, 1.1784560903, 410.8568890787)` | `116163 / 116164` | 251 / 754 | `61518:3, 61518:1, 60595:1, 57834:3, 59700:1, 61486:2` |
| rail 2, A01 | `M04_A01_BOLT_HEAD_PLUS_SHAFT_UNION`; 10,927 / 5,225 | `M07_A01_NUT`; 1,101 / 511 | `(0, -0.6427876097, -0.7660444431)` | `(134.5, -24.1010105327, 432.0688801977)` | `116165 / 116166` | 258 / 775 | `75714:2, 75714:1, 76786:1, 76786:3, 76671:1, 72989:3` |
| principal 1, A02 | `M08_A02_BOLT_HEAD_PLUS_SHAFT_UNION`; 10,464 / 4,938 | `M11_A02_NUT`; 1,160 / 549 | `(-1, 0, 0)` | `(48.918, 32.3331282440, 473.6550246020)` | `116167 / 116168` | 254 / 763 | `93511:3, 91282:2, 90409:2, 93193:1, 90606:3, 93908:1` |
| principal 2, A03 | `M12_A03_BOLT_HEAD_PLUS_SHAFT_UNION`; 10,571 / 4,988 | `M15_A03_NUT`; 1,156 / 545 | `(-1, 0, 0)` | `(48.918, 53.5451193640, 498.9344912250)` | `116169 / 116170` | 259 / 778 | `104120:3, 104774:2, 105674:2, 105030:1, 108657:1, 103937:3` |

The direction vectors come from the hash-bound hardware inventory; pivots and
dependent rows come from the A09 coupling report. `REF` controls translations
in DOFs 1–3; `ROT` controls the global rotation vector in radians in DOFs 1–3.
The positive-mass bodies use the same isotropic steel (`E=200000 MPa`,
`nu=0.3`, `rho=7.85e-9 tonne/mm^3`). The four nut C3D10 sets have explicit
`E=200000 MPa`, `nu=0.3`, zero-density sections and are constrained as rigid
carriers. The fit is geometric and does not use timber grain. The A09 port
frame separately defines `X` along rail grain, `T` and `N` along its source
principal/cleat directions.

The completed native known-answer fixture qualifies only `M00_A00` and its
`M03_A00` carrier. Its three frozen cases passed direct, mapped-without-carrier,
and mapped-with-carrier checks under a small implicit global-Y rotational
body-force history (`alpha_y=1.2 t rad/s^2`, 10 accepted states, `dt=0.001 s`,
terminal `theta_y=2.01e-7 rad`). The measured case captures were 24.72–27.13
MB and 13.28–20.11 s. This qualifies one map/mode response and the generic
solver path; it does not natively exercise A01–A03.

The inspected A09 `port_motion_n_plus.inp` is an input-only `NLGEOM *STATIC`
port-control displacement path with endpoint relative coordinate
`[0,0,1,0,0,0]` in the `X,T,N` frame (1 mm relative N translation). Its audit
is explicitly input-only and no accepted response is attached. That path is
not the A00 global-Y dynamic body-force test. The next ordinary-joint transient
force history has not been selected, so there is no source basis for choosing
an additional active acceleration or rotation direction.

The next step is to bind the intended ordinary-joint deck and its actual
external-port force or motion history to the four axis IDs. The source report
already establishes separate rank-six rigid kinematics for all four. Before
adding native work, compare only the maps active in that selected case under
their exact coordinate transforms. If exact transformed equivalence is not
shown and a dynamic response comparison is required, use matched direct,
map-only, and map-plus-carrier cases for only those distinct active maps, with
the existing full U/V, six-control, equation residual, carrier-kinematics,
mass/energy and parity observables. If all three remaining maps must be
qualified, the measured A00 case sizes suggest keeping each of the nine
serialized captures under the existing 64-MiB per-case limit; this is an
estimate, not a measured result. One combined full-field capture for three
remaining carriers would likely exceed that output cap. Do not broaden the
scope to all maps as a blanket prerequisite if the selected case uses fewer.

Key pins: A09 `nut-coupling.inp` SHA-256
`af5b36dce4e85b19a6a5b4805dd6b00259da88ccc1a849769642db2ecbf62903`,
`nut-coupling.json` `568ade2437181bc8e9398f64a2818bbf8bd3f46a64dae9639bf363cb68bec960`,
`rigid-carriers.inp` `a15eebb0537a4a3f096531f2c4e48ecd26b6ec53908d61178ead7dfe3bc27815`,
`materials.inp` `e0063d0ebc2232b6699f020488944617b1f44f7bfa38f931f47907d08202a3bb`,
and `hardware-budget-2026-09-24.inventory.json`
`ec673859835f1fdbb4e65fd7527416053b9ad708ebf7b9ea15f61af97d62da6e`.
The A00 freeze is `36b624a9d4658862e96a225a28b844b8372150dc449e4749a4b683faf5adcf9e`
and its terminal verifier report is
`e9c2da08d7ff1bffdd8fcffbb06d921ab71472ec409494c91334e1767c506603`.
