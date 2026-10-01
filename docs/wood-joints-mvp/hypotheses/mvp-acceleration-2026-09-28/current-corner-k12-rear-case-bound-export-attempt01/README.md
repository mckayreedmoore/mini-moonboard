# K12-rear case-bound corner demand export

This packet projects one newly authenticated `k12-rear` response into the
existing left-outer-corner BG001/BG003/BG045 map. The fresh native run used the
SPR489 direct-master input variant; the exporter consumes the sealed response
audit, the independent 50-body/global audit, and the parent terminal
assessment. It does not run CalculiX or transfer forces or floor states from
another case.

The source-bound report has seven increments at load factors 0.1, 0.2, 0.3,
0.45, 0.675, 0.925, and 1.0. Each increment retains all 338 mapped corner
interfaces, 232 contact rows, signed member force vectors, owner-datum
wrenches, contact/member paths, and the corner five-body balance. It maps six
physical bolts, eight separate lateral-plane actions, six outer-seat ties, and
12 washer seats. The six new block bolts remain within the 92 new axes; the
twelve retained LEG/FLOOR-RUNNER arrangements and 66 Hillman panel/kicker axes
remain separate.

For the two affected original left-leg bolt axes, all four mapped interface
actions per increment are repeated in
`corner-demand-report.json` under
`onward_transfer_scope.per_increment_action_rows`. At load factor 1.0, the
recorded force-on-first vectors are:

| Source action | Force on first (N) |
| --- | --- |
| `lumber_leg_bolt_left_1/outer-seat-axial-tie` | `[-241.9659, 0, 0]` |
| `lumber_leg_bolt_left_1/wood-interface` | `[0, -23.39143, 298.0269]` |
| `lumber_leg_bolt_left_2/outer-seat-axial-tie` | `[-530.5748, 0, 0]` |
| `lumber_leg_bolt_left_2/wood-interface` | `[0, -143.7603, 334.2164]` |

The report is numerical demand input for conditional joint checks on this
exact K12-rear response. It does not establish resistance, complete-joint
acceptance, design qualification, floor friction or anchorage, fabrication
approval, or climbing release. Existing resistance on the retained original
axes was not reopened.

The static preflight records the direct-master attempt02 model/deck, SPR489
method review, fresh six-case load-register record, rejected 23/77 floor
screen, and unchanged corner contract/map and legacy mapper. Projection output
was written only after the exact K12 response audit passed all seven gates,
the parent audit passed all 50 physical bodies and global balance at all seven
increments, and the parent terminal assessment marked this case usable for
conditional checks.

Reproduce from the repository root:

```sh
uv run --no-sync python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-corner-k12-rear-case-bound-export-attempt01/project_k12_corner.py --preflight
uv run --no-sync python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-corner-k12-rear-case-bound-export-attempt01/project_k12_corner.py --export
uv run --no-sync python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-corner-k12-rear-case-bound-export-attempt01/project_k12_corner.py --verify
```

`--preflight` does not read response forces. `--export` fails closed unless
the parent-owned run packet, exact direct-master response, all-50 audit, and
terminal assessment still match the pinned inputs and pass. `--verify`
revalidates those gates and compares a fresh seven-increment projection with
the saved report.
