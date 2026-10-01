# RF-to-opening fixture status after native run

The preparation packet and README preserve their pre-run status. The parent
ledger records `rf-opening-known-answer-attempt02` as consumed and terminal:
freeze SHA-256 `352fe14543c8ed9a6e71e9887225ecb8c0fe6f54c3a62262067f23a292685c68`,
native exit 0, and execution record SHA-256
`41a6ebb8f10e3351a710465623b8be5f8e7820fff2eb4a865a26bbd6286d6a10`.

Independent pre-run review passed at SHA-256
`e1ae4ea5efaa67e301698f0a21ae8ee7c44e9e770ea8ab77f38d87de0dd0486b`.
Independent post-run review passed at SHA-256
`067fffce0ef1950fc1d93b12959e66ea7519abe086d71273c2dfe2ac0f534e86`; all
810 source pins and nine output hashes matched, both RF-to-opening intervals
contained their known answers, and each interval fell on the expected side of
the `1e-7 mm` threshold.

This is a method-only result for isolated linear springs. The spring remains
active in tension, so the run does not test unilateral gap engagement, release,
side switching, frame response, joint capacity or mechanical acceptance. Do
not rerun or reuse the consumed attempt. The separate radial-gap fixture has
its own offline analytical audit and still requires its own exact native freeze,
pre-run review and parent ledger entry.
