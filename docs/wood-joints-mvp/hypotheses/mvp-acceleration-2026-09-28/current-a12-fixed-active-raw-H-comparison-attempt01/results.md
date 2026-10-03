# Parent raw-H comparison result

The parent independently reviewed the equations and execution controls,
replayed readiness, then ran the one-shot parent entry under the shared lock.
A draft G-transpose indexing error was caught and corrected before freezing;
the same shared assembly helper now passes an exact noncontiguous-bound
identity oracle. No frame solve ran with the draft error.

The actual fixed-branch comparison completed in 4.658475 seconds using one
unregularized general-LU solve. Matrix order and numerical rank are both
2649; minimum/maximum singular-value ratio is 1.08523e-7, and relative
linear residual is 1.01479e-17. All fixed-bound gates and all ten original
physical checks pass. Maximum body force residual is 1.87583e-12 N and
moment residual is 2.88480e-9 Nmm. Maximum spring-law residual is
1.13321e-7 N, compared with 1.08219e-4 N for the prior symmetric attempt.
This improvement does not settle the original source-force gate.

| Original source comparison | Failed rows | Maximum absolute difference | Maximum interval ratio |
| --- | ---: | ---: | ---: |
| Force | 27 | 0.0004846632 N | 128.2644 |
| Projected q | 0 | 1.0730411e-6 mm | 0.862411 |
| Rigid coordinates, source units | 0 | 1.9205537e-6 | 0.379246 |

The normalized worst force row remains source position 1586. The complete
27 failed rows, including source position, family, group, element, native
center/radius, arithmetic guard and signed prediction, are retained in
[assessment.json](assessment.json). Full force, coordinate, gap and multiplier
vectors are saved in [response.npz](response.npz). The original force, q,
coordinate, physical and branch criteria were not widened or changed.

Disposition: **STOP_PHYSICAL_OR_SOURCE_COMPARISON_GATE**. Original-H
compatibility does not remove the prior force-interval failures (27 versus
25 previously). Do not adopt these diagnostic forces or rerun this frozen
entry. This is not structural failure, a new support episode, an authenticated
fourth response, or joint acceptance. It confirms that symmetrization alone
is not a sufficient reproduction remedy.

After execution the parent independently verified all 62 frozen input hashes,
the assessment output pin and response hash. The native launch count remains
unchanged. Next work is bounded read-only diagnosis of the saved failed rows;
no solver-setting campaign, mask retry or geometry change is queued.

Assessment SHA-256: `5143ece6f25b6240722493c789c1de8fca16ab4e7f564ba906c4551448c107bc`.
Response SHA-256: `2ada6877988c573fbfe89bb47b9945e774a8c373c250ad136e1124943ffa1a97`.

The table's maximum absolute differences are over each full comparison vector.
Among the 27 failing force rows alone, the largest difference is
5.15564756e-6 N at source row 381 (`contact_8_1`), just beyond its
5.00000077e-6 N allowed interval. Failures comprise 18 unilateral, eight
bilateral and one held-tangent row. These discrepancies must remain visible
without being described as a physical strength failure.

A separate parent saved-array audit reconstructed q from the frozen H/D/e
and recomputed all 50 body residuals and the original 128-epsilon interval
checks. It exactly reproduced all 27/0/0 failed positions and the saved q
vector, without assembling or solving another system. Bound q-minus-mu
discrepancy is 3.6093e-13 mm.
