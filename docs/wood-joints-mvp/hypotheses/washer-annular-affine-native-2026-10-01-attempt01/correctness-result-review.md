# Independent affine result review

Reviewed 2026-10-01. **Current method result: `PASS_AFFINE_ELASTIC_METHOD_FIXTURE`; no substantial findings.** This result covers only the frozen C3D10 affine elastic known-answer job. It is not mechanical acceptance, candidate resistance, or contact-method acceptance.

## Run and artifact identity

The run is `wj-washer-annular-affine-20261001-a01`, bound to freeze SHA-256
`093ab967c805858b33e3d0530cadab25625cc3b8c69f696d3c39885302fa6817`. Frozen
inputs still match their recorded hashes; the executed `model.inp` digest is
`36333a78ef54299cefc1fbb4ca0449ec889ce8a174b3dfc0c5ce8d3b17e93e95`. The raw
`model.dat` digest is
`32e09011944c5c31fb694040324d52a58241c87746628ebd7c16867faf2825b5`; the
`native.stdout` digest is
`b7b45f4c3cb68c3c663fbe2c599d8d4845dc973c8cc6decd40d477b59d6c49d0`.
`execution.json` is pinned as
`2bfb59d1ad2762527e44286bf783f13efac59723d1c9958deb5b3ad5a167453f`, and
`frozen-output-audit.json` as
`3f0225a5d9f6e7b70ee914be2b9b4afc181a844e5281780a22f54eddbabb7095`.
Every output digest listed in `execution.json` matched the corresponding file.
The parent result's execution and audit hashes match those files. The run-ledger
entry binds the same run ID and freeze, pins the authorization and execution
record, and records one launch consumed in terminal state with native exit 0.
The authorization hash is
`f4ff1a6d98538dd2ae305abf0fa39086a263d11a2a475aea3f7a241c326ea85b`.

The recorded call used the pinned image, one CPU, 1 GiB, and a 60-second
timeout. It returned 0 in 0.2864 seconds, the container was confirmed terminal,
`native.stderr` is empty, and `native.stdout` reports `Job finished`. The
solver reports 800 nodes, 384 elements, four integration points per element,
zero applied nodal or distributed loads, and the single static increment at
time 1.0. No rerun was made. At review time `parent-result.json` still marked
`result_review_pending: true` and had SHA-256
`a1f5beb7d2d0e67f53e1055304f26211ba6a667304be871720fc712e185d428a`; this file
records the independent result review.

## Raw result checks

I parsed `model.dat` directly and recomputed the quantities from the frozen
`model.json` and coordinate map. There is one final-time block at 1.0 for each
requested output. Displacements and RF contain exactly the 800 frozen node IDs;
stress contains 1,536 rows, exactly four integration points for each of the
384 frozen element IDs.

| Check | Raw result | Frozen limit | Result |
|---|---:|---:|---|
| Maximum boundary displacement-field error | `2.7105e-20 mm` | `1e-8 mm` | Pass |
| Maximum free-interior displacement-field error | `2.7592e-20 mm` | `1e-8 mm` | Pass |
| Maximum stress-component error | `2.9523e-14 MPa` | `0.00025 MPa` | Pass |
| Top reaction-force error | `0.000172282 N` | `0.015695044 N` | Pass |
| Bottom reaction-force error | `0.000172282 N` | `0.015695044 N` | Pass |
| Top origin-moment error | `1.84e-13 N·mm` | `0.02 N·mm` | Pass |
| Bottom origin-moment error | `3.55e-13 N·mm` | `0.02 N·mm` | Pass |
| All-boundary force closure | `3.98e-13 N` | `0.02 N` | Pass |
| All-boundary moment closure | `1.66e-13 N·mm` | `0.05 N·mm` | Pass |
| Internal-energy error | `2.8521e-8 N·mm` | `1.1032e-6 N·mm` | Pass |

The directly summed top RF is approximately `-1469.504208 N` in z and the
bottom RF is `+1469.504208 N`, with the frozen analytical references
`-1469.504380282 N` and `+1469.504380282 N`. Their signs oppose as required;
their origin moments are near zero. The raw total internal energy is
`0.1102128 N·mm` versus the analytical `0.110212828521 N·mm`. The maximum
free-interior RF norm is `6.24e-14 N`, consistent with the absence of applied
loads and with those nodes being unconstrained.

The pinned CalculiX 2.23 manual's RF discussion (`node212.html`, SHA-256
`a6a7ae750b2b0b62ae690952865ba3dcc219cda6ab56a3929df82d249f1015c6`) and
`*NODE PRINT` documentation define RF as external force including applied and
reaction contributions. Because this deck has no applied loads, the constrained
node RF values represent reactions. The raw output uses the expected global
`U`, `RF`, stress, and total internal-energy headings and identities.

## Scoped conclusion

The frozen displacement, stress, reaction-wrench, moment, closure, and energy
gates pass on the raw solver output. This supports the specified affine C3D10
linear-elastic patch and its output extraction only. `parent-result.json`
continues to correctly state `mechanical_acceptance: false`,
`contact_method_accepted: false`, and `candidate_resistance_accepted: false`.
The separate contact job remains unauthorized. This result does not establish
washer pressure behavior, bending or local stress, yield, actual material
properties, wood crushing, joint resistance, or candidate acceptance.
