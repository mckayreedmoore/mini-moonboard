# Attempt02 architecture review

Reviewed 2026-09-28. Scope: `scripts/wood_joint_wj08_overlap_contact_geometry_attempt02.py` and its frozen packet at `current-overlap-contact-geometry-evidence-attempt02`, with the attempt01 adapter and T04 verifier inspected for dependency boundaries. This was a static review; no test suite or adapter verifier was run.

## Assessment

The adapter remains a focused geometry-only post-processor. It reads the frozen contact graph, checks measured geometry against the upstream classification states, and delegates inventory construction and packet mechanics to attempt01 (`scripts/wood_joint_wj08_overlap_contact_geometry_attempt02.py:71-201`). It does not load CAD or solver code. The evidence and README explicitly leave contact law, active bearing, force transfer, capacity, case response, and criterion acceptance unestablished (`.../current-overlap-contact-geometry-evidence-attempt02/README.md:24-28`; attempt01 evidence contract at `scripts/wood_joint_wj08_overlap_contact_geometry.py:338-384`).

The packet binds the attempt01 inputs, the current graph and receiver producers, the predecessor review, and attempt02 producer/tests. Its 15 listed source hashes matched the current files, and all three frozen packet checksums passed. The frozen record keeps `overlap_contact` pending.

## Finding

### F-01 — The rerun verifier is not anchored by attempt02 source pins

**Severity: Low — verification provenance only.**

Attempt02 invokes the upstream T04 verifier during both freeze and verify (`scripts/wood_joint_wj08_overlap_contact_geometry_attempt02.py:265-273,306-310`), through attempt01’s subprocess call to `verify_packet.py` (`scripts/wood_joint_wj08_overlap_contact_geometry.py:398-406`). However, attempt02’s source-hash set is inherited from attempt01 plus three explicit extras and its own producer/test (`scripts/wood_joint_wj08_overlap_contact_geometry_attempt02.py:32-36,53-68`). Attempt01’s fixed input map binds the T04 README, graph, and `source-pins.json`, but not T04’s `verify_packet.py` or `SHA256SUMS` (`scripts/wood_joint_wj08_overlap_contact_geometry.py:25-42,62-75`). T04’s verifier checks its local manifest against packet files, including itself (`current-geometric-interface-map-attempt02-2026-09-28/verify_packet.py:438-440`), but that manifest is not independently anchored by attempt02.

Consequently, a coordinated change to the verifier and its local checksum manifest could preserve the pinned graph and source-pin JSON while changing what the claimed upstream rerun check verifies. This does not change attempt02’s emitted geometry values, which are derived from the directly pinned graph, and it does not create a mechanics or acceptance claim. To close the provenance gap, add fixed expected hashes for the T04 verifier and checksum manifest to the attempt02 pin set, or remove the assertion that the pinned upstream check was rerun.

## Disposition

The adapter’s scope and evidence boundary are sound. F-01 is the sole actionable architecture finding and is limited to reproducibility of the upstream verification step; it does not invalidate the current geometry-only inventory or alter the pending criterion status.
