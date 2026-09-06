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
