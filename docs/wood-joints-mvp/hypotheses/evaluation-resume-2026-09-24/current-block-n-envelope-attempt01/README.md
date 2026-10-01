# Current block canonical station-N projection — attempt01

## Result

This attempt measures the 24 connector-block STEP solids from the reviewed
`led-clearance-2x6-runner-seated-blocks-v1` revision along the canonical station
axis `N=(0,-sin(50°),cos(50°))`. It uses each exact, hash-pinned STEP BRep and
the attempt02 material-frame map. It does not assign a station datum.

The plan requires each station report to name its datum. The reviewed plan,
decision log, criteria, current-criteria coverage, attempt02 input manifest,
attempt02 material-frame map, source inventory, orchestration handoff, and
prior outer-node result were checked and their hashes are recorded in
`block-n-envelope.json`. The only explicit datum found is the historical WJ-03
outer post/header-front-bottom corner. It does not define datums for the
reviewed 24-block revision. Source-inventory member-frame origins are recorded
as unadopted candidates where present. Several candidate receivers have no
source-inventory frame record; their exact STEP geometry is still pinned, but
no missing origin is inferred from it.

Therefore the `ordinary_n_envelope` criterion remains pending and unresolved.
No pass, exceedance, or exact-contact disposition against that station-relative
limit follows from these body spans. No dimensioned exception is authorized.

## Conditional body-only geometry screen

For each global point `p=(x,y,z)`, the producer evaluates

```text
n = N · p
n_min = min over the exact block BRep of n
n_max = max over the exact block BRep of n
body_span = n_max - n_min
```

The imported BRep is rotated from global XYZ into the attempt02 station X/T/N
basis with no translation, then bounded with CadQuery's optimal OCCT BRep
bounding box. The exported `N-min` and `N-max` coordinates are relative to the
global XYZ origin only; global origin is not a station datum. The separate
span comparison to 139.7 mm is dimensional diagnostics only, not an envelope
status. No viewer mesh or tessellation is used.

| Block ID | N-min from global origin (mm) | N-max from global origin (mm) | Body span (mm) | Span-only relation |
|---|---:|---:|---:|---|
| `bottom_center_left_cleat` | 219.840967859 | 339.540967859 | 119.700000000 | below |
| `bottom_center_right_cleat` | 219.840967859 | 339.540967859 | 119.700000000 | below |
| `bottom_outer_left_cleat` | 219.840967859 | 339.540967859 | 119.700000000 | below |
| `bottom_outer_right_cleat` | 219.840967859 | 339.540967859 | 119.700000000 | below |
| `center_post_cleat_left` | 137.199294728 | 288.155968610 | 150.956673882 | above |
| `center_post_cleat_right` | 137.199294728 | 288.155968610 | 150.956673882 | above |
| `center_principal_cleat_left` | 205.629767835 | 399.229667564 | 193.599899728 | above |
| `center_principal_cleat_right` | 205.629767835 | 399.229667564 | 193.599899728 | above |
| `knee_outer_left_inner_frame_block` | 210.494150049 | 401.993654286 | 191.499504236 | above |
| `knee_outer_left_spine` | 122.239411239 | 406.858036499 | 284.618625260 | above |
| `knee_outer_right_inner_frame_block` | 210.494150049 | 401.993654286 | 191.499504236 | above |
| `knee_outer_right_spine` | 122.239411239 | 406.858036499 | 284.618625260 | above |
| `left_service_inner_lower_cleat` | 229.840968000 | 349.540968000 | 119.700000000 | below |
| `left_service_inner_upper_cleat` | 229.840968000 | 349.540968000 | 119.700000000 | below |
| `left_service_outer_lower_cleat` | 229.840968000 | 349.540968000 | 119.700000000 | below |
| `left_service_outer_upper_cleat` | 229.840968000 | 349.540968000 | 119.700000000 | below |
| `top_center_left_cleat` | 229.840967859 | 349.540967859 | 119.700000000 | below |
| `top_center_right_cleat` | 229.840967859 | 349.540967859 | 119.700000000 | below |
| `top_outer_left_cleat` | 229.840967859 | 349.540967859 | 119.700000000 | below |
| `top_outer_right_cleat` | 229.840967859 | 349.540967859 | 119.700000000 | below |
| `wj04_lower_full_stock_cleat` | 229.840968000 | 349.540968000 | 119.700000000 | below |
| `wj04_upper_g7_crosscut_full_stock_cleat` | 262.640968000 | 349.540968000 | 86.900000000 | below |
| `wj06_outer_lower_right_cleat` | 229.840968000 | 349.540968000 | 119.700000000 | below |
| `wj06_outer_upper_right_cleat` | 229.840968000 | 349.540968000 | 119.700000000 | below |

Sixteen body spans are below 139.7 mm, none equal it within the 1e-6 mm
numeric comparison tolerance, and eight are greater. The maximum span is
284.618625260 mm for the two spine solids. This is the projection of each
spine onto canonical station N; it is not a station envelope exceedance.

The JSON contains each full STEP SHA-256, source-shape fingerprint, summary
hash, global bounds, exact-solid checks, mapped material-frame axes and source
bindings. It also lists linked bolt-axis/station IDs and any source-inventory
host-frame origins as unadopted datum candidates.

## Scope limits

This closes exact block-body geometry only. No selected or delivered bolt,
nut, or washer; tool or product envelope; tolerance envelope; or installed
hardware N bound is available. Those required parts of `ordinary_n_envelope`
remain pending. Candidate acceptance, an exception, native solve, fabrication,
and climbing release remain false.

## Reproduction

From the repository root, use the project's pinned CAD environment:

```sh
uv run --no-sync python \
  docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/\
current-block-n-envelope-attempt01/produce.py --verify
```

The narrow `--verify` rehashes the reviewed inputs, all exact STEP solids,
source maps and checked review documents, reconstructs the body projections,
and compares the result with `block-n-envelope.json`. The producer refuses to
overwrite an existing record.
