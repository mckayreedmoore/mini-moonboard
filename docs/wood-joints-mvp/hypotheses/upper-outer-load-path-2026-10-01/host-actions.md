# Upper outer host point-action sections

This note records a conditional point-action extraction for the two outer cleats and their three receiving hosts. It is an input record for later splitting-method review; it is not a strength check, construction instruction, or joint acceptance.

The canonical producer is `host_actions.py`. Its byte-canonical generated data file is `host-actions.json`; that JSON is ignored by Git and is kept as a local raw reference. Rebuild and check it with:

```sh
uv run --no-sync python docs/wood-joints-mvp/hypotheses/upper-outer-load-path-2026-10-01/host_actions.py --write
uv run --no-sync python docs/wood-joints-mvp/hypotheses/upper-outer-load-path-2026-10-01/host_actions.py --verify
uv run --no-sync pytest -q docs/wood-joints-mvp/hypotheses/upper-outer-load-path-2026-10-01/test_host_actions.py
```

The producer is [host_actions.py](host_actions.py), SHA-256
`39b3af2bdd468d20db868454cb81cce1ad2d3af30059c4204aa2284892cd390b`.
The current ignored local result `host-actions.json` has SHA-256
`5ee4c6da1266d9fd06cc26162fbebb9a96e8e907bd283dda25747d9a63516551`.
These identities bind this summary to the checked producer and result bytes;
the ignored JSON remains a local raw reference.

## Scope and extraction

The four evaluated interfaces are `base_rail_top <- top_outer_left_cleat`, `base_rail_top <- top_outer_right_cleat`, `base_side_left <- top_outer_left_cleat`, and `base_side_right <- top_outer_right_cleat`. The three frozen response families each contribute seven same-state increments, for 84 interface records and 63 whole-host balances. Every interface group contains the two lateral bolt-plane rows, two receiver-specific outer-seat tie rows, and four contact-cell point forces.

At each increment, the whole-host external wrench sums every incident physical connection row, every incident exact floor-tangent reaction (none are incident on these three hosts in the pinned records), and every discrete `physical_body_loads` node. Discrete loads are multiplied by that response increment's recorded load factor. Receiver-specific `first_point`/`second_point` values locate the outer-seat ties on the receiving host. The computed host force and moment residuals and propagated source rounding radii reproduce both the frozen response body balance and its independent all-body audit. These are source bookkeeping closure checks, not evidence of physical accuracy.

The producer inventories all incident connection source points, point identities, grain stations, finite contact bounds, and discrete-load node stations. It checks their station geometry against the same frozen model geometry at all 21 response states. For each target contact, all source polygon vertices are projected onto the receiving host's exact grain axis. Four contact-cell areas sum to the frozen finite polygon patch area within rounding. The patch footprint, rather than its cell-centroid points alone, sets the bracket extent.

At each bracket plane, the producer sums source point actions on each host half, transports the resulting wrenches to the cut datum, and reports both internal cut wrenches with signed local `N, Vu, Vv, T, Mu, Mv`. `N` here means force along the source grain vector `g`; `Vu` and `Vv` follow the exact model `section_u` and `section_v` vectors. The transverse `u-v` norm is retained as a diagnostic only. The other transverse component, axial action, torsion, and both bending moments remain visible. Point rows on a cut receive explicit one-sided assignments. Whole-host residual and RF rounding intervals, source coverage on each side, and the wrench jump across each target bracket are retained in the raw JSON. The jump lists target rows, competing connection/support rows, and discrete-load nodes separately; neighboring actions are not attributed to the target group.

The source methods identify the splitting check with internal shear on either side of a concentrated angled connection. These results remain conditional point-action section demands: they are not finite-element integrated cut tractions. The Figure-plane mapping and applicability remain unresolved in this artifact. No `Fv,Ed`, EC5 factor, resistance, capacity, or acceptance is assigned. In particular, neither an unsigned bolt-force sum nor the `Vu-Vv` resultant is substituted for a source-defined shear plane.

## Brackets and saved STEP sections

Stations are measured from each host's source-model start along its exact grain vector. The finite patch bounds below come from projection of every source polygon vertex. A 1 mm offset is used where host length permits; the left and right rail patches touch their respective rail ends, so the associated terminal bracket cut has zero exterior clearance.

| Interface | Host grain length (mm) | Finite target footprint (mm) | Before / after cuts (mm) | Saved STEP section area at both cuts (mm²) |
|---|---:|---:|---:|---:|
| `base_rail_top <- top_outer_left_cleat` | 2257.425 | 0.000–88.900 | 0.000 / 89.900 | 5322.570 |
| `base_rail_top <- top_outer_right_cleat` | 2257.425 | 2168.525–2257.425 | 2167.525 / 2257.425 | 5322.570 |
| `base_side_left <- top_outer_left_cleat` | 2539.768 | 2412.768–2501.668 | 2411.768 / 2502.668 | 12419.330 |
| `base_side_right <- top_outer_right_cleat` | 2539.768 | 2412.768–2501.668 | 2411.768 / 2502.668 | 12419.330 |

