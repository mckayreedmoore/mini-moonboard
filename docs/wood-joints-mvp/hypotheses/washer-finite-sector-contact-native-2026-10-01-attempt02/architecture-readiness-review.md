# Architecture readiness review — attempt 02

**Decision: TECHNICALLY READY for one bounded native method run** of freeze
`87894949d0f9aa45ca479fa290fb2ae8c354884d290b9ac0e13e2a902522c8aa`.
This is readiness for the frozen software fixture only. It is not a contact
capacity, material, candidate, or physical-work acceptance.

## Scope and identity

This review covers the immutable deck and expected record, coordinates,
result parser, pinned source/runtime/manual records, prerequisite-affine
binding, and launch/result ownership. It did not run CalculiX, Docker, CAD, or
the packet tests, and did not inspect the prerequisite review findings.

The assigned freeze SHA matches. The seven files in `files_sha256` match the
freeze record: deck, model/oracle record, coordinate map, verifier, pair-output
parser, source pins, and preparation record. The prerequisite affine freeze,
output-audit, and parent-result hashes also match their referenced files.
The freeze snapshots the relevant generator, runner, solver-profile, method,
and prerequisite artifacts. This binds the method packet to the exact
affine-result chain without importing its conclusions into this contact run.

## Readiness basis

The deck represents two separate C3D10 bodies with matched annular contact
faces, frictionless face-to-face penalty contact, and a finite eccentric
pressure patch on the upper body. Its lower bottom is constrained in all three
translations; the upper-body in-plane translation and spin gauges are explicit
in the deck. The pressure patch uses 16 TRI6 faces and 45 nodes. The model
record distinguishes the hypothetical isotropic diagnostic receiver and
finite penalty from any wood or material-compliance claim. These are coherent
inputs for a load-transfer and output-method check.

The oracle and verifier use current face coordinates to reconstruct the
follower-pressure wrench with the pinned CalculiX 2.23 three-point TRI6 load
rule. They also report the separately computed six-point integral comparison
under its frozen tolerances. The contact parser extracts the pinned
CF/CFN/CFS force and origin-moment rows; the result audit compares contact,
gauge, and ground wrenches and checks upper-body and whole-model closure. Gauge
forces are accounted for separately, and free-z gauge RF is not misused as a
reaction. This is an appropriate software-resultant check; it does not test
local contact pressure or stress.

The manual PDF and solver profile hashes are frozen. The source pins record the
2.23 binary, image, source archive, relevant source-member hashes, and manual
sections used for the load and output semantics. The shared runner snapshots
its own source and checks live source, manual, image, and binary identities at
launch. The source and HTML archives are referenced under `/tmp` rather than
stored in this attempt. Their hashes preserve artifact identity, but the
archive bytes are not a durable copy; retain those bytes if later audit must
replay source inspection after the temporary files are removed. This does not
block this bounded run given the frozen member hashes, manual, and runtime
identity.

## Parent-owned launch and result conditions

The technical review is complete before the parent receipt. Do not make this
review depend on that receipt; the receipt should record this review and the
other independent reviews against the same freeze, then make the launch
decision.

The runner serializes through the shared ledger and refuses a busy slot,
reused run ID, or an attempt directory that already has an execution record.
Its API nevertheless accepts caller-supplied time and memory limits and does
not itself enforce the freeze's one-launch-per-freeze count. Before launch,
the parent must confirm an idle shared slot, no prior launch for this exact
freeze, no competing heavy run, and pass exactly 60 seconds, 1 GiB, and one
CPU. Use one fresh run ID. Preserve any timeout, solver error, or incomplete
cleanup as the single consumed attempt; do not retry.

The verifier accepts paths for the expected record, coordinates, and `.dat`
file, and its printed audit does not carry their hashes or the input-freeze
SHA. Therefore the post-run parent result must bind the exact freeze SHA,
`execution.json`, solver output hashes, `model.json`, `model_coordinates.json`,
both verifier source hashes, and the resulting audit JSON hash. Invoke the
verifier only on those frozen inputs and that run's output. This is an output
provenance duty, not a reason to delay the present input-readiness review.

A passing run may establish only that this frozen hypothetical fixture
transfers the prescribed resultant through the modeled contact pair and that
the pinned output path closes its stated force and moment checks. It cannot
establish local pressure or stress, washer bending, crushing, plasticity,
partial-seat resistance, actual wood or product behavior, joint resistance,
candidate acceptance, fabrication readiness, or climbing release.
