# Knee-bridge planning-gravity operators

**Parent calculation complete: two audited elastic quotients pass; gravity operators ready for the six-case replay. Proposal remains unadopted.**
[Producer](knee-bridge-gravity.py) API: `build(output)`, with a fresh immediate
child of `rawlocal/knee-bridge-gravity/`. Import is inert. Producer SHA-256:
`b1c27fb57cd3a275c6629efaec32ec036076252e7b80ba679440c7ee8472be84`.

Frozen integration attempt02: manifest
`1744bb616354159c06694e99fb239251578dba3a6e860da5391dae19b5d7026c`,
receipt `8a2813419289bee46e2e0985ab702a602a8ff3a0d3aacdd43d1aad841c92c8df`,
producer `46b6966fe215408540acf636afa7e7638c2679d825f687c23eedac47c706ac46`.
Original operator assessment, its consumed native matrix/DOF/model and helper
pins, fit setup, order and integration artifacts are authenticated before and
after execution. Earlier source maps remain provenance; original records are
never rewritten or repinned.

The four stacks use the order's declared 6.5-inch nominal shaft, full hex head,
nominal-diameter bored hex nut and two annular washers. Their twenty geometric
centers come from canonical end seats and the fit setup's installed geometry.
Four 7.5-mm through-cylinder removals act at the canonical bore centers.
Densities remain 7,850 kg/m³ steel and 600 kg/m³ wood. Planning mass must
reconcile to `+0.24795882906138145 kg`; it is not measured hardware mass.

The implementation uses the current physical spine nodes and existing
`distribute_wrench`, `rigid_basis`, `factor_bordered` and
`solve_quotient_chunk` definitions. It factors only the two original native-K
spine quotients, with one gravity-delta RHS each and unchanged audit gates.
It retains the full geometric force/moment in F and rigid W while updating
elastic e through current B times the audited displacement. A rejected
quotient emits a STOP assessment/receipt and no updated operators; no rigid-only
replacement is available. Planning mass comparisons use `1e-12 kg`, global
force/moment comparisons `1e-5 N / Nmm`; quotient limits are unchanged.

H/D arrays, B bytes, connector rows and constitutive k remain the declared
**FILLED-BORE gross elastic approximation**. All live F/e/W columns remain
bitwise equal, retaining 250 lb × 2, signed 300 N and the 100-mm lever. Only
unfactored gravity columns change. The replay must use the new modeled mass
and `(new_mass + 25) / new_mass` deadfactor, preserving the proportional
25-kg equipment convention. Actual changed-hole stiffness, global displacement
compatibility, joint acceptance and physical release remain unqualified.

On success, `operators.npz`, `B.npz`, `row-identities.json`, `model.json`,
`model-inputs.json` and `operator-assessment.json` live directly in the output
child. The assessment binds the operator-ready artifacts through
`output_sha256`; `receipt.json` also binds the assessment. `inputs.json` and a
producer snapshot retain preparation provenance. The explicit
`NUMERICAL_SEED_ONLY` record pins old comparison/response files as initial
guesses, supplies the target's true mass/deadfactor, and transfers no force or
global compatibility acceptance. No frame solve or seed-result files are made.

Parent command from the repository root; the two quotient solves have at most
five existing-factor refinement corrections each:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 .venv/bin/python -B \
  docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/knee-bridge-gravity.py \
  --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/knee-bridge-gravity/attempt01
```

The parent ran the two elastic delta calculations: both pass their unchanged
quotient gates with zero refinement corrections. All 37 source pins and nine
receipt artifacts match. Global gravity force/moment recovery errors are below
0.000000001 N / 0.000000003 Nmm; B/row bytes, H/D arrays and all live columns
remain exact. New modeled mass is **225.197914143181 kg**, deadfactor
**1.111013461626**, net planning delta **+0.247958829061 kg**. The raw added
gravity is 2.431645451 N downward, with its full component-position moment.
No software tests, review loop, native/CAD/frame solve or helper pipeline ran.
Existing evidence stays active; generated operators belong only in the ignored child.

| Artifact under `rawlocal/knee-bridge-gravity/attempt01/` | SHA-256 |
| --- | --- |
| `operators.npz` | `7877699053a8285b77621ca0cfcb7b09d22b19e5c20729c193e1e5c3f4840e4f` |
| `operator-assessment.json` | `ce69ba58e3c6265d31ab0dfdec1ffac4c019b93fc1106c8f9677ed9b5b2c3f95` |
| `receipt.json` | `315c16d2a592b12dcd0160af47f9d4bababb6afaf54c6c74ddcbd41e01d45b6c` |
