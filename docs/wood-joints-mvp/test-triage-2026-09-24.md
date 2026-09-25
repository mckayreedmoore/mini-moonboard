# Pytest triage, September 24, 2026

Status: the full default pytest run remains unclassified and incomplete. This
note records one approved, bounded reproduction and the repair made to two
historical bolted-candidate geometry screens. It does not report a full-suite
pass or a wood-joint acceptance result.

## Incomplete full-run log

`/tmp/wood-joints-pytest-20260924-1458.log` contains progress through 46% (1,403
test markers) and nine `F` markers, then ends without tracebacks, a summary or an
exit status. A first attempt to map those markers through pytest's cached
collection order selected nine tests. That mapping was disproved: two selected
tests passed in the bounded rerun. None of the original `F` markers can now be
tied reliably to those selected test IDs. The difference between nine markers
and seven reproduced failures is unexplained; the log cannot establish the
full run's final failure count.

The exact bounded rerun output, including tracebacks, is preserved at
`/tmp/wood-joints-triage-repro-20260924.log`. It ran only these nine test nodes
and finished in 22.52 seconds with seven failures and two passes:

- Five tests in `tests/test_bolted_center_post_offset.py` failed at
  `scripts/bolted_candidate_center_post_offset.py:99` with
  `ValueError: Kerf-right and official post panel axes diverged`.
- `tests/test_bolted_center_shift_screen.py::test_outward_shift_retains_all_twenty_center_panel_axes`
  failed at `scripts/bolted_candidate_center_shift.py:81` with
  `ValueError: official/kerf-right relevant panel axes diverged`.
- `tests/test_bolted_native_input_contract.py::test_saved_native_input_is_explicitly_stale_until_v4_candidate_is_frozen`
  failed because the saved/current source-hash difference set includes an
  additional kerf-right axis CSV.
- `tests/test_bolted_center_shift_screen.py::test_prior_both_member_shift_does_not_select_owner_post_only_change` and
  `tests/test_bolted_task_ledger.py::test_ledger_has_unique_ids_and_resolvable_dependencies`
  passed.

Before the first rerun, the 14:58 pytest `lastfailed` cache already listed all
seven failing node IDs. At that time, the affected bolted screen scripts and
tests and the saved native-input document had September 22 timestamps; none
was a September 24 wood-joint implementation file. This is pre-existing
bolted-candidate lane work, separate from the active WJ24 changes.

## Screen comparison defect and repair

The two screen functions compared complete CSV row dictionaries across the
official and kerf-right packets. Their relevant rows have the same axis IDs,
receivers, locations, directions and modeled/occupied sizes. The compared rows
differ only in the packet-specific `assessment_status` prose. That prose made
the screens raise before evaluating or returning geometry results.

The guards in `scripts/bolted_candidate_center_post_offset.py` and
`scripts/bolted_candidate_center_shift.py` now compare rows by axis ID and the
geometry-bearing fields used by those screens. A focused regression in each
test file proves that different packet status text is accepted while a changed
`start_x_mm` is rejected. The historical JSON outputs and the two axis CSVs
were left unchanged.

The approved post-repair run selected the five previously failing post-offset
tests, the previously failing center-shift test, and the two new regressions.
All eight passed in 25.08 seconds. Ruff passed on the four changed files. These
checks cover only the two bounded geometry screens and do not close the native
input contract failure or classify the incomplete full run.

After recording the stale CSV history in the native-input test, the complete
`tests/test_bolted_native_input_contract.py` file and the same eight focused
screen nodes passed together: 12 passed in 33.37 seconds. Ruff passed on the
native-input test. The full output is preserved at
`/tmp/wood-joints-native-source-refresh-check-20260924.log`.

## Stale native-input fingerprint

