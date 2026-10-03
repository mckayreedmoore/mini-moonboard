# Independent single-run result review

**Disposition: clean bounded source-recovery run; row 1586 remains an RF
interval miss.** This review is limited to saved run artifacts and arithmetic
on reported values. I did not parse `.sti` triplets, refactor stiffness,
recover any source state, retry the runner, or launch a native solver.

The frozen parent input still hashes to
`a4f0ba75a5a3d46b047880ea4b6feae7df40470be1ca921ef78da398261b537a`. The
result file hashes to the requested
`560352a02ab4e01291f1c0d73db5f9001a71a38d8f9c3212962fb0cd586432b3`.
Its runner and source-manifest hashes match the frozen values. Independently
hashing the 22 pinned inputs, the frozen packet copies, and `uv.lock` found no
mismatch. The reservation’s before-run input map equals the execution record’s
after-run map; the execution record reports stable review hashes and no
postcheck error.

The saved external approval matches the parent reservation and the consumed
one-shot marker: approval SHA-256
`7cda6ca6cb107fd8cf37334c9743593d1a9f8d8aa6d69e2059ef39a6a6251859`, marker
SHA-256 `04c24cbe5f187159f2f741563f0fd71c63c1ea8eb202638f99d54cb8c41a52af`.
The parent wrapper hash also matches its reservation. The wrapper checked the
exact freeze, pinned snapshot copies, runtime, and idle shared-ledger slot;
held the ledger lock during the child process; set CPU and address-space limits
before Python imports; configured the numerical thread variables to one; and
ran the recorded command once. The execution record is terminal, return code
0, not timed out, with 5.231 seconds wall time including startup. The runner
reports 4.997 seconds CPU and wall time under its 60-second limits, a 2 GiB
address-space cap, two body factorizations, one source-triplet parse pass, and
zero native runs. It records zero corrections for each body. Configured thread
and memory limits are recorded; peak memory and actual OS thread count were
not measured.

The terminal files match their recorded hashes: stdout is
`METHOD_PASS_SOURCE_ROW_RF_MISS factorizations= 2 native_runs=0`, stderr is
empty, and the copied result matches the external report digest. The one-shot
marker is present and the execution record prohibits retry under this attempt.
The shared ledger is currently idle and contains no row-1586 recovery entry.
It has 60 total records now, compared with the 59 observed at reservation;
the execution artifact records the post-run idle slot but not the final record
count, so this review does not attribute that later count change.

The result identity is the frozen candidate
`compact-floor-flush-wood-joints-development`, revision
`led-clearance-2x6-runner-seated-blocks-v1`, row position 1586, inventory index
1786, `SPR1787` element 3690, and the two frozen owners. Their dimensions are
20 nodes/60 DOFs and 92 nodes/276 DOFs. Both method screens pass with no failed
gates. The reported raw loads close against the saved body residuals within
`8.9e-15 N` for `base_rail_service_lower_left` and `5.4e-15 N` for
`left_service_inner_lower_cleat`; their maximum rigid-load components are
below their respective balance thresholds. The operator leakage ratios
`7.42e-15` and `1.18e-14` are below the unchanged `5e-14` screen. These are
source-method results, not mechanical acceptance.

The sparse extraction totals reconcile: 2,320,506 unique upper pairs, 1,051
explicit zeros, and 4,601,263 reconstructed symmetric nonzeros, with all
diagonals present and no cross-body nonzero. Selected upper-pair counts are
1,830 and 11,010; adding 2,307,666 non-target same-body pairs and zero
cross-body zeros returns the global pair total. Only the 60×60 and 276×276
selected blocks were stored; their post-zero-elimination nonzero counts are
3,600 and 21,740. The report records no global stiffness rebuild and includes
both selected-block CSR digests.

Arithmetic on the reported endpoint coordinates and MPC displacements
reproduces `dd0 = 99.9999999999623 mm` and `dd - dd0 = 9.140037064980788e-7
mm` within floating-point rounding. `B*u` differs from the reported linear
endpoint-axis projection by `2.02e-15 mm`; finite-span extension differs from
`B*u` by `7.41e-15 mm`. The reported table force is `0.0036339103697834957 N`.
It lies inside the separate saved native table-force interval, but is above
the unchanged native endpoint RF interval’s upper bound
`0.0036338213363197223 N` by `8.9033463773410815e-8 N`. The resulting
`ROW1586_OUTSIDE_UNCHANGED_NATIVE_RF_INTERVAL` status is consistent with the
numbers.

The run preserves `STOP_PHYSICAL_OR_SOURCE_COMPARISON_GATE` and all 27
original force-interval failures. It records no force adoption, interval or
gate change, new case/state selection, full-frame solve, global rebuild, or
physical/design acceptance. The RF miss is the reported comparison outcome;
the method pass does not resolve the overall STOP.
