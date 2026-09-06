# Bounded observer replay of the original untied frame

Prepared, **not launched**. This is the existing finest original 2×8-foot100
baseline, not the redesigned joint candidate and not a strength approval.

The exact deck/context come from
`fea/results/full_frame_refinement/0.0625.tar.gz`, SHA256
`b7191366c224835aa6f790996671cc491ad3ae878cb9b797698a04d45e0b373b`.
Its `frame.inp` SHA256 is
`036c7e8a8303277848598275d1ea3e8c90abfe733a986d75dec515a0c9126b90`;
`frame.json` is
`b7a037d5538d7f842df9488ea436b26a91c301f4eee90fcccd3396145cbd65a2`.
The baseline completed 32 accepted increments in 108 iterations, 1156.324 s
under its 1200 s cap. Its archived launcher resolves `ccx` through PATH and
sets two OpenMP threads; the archived context does **not** independently bind
the historical container image. No historical image ID is retroactively claimed.

The prepared runner pins observer image
`sha256:8e84d8ad546cd98a861ceba3ccbf4c486b88f38a8b7e4c45f7784ace4cea21e1`
and checks the published build/source hashes, image manifest and actual binaries
before execution. Its canonical provenance is
`fea/mortar_kinematic_build/report.json`; the executable is
`/usr/local/bin/ccx-kinematic-observer-2.21`. This is the reviewed v2 packet,
including observed Dd/Bd kinematics, accepted physical contact forces and
virtual-work replay. No mutable alias is used for execution.

Execution plan: one byte-identical deck, unique evidence directory/container,
1500 s wall-time cap, 512 MiB stdout cap, two OpenMP threads, 6 GiB container
memory with no extra swap, and 2 GiB minimum free disk. Timeout or log-cap
termination kills only that named container and retains raw partial evidence.
Polling is every two seconds; the stdout cap can overshoot by one polling
interval's output. The original data/FRD are about 105/108 MB. Cube logging
suggests roughly 257 MB additional stdout for 610 nodes × 108 calls; this is
an estimate, not a bound on future nonlinear iterations or sparse entry counts.
The existing strict reader materializes the stream, so audit runs separately
with a 6 GiB address-space limit and 300 s timeout. Exhaustion is an incomplete
audit, never local-contact acceptance.

Independent inventory checks expand the actual deck's C3D10 slave surface
faces in contact-pair order LEFT, RIGHT, KICKER, sort each pair's node numbers,
and compare all 610 `(pair, slot, node)` identities in every observer call.
They reject missing/wrong/reordered pairs, extra ties and overlapping slave
nodes. This is separate from the strict reader's stream-internal inventory and
STA/accepted-call chronology checks. No geometry-derived union substitutes for
the launched-deck inventory.

Post-run comparisons retain every accepted call's local arithmetic results,
retain all accepted physical coupling records, compare all printed DAT displacement/reaction coverage and values against the
archive, compare complete accepted STA history, and replay unchanged global
0.1 N/component and 1 Nmm/component gates. Differences remain explicit.
The physical force audit additionally resolves all twelve C3D8 S2 master nodes
from the actual launched deck. It rejects physical nodes outside the disjoint
slave/master memberships and checks every coupled node's accepted observer
displacement against its DAT endpoint before computing moments. Tolerance is
half the last printed decimal unit plus 1e-12 mm arithmetic slack, not a model
accuracy allowance. Moments use original coordinates plus the checked
full-precision observer displacement. Each patch reports applied slave/master
forces and moments separately, their summed imbalance, and every surface node
absent from coupling columns; it does not assume that every face remains closed.
Separately, each massless numerical ground brick is checked using its applied
master contact force/moment plus the four actual bottom-node DAT reactions at
original plus DAT-displaced coordinates. Fixed-bottom displacement must remain
within the existing 1e-9 mm guard. The resulting body balances are reported
against the unchanged 0.1 N/component and 1 Nmm/component diagnostic thresholds.
Pair cancellation is not a substitute for this independent reaction balance;
failed body checks remain explicit, not a joint-demand qualification.

V2 reconstructs weighted gap/tangential kinematics and physical forces from
observed matrices and state. The matrices, initial weighted gap and frozen bases
remain observed inputs: segmentation, weak-law acceptance, real floor properties
and joint capacity remain unvalidated. Nonzero solver exit, runtime/output stop,
failed audit, changed printed outputs/history or failed existing global gates
produce a nonzero CLI exit while preserving available evidence.

Execution provenance is fail-closed: all nine executing project source files
(runner and its complete import-time dependency closure) are snapshotted before
launch. Live file hashes, imported-module origins/import-time hashes, snapshot
bytes and the prelaunch digests must agree before the audit subprocess, at its
entry, and after its calculations. A newly executable `fea/__init__.py` is
rejected. The portable audit does not call the dormant CAD/integration helpers;
their host packages are outside this executing closure. Changed sources require
a separately reviewed replay, not silently relabeled old evidence.

Budget checks occur both while running and after wait returns, including a
process that finishes before the first poll. SIGINT/SIGTERM and monitor exceptions
trigger inspection of only the unique launched container; a running container
is killed, while an already stopped/removed one is not. Inspection also follows
every ordinary Docker-client exit: client completion alone cannot establish
container termination. A surviving container is killed and inspected again;
this is rejected partial evidence even if the client returned zero. Cleanup failure retains
the container name/client PID and an explicit unconfirmed-termination status.
An uncatchable SIGKILL or host failure cannot guarantee cleanup. Terminal reports
hash all available raw solver files and all available audit outputs (including
partial/rejected results and the audit log). None of these outcomes authorizes
an automatic rerun.

The audit is a separate process session with a 300-second wait limit. Parent
SIGINT/SIGTERM handlers terminate and reap only that audit child and persist
available partial artifacts and hashes. Signal delivery is briefly blocked
around child-handle assignment and final report persistence to close those
interruption windows. Tests invoke the real audit wiring with compact patched
provenance/replay fixtures: accepted-call IDs are joined through STA endpoints
to actual DAT parsing, displacement checks and physical moments. Independent
printed-field, history, global-gate and ground-body-gate corruptions each reject
while retaining diagnostic artifacts. These tests do not replace the real
source/deck or numerical replay regressions.

Solver-client creation uses the same signal mask: its handle and PID are
assigned before queued stop signals are delivered. A still-live client is
stopped and reaped before an absent named container can be called terminal.
Solver terminal-status construction, raw-output hashing and report persistence
are inside the monitor's final masked section, so there is no unprotected
handoff leaving the report RUNNING during large-file hashing. The audit wiring
regression explicitly asserts both soft and hard `RLIMIT_AS` limits are 6 GiB;
omitting the resource-limit call fails that test.

Runner: `python -m fea.mortar_frame_observer` after explicit launch release.
Tests: `uv run pytest tests/test_mortar_frame_observer.py` (no solver).

Prelaunch verification: 43 focused tests and Ruff passed; the immutable-image
manifest and actual binary hashes were checked. A final independent correctness,
testing and architecture review pass found no substantial remaining findings.
These are runner qualification results, not evidence that the frame solve has
been executed or accepted.
