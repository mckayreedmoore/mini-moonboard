# Architecture/result review: affine annulus

**Scoped conclusion: PASS for this one affine elastic software-method
fixture.** The frozen-output audit reproduces from the recorded `model.dat`,
and the run provenance, parent controls, and terminal cleanup records agree.
The prior architecture condition was caller-enforced; the parent readiness
record supplies those controls for this run. This does not mean the unchanged
runner enforces freeze-wide limits.

## Provenance and run controls

The input freeze remains SHA-256
`093ab967c805858b33e3d0530cadab25625cc3b8c69f696d3c39885302fa6817`. I
rechecked its seven frozen artifacts, nine copied source snapshots, and nine
live source hashes. Parent readiness binds that freeze, records zero prior
runs for it, and binds the three pre-run reviews to their recorded hashes.
Its `ready_for_scoped_native_run` is true, with one CPU, 1 GiB, a 60-second
timeout, and stop-after-one-launch controls.

Run ID `wj-washer-annular-affine-20261001-a01` is consistent in readiness,
authorization, execution, and the sole ledger row for this freeze. The
authorization and execution record the same caller command: pinned image
`sha256:31336f517557f5dd5f97d85b1e6e15947fd1c10b44edc1364dbba4c1a5ab6c38`,
`--cpus=1`, `--memory=1g`, `OMP_NUM_THREADS=1`, and `timeout 60s`. The run
returned zero in 0.286 seconds. Its output hashes still match the files on
disk. The ledger records one of one launches consumed and a terminal run; its
slot is idle. The execution record confirms the container terminated. The
solver log says “Job finished,” and the status file contains one accepted
increment. These records satisfy the parent-side bounds and serialization
conditions for this attempt; they do not upgrade enforcement in the shared
runner.

## Result and claim boundary

I independently reran the local read-only affine parser against `model.dat`.
Its JSON exactly matches `frozen-output-audit.json`. The parsed output hash is
`32e09011944c5c31fb694040324d52a58241c87746628ebd7c16867faf2825b5`; the
audit hash is
`3f0225a5d9f6e7b70ee914be2b9b4afc181a844e5281780a22f54eddbabb7095`.
The reported `PASS_AFFINE_ELASTIC_METHOD_FIXTURE` covers all 1,536 stress
rows, affine boundary and free-interior displacements, top and bottom reaction
wrenches, global reaction closure, and elastic energy. Maximum stress error
is `2.96e-14 MPa` against a `0.00025 MPa` limit; reaction, displacement,
closure, and energy gates also pass. The runner and solver records retain
`mechanical_acceptance: false`.

This result is limited to the hypothetical `nu = 0` C3D10 affine patch and its
software method gates. It provides no contact-method result, washer or wood
property, local washer-stress recovery, resistance, candidate acceptance, or
physical-build evidence. Parent readiness keeps `contact_job_authorized` false.
The existing `parent-result.json` still says `result_review_pending: true`;
this file records the scoped review conclusion without changing that parent
record.

## Durable record hashes

- Parent readiness: `3b28b4c697832301feb486ecf1133900b6e8b6e9398787f6f671e0e99bdd1500`
- Authorization: `f4ff1a6d98538dd2ae305abf0fa39086a263d11a2a475aea3f7a241c326ea85b`
- Execution: `2bfb59d1ad2762527e44286bf783f13efac59723d1c9958deb5b3ad5a167453f`
- Parent result: `a1f5beb7d2d0e67f53e1055304f26211ba6a667304be871720fc712e185d428a`

