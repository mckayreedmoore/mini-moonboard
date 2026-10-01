# A12-forward selected-floor input proposal, attempt 10

This packet prepares one case-bound 37-cell floor-support proposal for
`a12-forward`, using immutable adapter attempt 02. The selected set is the
zero-u 711 interval classification that was strictly positive at all seven
printed states of the source-bound, rejected 31-cell A12-forward attempt 02.
That prior run is the direct diagnostic lineage only; its response is not a
response for this proposed 37-cell input. The original A12-forward all-bearing
model remains the source authority for geometry, laws, loads, and materials.

The attempt10 replay rehashed all 40 original source pins and reproduced the
diagnosis. The repeated classification is 37 positive, 63 separated, and no
ambiguous cells at every printed state. Three of the 31 originally selected
cells separate, while nine cells formerly inactive classify positive.
SPR1026 remains selected in the rejected source input and classifies as
separated at all seven states. The screen carries classification intervals
only; force and RF values are withheld.

The proposed input has 74 active tangent rows and 126 inactive rows. It keeps
the 100 normal SPRINGA laws, geometry, load, and material inputs bound to the
A12-forward all-bearing controls. The independent serialized-deck audit and
independent case-context audit both pass. Their details and hashes are in
`a12-forward/parent-serialized-input-audit.json`,
`a12-forward/parent-case-context-check.json`, and
`input-evidence-pins.json`.

This remains a rejected diagnostic support proposal. It establishes no
selected-branch response, floor qualification, accepted force, corner demand,
or mechanical acceptance. No freeze or native solve was created. Parent owns
readiness, freeze, serialized execution, and final validation.

The source replay and screen projection are prepared by:

```bash
uv run --no-sync python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-springa-case-bound-floor-input-adapter-attempt10/project_a12_forward37.py
```

The immutable input adapter is
`current-springa-case-bound-floor-input-adapter-attempt02/prepare.py`; its
ten explicit source hashes and emitted hashes are recorded in
`a12-forward/source-pins.json`. The independent audits were invoked with the
case-bound checker and this packet's context checker. Their scripts do not
execute the solver.
