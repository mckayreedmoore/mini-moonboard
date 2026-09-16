# Selected flush-top commercial-angle ledger

Candidate: `compact-spliced-flush-top-development`.

This deterministic ledger reads six authenticated report archives and applies `fea.current_response_resistance.angle_comparisons`. It runs no native solve and changes no archive.

| Case | ML24Z | SDS25112 | Listed interaction max | Positive unlisted F2 max, N | Loaded-flange force-parallel couple max, N·m |
| --- | ---: | ---: | ---: | ---: | ---: |
| `a12-left` | 24 | 144 | 0.530806 (`clip_single_top_left_1`) | 240.600 (`clip_angle_base_left`) | 16.050 (`clip_angle_base_left`) |
| `a12-rear` | 24 | 144 | 0.558082 (`clip_single_top_left_1`) | 100.940 (`clip_angle_base_left`) | 10.601 (`clip_single_top_left_1`) |
| `a12-forward` | 24 | 144 | 0.458101 (`clip_single_top_left_1`) | 75.050 (`clip_angle_base_left`) | 9.087 (`clip_horizontal_lower_left_1`) |
| `k12-right` | 24 | 144 | 0.579743 (`clip_single_top_right_2`) | 240.815 (`clip_angle_base_right`) | 16.340 (`clip_angle_base_right`) |
| `k12-rear` | 24 | 144 | 0.615121 (`clip_single_top_right_2`) | 103.694 (`clip_angle_base_left`) | 11.285 (`clip_horizontal_lower_right_2`) |
| `a1-rear` | 24 | 144 | 0.280940 (`clip_horizontal_bottom_left_1`) | 9.459 (`clip_split_header_center_right`) | 5.862 (`clip_horizontal_lower_left_1`) |

## Six-case envelope

- Listed interaction maximum: **0.615121** at `k12-rear` / `clip_single_top_right_2`.
- Positive unlisted F2 maximum: **240.815 N** at `k12-right` / `clip_angle_base_right`.
- Absolute loaded-flange force-parallel couple maximum: **16.340 N·m** at `k12-right` / `clip_angle_base_right`.

## Completion gate

**OPEN.** Listed interactions do not qualify positive F2 separation in bearing-like installations. They also do not supply an applicable complete-wrench resistance for loaded-flange couples. Ledger is demand evidence, not construction release or design qualification.

The [online product/options review](compact-spliced-flush-top-angle-options.md) found no catalog-only larger ML angle or screw substitution that closes those actions. It records the smallest completion routes and a ready-to-send technical question.

Full per-case, per-connection values and authenticated input hashes are in [compact-spliced-flush-top-angle-ledger.json](compact-spliced-flush-top-angle-ledger.json).
