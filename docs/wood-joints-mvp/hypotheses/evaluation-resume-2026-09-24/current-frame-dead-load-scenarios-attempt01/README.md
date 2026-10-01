# Current-frame dead-load scenarios — attempt01

## Result

This source-bound contract records current modeled-body gravity and nine
analytical placements of the separate 25 kg accessory allowance for
`led-clearance-2x6-runner-seated-blocks-v1`.

- Modeled inventory: 778 rows, 224.4207767 kg.
- Additional allowance: 25 kg, represented once in each scenario.
- Hold placement reference: equal-weight centroid of 142 current climbing-face
  axes, `(-17.895775, 704.722765, 1132.633675) mm`.
- Electrical location proxy: sum-volume centroid of all 263 current modeled
  light and wire bodies, `(-9.371857, 663.284688, 1148.908767) mm`.
- Scenarios: three electrical/hold mass splits and six named hold-axis endpoint
  placements. Each is paired with all six applied climber cases for 54
  resultant arithmetic checks.
- Contract digest: `6161d0ed6c71013840856411ce7c5a890962410f9b7a6e1aaf536e2dfd43ba10`.

The contract references and validates all 778 source gravity rows as the load
basis; downstream solver mapping must preserve their application or document
an equivalent mass transfer. Combined case wrenches are cross-checks only;
they do not replace distributed gravity or map forces to connections.

## Limits

Accessory splits and locations are scenarios, not measured masses or an
observed installation. The electrical centroid is a volume-weighted proxy for
nominal separate CAD bodies; overlapping bodies count once per body, with no
Boolean union. It is not actual equipment mass. Hold placement uses a face-
projected reference with zero added outward CG offset; actual hold CG is
unknown. T-nuts and modeled fasteners already in the 778-row inventory are
excluded from the allowance to avoid double counting.

This artifact does not build or map the full-frame solver model, define
connections or boundary conditions, establish reactions or demands, or show
mechanical acceptance. The attempt02 full-frame manifest remains
inventory-complete and inputs-not-ready. All solve, acceptance, and release
flags in this artifact remain false.

## Reproduction

From the repository root:

```sh
scenario_dir=docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/
scenario_dir+=current-frame-dead-load-scenarios-attempt01
uv run --no-sync python "$scenario_dir/produce.py" --verify
```

Verification rebuilds the nominal electrical shapes in memory, checks pinned
inputs, runtime JSON and every loaded project geometry module, then compares
the source-derived payload to the frozen JSON. To create a new attempt, copy
the directory and update its identity; `--write` intentionally refuses to
overwrite an existing artifact.
