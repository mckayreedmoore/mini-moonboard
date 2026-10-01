# Shared-edge attempt02 result

The first case, `shared_slave_mortar`, failed to converge. It has no accepted
state and no passing mechanical or contact-method result. The serial runner
stopped after that failure, leaving `shared_slave_penalty`, `cross_role_mortar`
and `cross_role_penalty` unexecuted.

The native CalculiX 2.23 process ended with code 201 after 201 iterations in
step 1, increment 1, attempt 1. The only STA row is rejected (`1U`), with total
and step time both zero. CVG contains iterations 1 through 201. The terminal
message is `too many iterations needed`. Docker reports `OOMKilled=false`;
there was no parent time/output stop. Runtime was 1.626 seconds. The frozen
MORTAR audit cap of 14 is also exceeded. Final FRD values are the solver's
unaccepted best iterate, not an endpoint suitable for the known-answer gates.

Before iteration, native output explicitly reports that nodes 1, 4 and 24
belong to both `Z_CENTRAL` and `X_CENTRAL` slave surfaces and that their
Lagrange multipliers are removed. It emits this warning in both pair
orderings. This is the shared-edge pattern the fixture was intended to test.
The pinned source, `remlagrangemult.f:52–76`, sets `islavact(l)=-2` on that
shared-slave path. Lines 78–93 contain the analogous slave/master cross-role
removal. The cross-role deck did not run, so the latter is source evidence,
not an observed cross-role result. The warning and failure do not establish
a unique causal explanation for every residual or any physical joint failure.

All 14 frozen file hashes, the executed deck, root/case execution records and
all recorded native output hashes match. The pre-run synthetic oracle passed
for all four decks, including rejection of excessive displacement/reaction
perturbations and missing/nonfinite DAT records. The four decks were unchanged
from the captured preparation. The separately owned attempt02 corrected only
verifier units, schema access, numeric representations of existing tolerances,
case-order checks and a surface-count prose typo. The earlier active worker's
files remain preserved.

Evidence:

- [Input freeze](input-freeze.json):
  `1a23e2fe3fb5152d12d54b49e3033f4edb0793d699263e17d0a0b7d3b6b0ad6c`.
- [Execution](execution.json):
  `188e1097ac1f68aa21a025fd9bd0a96c6f7e3c68a5873e986dc853588af0023c`.
- [Failure diagnostic](failure-diagnostic.json):
  `40159d1d37047be8070a96553ae706a2192afd8a4a77e5d85db448cc250a67ff`.
- [Frozen verifier](verifier.py):
  `e1c71ac9959bab6a66b13f8d8315d9536af41785f32a44ba9bf722c90d9d7ac7`.
- Pinned source archive:
  `9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7`.
  Member `CalculiX/ccx_2.23/src/remlagrangemult.f`:
  `85376768d34d9aa2a91c96554c7a39befe476e01ceac8709d49d3de8b92308c2`.

The frozen verifier records `FAIL` at the incomplete-root-execution gate. The
separate diagnostic records the more specific native failure without changing
that verifier or claiming a later pass. No thresholds were widened.

The next bounded comparison is the two unchanged penalty control decks in a
separately reviewed and frozen subset packet. This can distinguish the tested
formulation behavior from a general fixture/oracle problem. It cannot repair
the failed MORTAR result or authorize a current-joint solve. Do not remove
physical contact edges, add restraints or alter the reviewed model to make
this test pass. Joint acceptance and all structural criteria remain open.
