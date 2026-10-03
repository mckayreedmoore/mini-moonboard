# Panel receiver verification record

This record concerns the frozen source join and its method limits for
`led-clearance-2x6-runner-seated-blocks-v1`. It adopts no resistance criterion
and changes no reviewed geometry, native source, purchased hardware policy,
or release flag. The mechanics coordinator retains native readiness,
execution and response acceptance; the primary owns integration and Git.

## Independent parent reconstruction

The initial inventory parent replay verified all 66 current axes, 58 retained
stations, eight recorded moves, 22 panel/receiver pairs, 16 receiver members,
and 79 inventory source-byte bindings. After closing the graph-input source
guard, the inventory verifies 145 distinct byte bindings, including all 68
declared graph geometry inputs. The current center-kicker receiver
identities are the two center posts. Historical backer identities and the
50.8 mm occupied-length proxy remain provenance, not current receiver or
installed-thread evidence.

A direct raw-model/response reconstruction retained 1,386 screw states and
4,158 native scalar components across A12-rear, A1-rear and K12-rear. Local
lateral scalars transformed by the recorded force basis, and withdrawal
scalars transformed by their preserved normal, reproduce the saved endpoint
vectors. Their source law remains explicitly non-qualifying for Hillman.

A separate recursive equation-transpose oracle examined all 5,544
panel/receiver endpoints. Continuing through physical support pivots into
reduced free DOFs reproduced the initial refusal census: 77 moment
discrepancies, 42 force discrepancies, and seven affected role/receiver
memberships on four kicker axes. The force discrepancies occur only in
A1-rear; moment discrepancies occur in all three cases. No comparison bound
was relaxed, and no additional couple was inferred.

Stopping the independent recursion at the first owned physical DOF instead
projects applied connector loads onto the physical body before its support
constraints. All 5,544 endpoint force and moment comparisons then agree
under the original 1e-7 N and 1e-5 Nmm comparison bounds; the largest moment
component about a reported attachment point is approximately 9.89e-8 Nmm.
Support reactions are separate source channels and are not added to screw
loads or counted as numerical spring-ground reactions.

The unchanged upper `actions.py --verify` and `nodal_transfer.py --verify`
both pass exact saved-byte checks. The latter covers 42 top-cleat states and
672 connection transfers. Those top-cleat paths are not the newly examined
floor-dependent receiver paths. The primary's bottom/finished-host producer
uses physical point-action records directly, without this recursive
MPC expansion. These checks do not extend a historical acceptance claim.

## Closing validation

The full producer `--write` and `--verify` both complete with exact saved
bytes. The combined source closure contains 171 distinct pins; a separate
parent byte/size/hash check verified every record. The output contains
1,386 screw states, 4,158 scalar states, 5,544 endpoint actions, 924
physical-body projection groups and 840 panel/contact receiver groups.
All endpoint and group physical-body projection comparisons agree; the
recursive reduced mapping remains explicitly `REFUSED` with the original
77 moment and 42 force discrepancies.

The saved endpoint records were compared with both independently calculated
raw-source oracles. All 5,544 records agree, with a maximum moment-component
difference of approximately 4.55e-12 Nmm. This verifies the reported source
diagnostics and projection, not the stiffness law or hardware resistance.

All 30 focused tests and Ruff lint/format checks pass. The 30 tests also pass
in a temporary checkout containing only this packet's Python files and its two upstream
Python helpers, without the frozen JSON, STEP inputs, or repository
`conftest.py`. The known-answer mapping fixture includes an owned physical
pivot constrained to an unowned fixed support, a nonzero moment arm, rounding
radius propagation, and support reaction channels kept separate.

Both raw output files remain ignored and uncommitted:

| Local output | SHA-256 |
|---|---|
| `receiver-transfer.json` | `0ac0e30d582322f8919277aabec3af134c7bf5ecb2b0523d649622bcd4a47534` |
| `source-pins.json` | `973ffd947cb6bcaa823e4038c0b6c98fc18736423a872ef87666806878784b3e` |

The first three independent Luna/max reviews covered correctness, testing
and architecture. The architecture review identified that the Hillman note
cited the purchase record and shop checklist without pinning their bytes.
The producer now includes both records in its source closure, and exact
replay, all 16 tests, Ruff lint and formatting pass after regeneration.
The action implementation and tests were also formatted without semantic
or method-document changes.

A fresh second three-agent Luna/max pass found a further source-snapshot
guard gap. Each native case now checks its recorded attempt04 manifest,
receiver screen and contact graph hashes against the current input bytes.
The inventory also validates and pins all declared graph geometry inputs.
The present bytes matched before this fix; the added mutation checks prove
that changed source bytes refuse a future join despite unchanged revision
and axis IDs. The source responses and action resultants are unchanged.

