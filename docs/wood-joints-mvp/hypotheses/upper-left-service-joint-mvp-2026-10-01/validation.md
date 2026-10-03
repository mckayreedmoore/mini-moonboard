# Joint packet validation

This validates the source checker and handoff, not the engineering joint.
The joint remains HOLD, with local MVP, six-case acceptance and physical
release flags false. No native or CAD work, shared staging, commit or push ran.

The first independent Luna/max pass found no substantial correctness or
architecture issue. Testing identified three meaningful gaps: incomplete
release-flag regression coverage, missing boundary factor/receiver/port guards,
and an omitted explicit shop-sequence/individual-transport gate. All three
were confirmed and fixed. The checker now verifies the exact two receivers,
sixteen source port names and twenty source load nodes at all 21 states;
tests reject wrong factors/receivers, missing/duplicate states and ports, and
out-of-interval moments. Every release/model-state flag and the exact seven
remaining engineering/operational gate IDs are asserted.

The second independent pass found no correctness issue and confirmed two
additional useful safeguards: enforce candidate identity as well as revision,
and assert that saved receiver force/moment/datum values remain unchanged.
Both were fixed. The checker requires the named wood-joint candidate in its
action/freeze/geometry/seat inputs. Tests reject another candidate/revision,
preserve distinct nonzero synthetic wrenches, and compare all 21 original
boundary rows with independent golden digest
`63cf2ad4d39762ee541ca06a733e1a73de15cce7e915e4141d9e6c2ef830ad27`.

After these fixes, all six focused unittest checks and Ruff pass. The final
replay preserves 84 bolt states, 21 complete boundary states, eight nominal
washer seats and the original numerical component results. `review-target.json`
preserves the first target; `review-target-pass2.json` preserves the second,
and `review-target-pass3.json` binds the final target and generated report.
The first and second reviews remain byte-preserved. The third independent
Luna/max pass reports no substantial correctness, testing or architecture
findings. Its reviews are [correctness](review-pass3-correctness.md),
[testing](review-pass3-testing.md) and [architecture](review-pass3-architecture.md).
The testing reviewer independently reran six tests, Ruff and the exact
checker replay. Parent authenticated all three final source-file hashes,
the unchanged generated-report digest and the review-file digests in
`final-receipt.json`. Five confirmed implementation/test findings were fixed
over the three review rounds; no source-checker finding is deferred. The
seven engineering/operation gates remain open, which prevents joint MVP
acceptance regardless of this clean software review.

Final generated-report SHA-256:
`35f11b92a35604c8d924d20d9cb5f9a5221b415ef40cc9fb94e8de8f5fcc346d`.

The local source report is `/tmp/mini-moonboard-upper-left-service-joint-mvp-2026-10-01.json`.
It requires the existing ignored raw JSON/native/STEP evidence and is not a
standalone clean-checkout evidence bundle. The canonical project continuation
is [NEXT-AGENT-HANDOFF-2026-10-01.md](../../NEXT-AGENT-HANDOFF-2026-10-01.md).
Included usage was freshly observed at 99%, ordinary usage allowed; stop at
unknown/exhausted usage without credits or paid/API fallback.
