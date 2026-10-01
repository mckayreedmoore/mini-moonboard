# Shared-edge penalty-control results

`PASS_SHARED_EDGE_PENALTY_CONTROLS`. Both unchanged surface-to-surface penalty
inputs completed normally in pinned CalculiX 2.23 and passed all frozen
known-answer, trace and output checks. Each case accepted one full static
increment at time 1 in two iterations, without a rejected attempt or cutback.
Native and Docker exit codes were zero, with no OOM or monitor stop.

The maximum normal displacement-profile error was `6e-10 mm`, below the
`1e-7 mm` limit. Both axes approached by `5.00006e-5 mm`, against the
`5e-5 mm` linear reference. Each interface gap was `−1e-5 mm` to the printed
precision and face warp was zero. Axial support resultants were approximately
`3.9999998 N` against `4 N`; pressure compliance was approximately
`5.00006025e-5 mm3/N` against `5e-5 mm3/N`. All inherited tolerances remain
unchanged.

Across both cases, force-closure and first-moment-closure norms were each
below `2.83e-7` in their corresponding units, against limits of `0.041 N`
and `0.041 N mm`. Full 81-node U/RF DAT and DISP/FORC FRD
coverage passed. Each CONTACT block contains 81 finite node records, including
all 15 distinct slave nodes in the shared-slave case and all 18 in the
cross-role case. Contact-field coverage is diagnostic; this is not a
pointwise-pressure or pair-local force validation.

All 12 frozen input hashes and all recorded output hashes match. Each root
run entry equals its case execution record. The executed decks remain
byte-identical to the corresponding inputs from the preceding four-case
packet. Synthetic positive and negative preflight checks had passed before
freeze. Serial execution ran on September 27, 2026, from 16:40:58.004734 to
16:40:58.649743 UTC; each case took about 0.32 seconds.

The [independent result review](independent-review.md) confirms the raw outputs,
known-answer errors, provenance and bounded interpretation.

Evidence:

- [Input freeze](input-freeze.json):
  `e622aae3283d2c0d7f940e9e706ecc15b616eaf19fe1593c2d038fa97da12c9c`.
- [Execution](execution.json):
  `0b0f13ba110ac051125231e2149000afad5624b9d7e46424ab68c1799739c445`.
- [Verifier result](verifier.json):
  `013a0259dd9806bcddfcb3e204374b79df0f3d99486f4b8809d4e831656d871b`.
- [Frozen verifier](verifier.py):
  `c541fa3180d5cdac1bb3c87defdaf73e160f320f3b27f098727d70633b44897f`.

This establishes the two tested sharing-pattern responses for the penalty
formulation in this small fixture. The [shared-slave MORTAR failure][mortar]
remains terminal; its cross-role case was not run. A penalty pass neither
rescues that MORTAR result nor proves the failure's unique cause. No current
joint response, strength, structural criterion or release is accepted here.
The energy-output check and explicit current-joint path contract remain
separate readiness work before a joint-method run.

[mortar]: ../contact-mortar-shared-edge-known-answer-attempt02/RESULTS.md
