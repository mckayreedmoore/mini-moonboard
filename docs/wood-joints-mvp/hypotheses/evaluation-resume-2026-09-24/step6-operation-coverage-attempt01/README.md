# Step 6 operation-coverage attempt 01

Diagnostic register for `led-clearance-2x6-runner-seated-blocks-v1` (reviewed repository identity
`b1e8707d`). The selected candidate remains
`compact-floor-flush-development`; this is a separate development lane.

`operation-coverage.json` contains 575 joined operation records: 92 candidate bolt stacks,
12 retained frame-bolt stacks, 66 Hillman axes, 142 T-nut corridor rows, 132 LEDs and 131
modeled wire segments. A separate 24-entry grouping table assigns the 92 candidate axes to
their current blocks. The table records 96
block-axis links because an axis can serve multiple block receivers. Input documents, the 405
service asset files, and the three embedded current electrical replacement meshes are pinned
by digest.

## What the register records

- Candidate and retained bolts keep install, turn, counterhold, retrieval, withdrawal and
  reverse-assembly statuses separate. Motion envelopes and current-revision wrench poses are
  proxies; the wrench profile is unselected. They do not establish real-tool access, physical
  fit, capture or support.
- The 66 Hillman rows preserve the 58 fixed and eight moved axes. Their current receiver
  envelope check clears finished receivers; driver access, embedment, support, and reversal
  remain unverified.
- T-nut rows join each modeled baseline asset to its separate provisional corridor envelope.
  The corridor envelopes were excluded from the retained access screen as non-installed
  projections. G6 and G12 findings remain unresolved hold-product envelope conflicts.
- LED and wire rows preserve route order and use WJ18 only for panel-ownership topology.
  The current G1/G2 hole checks are narrow nominal checks; service feeding, capture and
  restoration are not proven. Fixed display-solid overlaps do not prove a flexible cable is
  physically blocked.

The 139.7 mm ordinary local-N disposition remains unresolved. No historical 28-body/104-axis
records, local-N results, or synthetic-wrench results are used. This artifact closes source
reconciliation and coverage mapping only; it does not close Step 6 fit/use readiness, mechanics,
fabrication, or climbing release.

## Reproduce and verify

```sh
cd docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/step6-operation-coverage-attempt01
python3 produce.py --write
python3 produce.py --verify
```

Machine JSON SHA-256: `1722ff0f0a438934df15e6285947bdbf3b34f8d99a1e94e30403d756ab33d7ae`.