The failing native-input test compares the saved, non-ready contract against
current source hashes. The saved hash for
`docs/floor-flush-construction-kerf-right/connection-axes.csv` is
`5b2b36f74fd5217ce91a5ceabf5134560811adfa2132eec999cd9f58a2ad6ad7`; the
current file hash is
`174033945a2136b094bf99360cb2c6dfa409accef423ab12538ef289b5d36a58`. The
saved input is timestamped September 22 at 11:59; the CSV is timestamped that
day at 15:52. The existing width-option documentation explains that the
kerf-right faces are narrower and the right-hand frame members move inward.
The current CSV reflects that packet-specific geometry: across its 222
common axis IDs, 52 right-side `start_x_mm` values differ by 3.175 mm, and the
packet description differs on every common row. The 32 panel axes used in the
center-shift parity screen and the four center-post kicker axes remain
geometrically equal between packets.

This source-history difference explains the extra path in the test failure;
it is not evidence that the selected baseline changed in the wood-joint lane.
`docs/bolted-candidate-native-input.json` remains historical and explicitly
non-ready. Keep it stale until the separate bolted candidate has a frozen
V4 input contract; do not regenerate its hashes. The stale-input test now
includes the September 22 kerf-right CSV refresh in its exact expected
stale-source set, alongside the owner-input and timber-helper differences.
Its inline history comment records why the saved fingerprint remains stale.
The test still asserts that no native cases ran and that the saved input is
not ready.

The selected-candidate export check is a separate, already documented gate:
`local-validation-2026-09-24.md` records the pre-existing mismatch between the
selected model and its frozen geometry snapshot. This triage did not alter
that model, its hashes, or its evidence. Likewise, the earlier Ruff log at
`/tmp/wood-joints-ruff-20260924-1458.log` names a `producer.py` that is absent
from the current tree (only its `.py.snapshot` remains); the local validation
checkpoint records a later whole-repository Ruff pass.

## Source hash context

Hashes below were captured before the screen repair and bind the reproduced
tracebacks to their inputs. The saved native-input hash is the original
fingerprint stored in that JSON; the current CSV hash was measured from the
working tree.

| File | SHA-256 or saved SHA-256 |
| --- | --- |
| `scripts/bolted_candidate_center_post_offset.py` (pre-repair) | `8463215b6a25d4a4cdaee2b7bbbfef18704d3f2bf6770b7a5d1c595f4968bf0d` |
| `scripts/bolted_candidate_center_shift.py` (pre-repair) | `c436a73ced0089861e52e3bd9dc6939d9fe4b2c67add661564f508f4262f4e0f` |
| `scripts/bolted_candidate_native_contract.py` | `25c9a0e409754abebafe3b3ffff65ea58b01559575ab4144124c95013399afcf` |
| `tests/test_bolted_center_post_offset.py` (pre-repair) | `5d8c8f3ac0776658c5b637746f428012ed98bc76a3b3131ea723967594be1ea1` |
| `tests/test_bolted_center_shift_screen.py` (pre-repair) | `75e0a81e9de7ca857339af44cbc4882dea561553dabd52896a0ce7d3ea31238d` |
| `tests/test_bolted_native_input_contract.py` | `1547cfd933f708e3cdf1f5107d7fd3e12cb720ec7559208ff7320411d7d161d5` |
| `tests/test_bolted_native_input_contract.py` (after documented expectation update) | `04632e6c3bc7e7ec061f0978ef3c5020958bca32a8c762280b20dddb059e9da8` |
| `tests/test_bolted_task_ledger.py` | `6612383e1b19286ff1afa1d413289c7774b8ac3623ad3910ec48959df1a3f86c` |
| `docs/floor-flush-construction/connection-axes.csv` | `746ca0963838396004f22147a5f4a66991375aaf925036caf60718f83b6b0a58` |
| `docs/floor-flush-construction-kerf-right/connection-axes.csv` (current) | `174033945a2136b094bf99360cb2c6dfa409accef423ab12538ef289b5d36a58` |
| `docs/bolted-candidate-native-input.json` | `0eeab3bc907f159a0b6862da81f29ccf4dda26243b647a408bb5fdbe5e78254a` |
| Saved native-input hash of the kerf-right axes file | `5b2b36f74fd5217ce91a5ceabf5134560811adfa2132eec999cd9f58a2ad6ad7` |
| `mini_moonboard/compact_floor_flush_frame.py` | `8764bec57564efa79f2636e589aa0e35b229c48975c791eec5c47b20183bf17a` |
