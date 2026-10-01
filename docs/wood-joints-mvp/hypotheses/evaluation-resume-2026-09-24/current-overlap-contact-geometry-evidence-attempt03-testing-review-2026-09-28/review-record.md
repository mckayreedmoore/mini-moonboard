# Attempt03 testing and reproducibility review

Candidate: `compact-floor-flush-wood-joints-development`  
Revision: `led-clearance-2x6-runner-seated-blocks-v1`  
Criterion: `overlap_contact` remains pending.

## Finding

**P2 — Add a failure-path test for actual source or frozen-packet drift.** In
`tests/test_wood_joint_wj08_overlap_contact_geometry_attempt03.py:125-131`, the
drift test changes the expected predecessor hash in memory; it does not alter a
pinned input or a frozen packet. The freeze/verify test at lines 133-163 only
checks a successful cycle and valid checksums. Consequently, the suite does
not exercise the main failure paths in
`scripts/wood_joint_wj08_overlap_contact_geometry_attempt03.py:359-404`, such
as changed current source hashes, modified evidence/source pins, or a broken
packet checksum. Add a `tmp_path` case that freezes a packet, changes a real
pinned input or packet file, and asserts that verification rejects it. This
would make the reproducibility guarantee resilient to regressions in the
verification checks.

## Coverage and verification

The geometry tests include nine one-field contradictions above the relevant
distance, area, and volume limits, plus equality-at-tolerance acceptance cases
for shared area and common volume. I found no issue in those covered cases.
The builder and CLI tests assert `pending`; the frozen evidence and source pins
also record `pending`. The selected criterion register and method map remain
pending as well.

Validation performed:

- `.venv/bin/python -m pytest -q tests/test_wood_joint_wj08_overlap_contact_geometry_attempt03.py` — 13 passed.
- Attempt03 packet `--verify` — passed with `PASS_GEOMETRY_ONLY_CRITERION_PENDING`.
- Packet `sha256sum -c SHA256SUMS` — all three listed files passed.

No source, test, packet, queue, status, or goal files were changed for this
review.
