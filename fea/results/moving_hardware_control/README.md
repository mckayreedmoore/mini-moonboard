# Moving-hardware control evidence

`first-input-rejection.tar.gz` preserves the original `quiescent-an9hdwot`
attempt and its `control-n9loh3l6` preparation, the complete eleven-body
locked-thread geometry/STEP/source export, its `mesh-otcxe8mb` mesh and source
snapshots, and the recorded mesh runtime. Original files are unmodified.

The native executable rejected a `*NODE` coordinate field and exited **201**.
The DAT is empty and STA contains only headers: **zero accepted states**.
The owned container was stopped with exit 201 and removed successfully.
This is an input-format failure, not a contact or structural result.

The archive contains original freeze manifests, raw input/output, launcher,
build manifest, preparation source closure, CAD source closure and STEP files.
`first-input-rejection.json` binds the archive SHA-256. `members.json` inside
binds every archived member. The retained publisher and mesh-parser source
are provenance copies and are not executed during replay.

Run `uv run pytest tests/test_moving_hardware_control_publication.py -q` to
verify original linked hashes, eleven disjoint mesh body inventories, deck
identity and terminal input rejection without Docker, CAD or a solver. This
does not recompute CAD geometry, mesh Jacobians, contact fields or capacity.
The source-derived reference mass remains a preparation result, not a native
mass comparison: no native numerical state exists for this attempt.

Any corrected attempt must be published separately; this archive is not
overwritten or retrospectively relabeled successful.

## Second attempt: bounded timeout

`second-quiescent-timeout.tar.gz` preserves `quiescent-mgxeu8y1` and its
`control-qci96sn1` preparation separately. Its report binds the archive hash.
The archive's `references.json` binds the original first archive and each
unchanged shared member by SHA-256, avoiding duplicate geometry and mesh data.
Both archives are required for complete replay; the first archive is unchanged.

The corrected coordinate-format deck reached one accepted increment at
**1e−8 seconds**, followed by ten recorded unsuccessful attempts at increment
2, cutting back to 1e−11 seconds. The bounded process exited **124**, and the
captured owned container was removed successfully. The recorded inner timeout
was 120 seconds; the launcher allowed 140 seconds for observation.

This is **partial, unqualified output**, not a completed contact response or
evidence of a physical structural failure. Publication tests check the original
hash chain, partial accepted-state history, terminal state and cleanup, not
numerical equilibrium or contact-energy correctness. Any separate partial
numerical diagnostic must retain these limitations.

## Third attempt: catalog-clearance quiet control

`third-catalog-quiescent.tar.gz` is a separate self-contained archive of
`quiescent-ggs6anor`, preparation `control-muorg377`, all eleven STEP bodies
and source snapshots from `stitch-joint-geometry-df3e0965`, and its
`mesh-7amycoem` mesh, metadata, frozen mesher sources and recorded runtime.
The first and second archives and reports remain unchanged.

This quiet-only case uses the provisional 10.9982 mm washer bore, not the
original zero-clearance bore. Its process hit the recorded 120-second limit
and exited **124**, with successful owned-container cleanup. STA records
**19 accepted increments**, ending at **2.00705e−8 seconds**, short of the
requested 2e−6 seconds. There are no unsuccessful-attempt rows in this STA;
shrinking accepted increments must not be mislabeled rejected cutbacks.

The archive report and portable tests verify provenance, raw inventories,
the catalog variant, partial STA history and terminal/cleanup records. They
do not certify response completeness, quiet behavior, equilibrium, contact
energy, material resistance or physical structural failure. An accepted
increment is not equivalent to a qualified numerical result.

## Fourth attempt: DIRECT stationary control

`fourth-direct-quiescent.tar.gz` is self-contained and preserves
`quiescent-ffkg77qe`, preparation `control-r3gnwd2c`, and the same complete
catalog-clearance geometry and mesh evidence used in the third attempt.
The prior three archives and their reports remain unchanged.

The frozen deck specifies implicit `DIRECT`, twenty fixed increments of
1e−7 seconds, and a total duration of 2e−6 seconds. The frozen solver cap is
180 seconds and the outer observation cap is 200 seconds. Native execution
finished and exited **0**; STA records all **20 accepted increments** through
2e−6 seconds, and owned-container cleanup succeeded.

This publication certifies the original hash chain, terminal execution and
fixed-increment STA schedule only. It does **not** establish quiet behavior,
contact-field completeness, energy or momentum consistency, contact-law
qualification, material resistance or permission to build or climb.
Those require a separate numerical audit of the retained output.

## Partial numerical diagnostic

[Retained report](diagnostics/partial-quiescent-gb9rn5dl/report.json) and its
adjacent source snapshot reproduce four failed first-state gates: bolt/nut
speed, washer speed, washer-bore penetration, and recorded contact energy
alone. The frozen launch → preparation → context/deck chain fixes the original
thresholds. Missing tail fields prevent an impulse or full energy audit.
This diagnoses a contact-model problem, not board strength or construction safety.

Run `uv run pytest tests/test_quiescent_hardware_diagnostic.py -q` to replay
the report from the archived native output without a solver.
