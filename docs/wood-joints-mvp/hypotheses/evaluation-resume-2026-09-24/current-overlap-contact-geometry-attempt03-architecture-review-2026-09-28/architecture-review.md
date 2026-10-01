# Attempt03 architecture review

**Candidate/revision:** `compact-floor-flush-wood-joints-development` / `led-clearance-2x6-runner-seated-blocks-v1`  
**Criterion:** `overlap_contact` remains `pending`  
**Scope:** attempt03 source and its frozen evidence packet; read-only review.

## Assessment

The attempt03 dependency chain is explicit and hash-bound: attempt03 reuses attempt02 and attempt01 helpers, validates the upstream graph, and keeps the work at geometry classification. The packet pins 26 repository inputs, including the attempt03 producer and test, attempt02’s packet, three attempt02 review records, and the T04 verifier and checksum manifest. Attempt03 checks the direct hashes before calling `attempt02.verify_packet`; that verification path runs the pinned T04 verifier. Attempt02’s four packet files are separately fixed-hash checked and then reverified. Evidence and README retain the geometry-only limitations and pending disposition.

The frozen packet checksum command passed, and `python3 -m scripts.wood_joint_wj08_overlap_contact_geometry_attempt03 --verify` returned `PASS_GEOMETRY_ONLY_CRITERION_PENDING` with the expected 50 nodes, 1,225 pairs, and geometry classifications. I found one low-severity verifier metadata gap; the checked-in packet’s current metadata is correct.

## Finding

- **Low — verifier accepts inconsistent candidate, revision, or scope metadata.** `freeze_packet` writes `candidate`, `revision_id`, and `scope` into `source-pins.json` at `scripts/wood_joint_wj08_overlap_contact_geometry_attempt03.py:325`, `:326`, and `:330`. `verify_packet` checks the schema and attempt ID at `:364–365`, disposition at `:374–375`, predecessor packet, upstream verifier, and review bindings at `:376–389`, but never compares those three fields with the pinned candidate/revision and fixed geometry-only scope. `_render_readme` does not consume them; its source-count statement is at `:301–303`. Changing only those values and refreshing the packet checksum manifest could therefore leave `--verify` passing while the source-pins metadata misstates which candidate/revision or scope it describes. Compare the fields with `EXPECTED_CANDIDATE`, `EXPECTED_REVISION`, and the frozen scope string, and add a verifier test for each rejected mismatch.

## Other review questions

- **Dependency boundaries:** The successor script reaches through attempt02 to `attempt02.attempt01` helpers and constants (`scripts/wood_joint_wj08_overlap_contact_geometry_attempt03.py:14`, `:16–25`, `:71–98`, `:101–110`, `:220–240`). This is tight implementation coupling, but the imported layers are explicit and their source hashes are recorded; it does not currently leave an unbound source dependency.
- **Source/verifier pins:** The current producer, tests, upstream geometry producers, predecessor packet and review records, T04 verifier, and T04 checksum manifest are included in the source-hash map and compared during verification. The T04 verifier is called through attempt01’s `_run_upstream_verifier` (`scripts/wood_joint_wj08_overlap_contact_geometry.py:398–411`).
- **Predecessor integrity:** All four attempt02 packet files have fixed SHA-256 values in attempt03 and are rechecked by attempt02’s verifier. The attempt02 predecessor review records and T04 verifier inputs also have fixed hashes.
- **Geometry-only scope:** The adapter applies geometry measurement/state consistency checks (`scripts/wood_joint_wj08_overlap_contact_geometry_attempt03.py:105`, `:215`), inherits the member/panel pair inventory, and writes no contact law, active-contact result, force transfer, or acceptance. It preserves `pending` in the generated evidence and verification result (`:223–240`, `:405–415`).
