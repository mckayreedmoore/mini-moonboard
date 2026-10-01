# Attempt 05 post-timeout continuation forensics

Status: preserved forensic addendum; it does not replace or edit the original
`port_motion_n_plus-execution.json` record and does not create a response
result.

## Observation

The execution record reports an outer timeout from 2026-09-27 00:32:42 UTC to
00:42:57 UTC and return code 137. The named Docker solver container remained
alive after that record was written and continued updating its bound `.cvg`
and `.sta` files. The parent stopped the named container after discovering
the continuation. At the 2026-09-27 01:39:58 UTC process check, there was no
`wj-native` container or CalculiX process. A later process check likewise
found none.

The last `.cvg` record is increment 2, attempt 3, iteration 31. The `.sta`
summary still records increment 1 accepted at 0.01 mm and increment 2
attempts 1 and 2 as unaccepted after 60 iterations each. No later increment
was accepted. This is an incomplete nonlinear continuation, not a converged
response or a physical failure result.

## Hash reconciliation

The original execution snapshot remains intact. Of its recorded solver-output
hashes, these files changed during the unrecorded continuation:

| File | Recorded SHA-256 | Current SHA-256 |
| --- | --- | --- |
| `port_motion_n_plus.sta` | `00b8b6e5df0e0cc6161026af97e51d8afff895fb1523185fc25707585a8d0d34` | `e15ad08507b022586c15ed91fa7d63ba73d65a505727b6f9fc9862ff88296241` |
| `port_motion_n_plus.cvg` | `cb353784c44218c1d4553dc21aee20378c3991f8946bb31b214f373075ab3688` | `e7a3eb421a93f818c25afc867707198ff06cf925a1066d537a77e6d23f38f851` |

The recorded hashes for `.dat`, `.frd`, `.stdout`, and `.stderr` still match
the current files. The `.cvg` last changed at 01:37:32 UTC; the `.sta` last
changed at 01:25:19 UTC. The stdout and run metadata therefore describe only
the original outer-timeout snapshot, not the later solver iterations.

## Disposition

Keep the original execution record as evidence of the launched run and its
timeout snapshot. Use the current `.cvg` and `.sta` only with this addendum as
an unauthenticated post-timeout continuation from the same bound process.
Do not treat them as a second run, overwrite the original hashes, or use the
continuation as a joint-response result. The output mismatch was caused by
the launcher ending while its Docker child remained alive; any future native
execution needs parent monitoring of the container itself and hash capture
only after verified process termination.
