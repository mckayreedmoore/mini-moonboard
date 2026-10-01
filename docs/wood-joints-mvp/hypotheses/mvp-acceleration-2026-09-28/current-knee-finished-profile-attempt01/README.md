# BG001 finished knee profile distances

This read-only screen measured the finished STEP profiles for
`knee_outer_left_post_1` and `knee_outer_left_post_2` in
`base_post_outer_left` and `knee_outer_left_spine`. The 48 finite rays cover
the four signed profile directions at 0.01 mm inside each receiver-thickness
endpoint and at its midpoint. The producer verified the acceleration inventory,
reduced-static member geometry, attempt04 manifest, helper and both STEP hashes
before querying. No CAD rebuild, model edit, mesh or native mechanics run was
performed.

## Verified distances

`g` is the pinned proposed grain axis (+Z); `e = unit(g × a)` is +Y for the
pinned +X bolt axis `a`. Values are from the bolt centerline to the final
finished exterior profile in the corresponding ray direction. The three
through-thickness stations returned identical terminal distances for each
bolt/member/direction.

| Bolt | Receiver | Grain end `g− / g+` (mm) | Edge `e− / e+` (mm) |
|---|---|---:|---:|
| `knee_outer_left_post_1` | `base_post_outer_left` | 171.45 / 67.45 | 38.10 / 101.60 |
| `knee_outer_left_post_1` | `knee_outer_left_spine` | 31.75 / 244.55 | 44.45 / 95.25 |
| `knee_outer_left_post_2` | `base_post_outer_left` | 213.50 / 25.40 | 38.10 / 101.60 |
| `knee_outer_left_post_2` | `knee_outer_left_spine` | 73.80 / 202.50 | 44.45 / 95.25 |

Every ray has exactly one terminal face candidate. All 48 terminal hits are
finite `PLANE` faces with `|n·ray| = 1.0`, so each measured profile direction
ends at a square-cut plane. The base-post terminal grain faces are BRep faces
12/13 (`g−/g+`); its edge faces are 14/7 (`e−/e+`). The spine grain faces are
4/3 and edge faces 2/5. These are local STEP face ordinals. The cut-aware result
therefore corrects the earlier descriptor-only note in
[`current-knee-post-check-dependencies.md`](../current-knee-post-check-dependencies.md),
which called the spine end oblique and left its grain ray unmeasured: for these
BG001 axes, the queried grain-terminal faces are square in the finished STEP.
This finding is scoped to these two receivers and the sampled stations; it does
not claim a continuous minimum for every possible point through receiver depth
or apply to other members.

The nearest queried edge distances are 38.10 mm (6D) in the post and 44.45 mm
(7D) in the spine, where modeled nominal `D = 6.35 mm`. Both exceed 4D
(25.40 mm). The complete raw face hits, material intervals and normals are in
[`query.json`](query.json).

## Conditional NDS-2024 geometry screen

This reuses the Chapter 12 method recorded in the
[`ordinary finished end/edge query`](../../evaluation-resume-2026-09-24/ordinary-finished-end-edge-query-attempt01/README.md):
§§12.1.2.1–.3 define end/edge/spacing measurements, §12.1.3.4 directs bolts to
Tables 12.5.1A–D, §12.5.1.2(a) and Table 12.5.1A give end-distance `CΔ`, and
§12.5.1.3/Table 12.5.1C cover edge distances. The primary source is the
official [AWC 2024 NDS Chapter 12 PDF](https://awc.org/wp-content/uploads/2026/08/AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-%E2%80%93-Dowel-type-fasteners.pdf),
whose pinned SHA-256 is
`5fc837523ff10acc097a162718700a9b4ba64e627d2b0023439146d42fe4ee2a`. The
current [March 2026 AWC errata/addenda](https://awc.org/wp-content/uploads/2026/03/2024-NDS-Errata-and-Addenda-03.23.26.pdf)
was also checked; it does not change the cited Table 12.5.1A/C numeric
geometry requirements. The values below are a conditional geometry screen for
the NDS softwood row and modeled quarter-inch diameter, not an assigned
connection resistance.

For softwood parallel-grain tension (fastener bearing toward a member end),
Table 12.5.1A uses 7D (44.45 mm) for `CΔ = 1.0` and 3.5D (22.225 mm) for the
`CΔ = 0.5` floor. The finished STEP shows two shorter square ends in the
opposed signed load path: the post `post_2/g+` end is 25.40 mm (4D), and the
spine `post_1/g−` end is 31.75 mm (5D). Both exceed the half-factor floor, so
§12.5.1.2(a) gives the preliminary branch factors `4/7 = 0.5714` and
`5/7 = 0.7143`; 4D is not categorically excluded or rounded down to 0.5. If
parallel-grain bearing/tension toward +Z in the post and toward −Z in the spine
are established as the applicable signed scenario, NDS §12.5.1.2's group rule
makes the smallest factor, 4/7 from the post upper end, apply to every fastener
in BG001. Other receiver, shear-plane, or adjustment factors remain unknown.
For the reversed directions (post toward −Z and spine toward +Z), all sampled
square-end distances exceed 7D, so this end-distance branch is 1.0 if that
reversed signed scenario applies.

For parallel-grain compression and perpendicular-to-grain end loading,
Table 12.5.1A requires 4D for `CΔ = 1.0` and 2D for its 0.5 floor. The shortest
queried square end is exactly 4D; all others are longer. These geometric ends
therefore do not reduce those branches. Table 12.5.1C's fixed perpendicular
loaded-edge minimum is 4D and its unloaded-edge minimum is 1.5D; all four
queried edge distances in each receiver exceed 4D. Any parallel-load row
classification, signed force angle, member shear check and full connection
factor still require their own inputs. Loading at an angle to the fastener is
also a distinct equivalent-shear-area route under §12.5.1.2(b).

The model proposes a softwood geometry screen but does not verify the delivered
species, grade, dimensions, bolt, holes, or physical cut. The center-to-profile
values do not check splitting, net section, shear-out, bearing, hardware,
complete load transfer or group capacity. No mechanical pass or failure is
assigned.

## Bores and limits

The initial void on each ray is 0–3.75 mm, the modeled 7.5 mm receiver bore.
On rays toward the other BG001 bolt—`post_1/g+` and `post_2/g−` in each
receiver—the query preserves a second internal cylindrical-bore interval at
38.30–45.80 mm. These are bore walls, not terminal exterior faces. The final
material exits are the single square planes listed above. The query's stations
are discrete, so it does not optimize a continuous minimum through receiver
thickness or infer a physical installation.

## Reproduction

From the repository root, run the pinned finite-ray producer with the project
environment:

```sh
PYTHONDONTWRITEBYTECODE=1 taskset -c 15 .venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-knee-finished-profile-attempt01/query.py
```

[`execution.json`](execution.json) records the completed run and output hashes.
The query itself rejects mismatched source pins, changed helper code, STEP hash
changes, non-single-solid inputs, axis/receiver disagreement, or receiver
projections that do not match the finished STEP vertices.