The second testing reviewer disclosed seeing peer summaries during a status
lookup after completing its independent checks. The closing third pass uses
fresh reviewers instructed to avoid peer notes and that status tool.

The fresh third pass returned no correctness or architecture findings. Its
testing review identified two useful coverage gaps, without finding a current
implementation defect. The known-answer fixture now uses signed non-unit MPC
weights and physical nodes offset from the response and common datums, with
explicit force/moment radii. Eleven independently constructed audit mutations
check parent status/count, body/global raw and interval gates in both source
records, and numerical ground exclusion. Only the test file changed.

The fourth independent pass returned no correctness or architecture findings.
Its testing review identified two bounded coverage gaps, without finding an
implementation defect. An unaffected-body failed gate is now refused even
when the report selects another body, and distinctive numeric source audit
resultants and radii survive the positive snapshot. A small source-only
fixture exercises the real per-screw assembly of signed lateral and
withdrawal actions, endpoint order, combined force/moment vectors and radii.
Only the test file changed; the full exact replay and all 171 source pins
were verified after regeneration.

The fresh fifth Luna/max pass is closed. Reviewers received the raw task,
current implementation and validation evidence, without earlier findings or
peer notes. The correctness and testing reviews found no consequential
defects or missing acceptance behavior. The architecture review identified
one conditional API risk, explicitly deferred below.

| Independent reviewer | Checks and outcome |
|---|---|
| `/root/panel_receipt_correctness` | Read inventory/action joins, source records, saved output, MPC helper contracts and producer error paths; no substantial correctness findings. Saved native models have no fixed-node/physical-node overlap. No tests or full replay run by this reviewer. |
| `/root/panel_receipt_testing` | All 30 focused tests and read-only full `produce.build_report()` replay pass, including the 171-pin/21-state census and separate projection/refusal results; no consequential coverage findings. |
| `/root/panel_receipt_architecture` | Read ownership, source closure, module imports and claim boundaries; one conditional cross-checkout API risk, deferred with the rationale below. No replay or tests run by this reviewer. |

Deferred architecture finding: importing `actions.py` from checkout A and
directly calling its `build_report(root=B)` can execute A's sibling helpers
while pinning B's helper files. The supported `produce.py` CLI uses its own
checkout; `produce.build_report(root=B)` dynamically imports the modules
from B. Those paths therefore execute the pinned helper files, and the
current exact replay independently verifies all 171 byte bindings. The
action report also records the executed helpers' hashes. No current packet
result is affected. A future direct cross-checkout action API consumer must
load that module from the target checkout or add a runtime-path refusal
before relying on its pin document. This bounded future API guard is
deferred to preserve the reviewed current-path implementation.

The testing reviewer suggested an optional future regression combining a
successful physical-body projection and refused reduced mapping in one
synthetic connection fixture. This is deferred: the existing fixture checks
the separate stencils and wrenches, and the full frozen replay plus the
independent raw-source reconstruction of all 5,544 endpoints verify that
physical-body agreement does not erase the original refusal. There are no
other unresolved review findings.

## Frozen code and method bytes

These files are included in the final source-pin document:

| File | SHA-256 |
|---|---|
| `produce.py` | `7482a21e9b3a52c70679b6701112651ef42abbc1a1b8a761c885780827f88731` |
| `test_produce.py` | `b1f3015d65cd8ffaf28b235087e813c9274da82a0ddc55b8700c7402587326f4` |
| `inventory.py` | `c4c826055bdbe555fefc76d58c0d0eb39cfc884351e082b4fa8998541742dd6e` |
| `test_inventory.py` | `09d340742a1922d570102814f5b0acb0bf334b18bb4197028c02228779a1a1de` |
| `actions.py` | `ef296cd40458a8c05610707c3d072eea8a9db65aa7681fa3e680f299b89ec790` |
| `test_actions.py` | `74a240d3e825a753ff6a620010277070b96934b838a76ca2e98362eee8284ebc` |
| `inventory.md` | `4ec74a817feffb869052f1558c62890ae02e4035f5cb367fc06e4d496ffbb639` |
| `actions.md` | `d0e2c3dd26770a1a239371082284da9e57c3a6ea6f007f86c1edc64fd444f47e` |
| `hillman-applicability.md` | `8a5f5a031c429eee9d2c08a20047dd0b01c2b1be44b849b30132cc3ad5056354` |