The left rail's before cut is at its start boundary and the right rail's after cut is at its end boundary. Those are explicit one-sided terminal traces, not two strictly interior cuts. The side brackets have 1 mm clearance either side of the finite target footprint, with 37.100 mm of host material from the after cut to the side-host end. The complete target group, including point ties and bolt planes, lies between its two reported cuts.

The areas are read-only planar sections of the hash-pinned saved STEP solids, queried with CadQuery/OCP; no geometry was reframed or regenerated. Each queried cut produced one planar component face and one wire. This describes the saved BRep at those planes only. It does not establish the section of any built member, inspected bores or cuts, integrated traction, or a usable design section. Exact local section bounds, plane origins, component faces, and kernel versions are in the raw JSON.

The exact source local frames are preserved, not relabeled into a newly assumed global basis:

| Host | Grain `g` | Source section `u` | Source section `v` | Candidate global `+N` projection |
|---|---|---|---|---|
| `base_rail_top` | `[1, 0, 0]` | `[0, 0.6427876099, 0.7660444429]` (`T`) | `[0, -0.7660444429, 0.6427876099]` (`N`) | `Vv` |
| `base_side_left/right` | `[0, 0.6427876099, 0.7660444429]` (`T`) | `[1, 0, 0]` (`X`) | `[0, 0.7660444429, -0.6427876099]` (`-N`) | `-Vv` |

The last column is only a signed projection exposed for later source-plane binding. The JSON retains all local components and includes a projected `+N` value and rounding radius at each cut side. Candidate signed loaded-boundary and farthest-fastener distances are geometric diagnostics from these source axes and saved STEP edges; they do not adopt `h_e` or a resistance.

Across the 84 records, the largest absolute conditional point-action projection onto global `+N` among either half-host cut wrench is:

| Interface | Signed projection (N) | Source state | Cut | One-sided trace and host half |
|---|---:|---|---|---|
| Rail / left cleat | +929.482 | A12 rear, increment 6, factor 1.0 | after-group | approach from negative station; positive-station half |
| Rail / right cleat | -1055.889 | K12 rear, increment 6, factor 1.0 | before-group | approach from negative station; positive-station half |
| Left side / left cleat | -1715.789 | A12 rear, increment 6, factor 1.0 | before-group | approach from negative station; negative-station half |
| Right side / right cleat | +1664.405 | K12 rear, increment 6, factor 1.0 | before-group | approach from negative station; positive-station half |

These are extrema of the reported conditional point-action resultants over the two cuts, both one-sided traces, and both host halves. They are not adopted EC5 `Fv,Ed` values, finished-cut tractions, or capacities.

## Frozen input pins

All hashes below are SHA-256. The producer refuses to write or verify if any pinned source is missing or changed.

| Frozen input | SHA-256 |
|---|---|
| `upper-frame-joint-review-2026-09-30/upper-joints.json` | `0fc5f9ce9c92effcb01d3213c38b33282c281539dab9d48cb06f33e15c1994a6` |
| `upper-frame-joint-review-2026-09-30/freeze.json` | `d4ba1c78eb358d25e32819201e9c59e05d425a06d9e4e5cca3dc09d7139ffd73` |
| `mvp-acceleration-2026-09-28/reduced-static-attempt01/contact-geometry.json` | `034067430fff5207cdb40819fa8118a367edeb29a8d83926928cc96a0e87d151` |
| A1 rear `model.json` | `72d043e1a70702d8d464c21a039e897036e17c95e368ec776063584dac74f5fd` |
| A1 rear `response-zero-u-token.json` | `257b5b743369fcc2242537b7ccfe81f2efba0a195ef044624d7b67da6a09678c` |
| A1 rear `parent-all-body-response-audit.json` | `247845921630a092c3f7a79d9ac11c92d732f021d2cb1dc5214e54b1a344deca` |
| A12 rear `model.json` | `8a90452d8afa1f1722b3253b18d5aeec72c432033a22d5d0828082022cc1cda8` |
| A12 rear `response.json` | `892dadeed0b20d809ce5250d3cd1c3deb31697f69208d8bbefb5f702160e1274` |
| A12 rear `parent-all-body-response-audit.json` | `3da26086016c01f830e055bfa72c8a55370c9adc138b28d73127596924c410d5` |
| K12 rear `model.json` | `8f1d9bce9b62b18b3694f81816ef5c4c7cbe5e94b4c459a640fce7a98db68dbd` |
| K12 rear `response.json` | `42ffb135d47bd3bd28874e886682b4f07175ee060fb383b6e3c128e5102073c6` |
| K12 rear `audit.json` | `66c2b9aa397b16cd4c0b2420c5cf4588e15d12bfd3fbfd75b7df8f2b0d1d4bee` |
| Saved `base_rail_top.step` | `79b4f7f66f35928ed383d0e396ce221d9a4302136b088a7bcd41749c52a10a60` |
| Saved `base_side_left.step` | `237c3fa6aa0b52c39124580810d048e38919b99b9a1fb5db5a2423e7eda62fdf` |
| Saved `base_side_right.step` | `ddb6ac20f1f50a9036448eb5680fdc486532ff3826ce52d566baf685a800a59f` |

Full source-relative paths and repeated pin records are included in `source_pins` in `host-actions.json`. No native solve was run and no geometry was modified.
