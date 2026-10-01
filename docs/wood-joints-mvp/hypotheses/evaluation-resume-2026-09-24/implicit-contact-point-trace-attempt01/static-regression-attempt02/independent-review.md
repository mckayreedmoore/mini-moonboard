# Independent review of the matched static regression

I independently checked the frozen attempt02 inputs and both native captures
with the packet's read-only verifier and pinned attempt01 parser. The freeze
SHA-256 is
`0fc873314b989e5a5d9de2a77310a05d8299dfd0783101e1a85ccfaf5483dbcf`; the
expected record SHA-256 is
`7b0d7fc5aa1dd5c01dbe71d7cace95942a2a3f65a6ddbdbe118f289b318e82c9`. The
freeze covers nine local files and fifteen external source/build dependencies.
Both captures used the frozen coupon input SHA-256
`73f32786bf6dee6c88e78f8e3d4e24f67afb9548225868fd10850c77e27298ab`.

The recorded case order and Docker state timestamps confirm the runs were
serialized. The old container started at `21:09:24.291946779Z` and finished at
`21:09:24.503142868Z`; the trace container started later, at
`21:09:24.725067108Z`, and finished at `21:09:24.935718228Z`. Both containers
exited with code 0, were not OOM-killed, and report the frozen image IDs and
binary identities. Both commands use one CPU, one solver thread, 1 GiB memory
and memory-plus-swap, and no network. Captured output sizes are 551,225 bytes
for old and 1,734,725 bytes for trace, each below the 16 MiB cap.

The paired outputs pass the unchanged comparison gates. The following hashes
are the actual captured file hashes from old and trace, respectively:

| Output | Old SHA-256 | Trace SHA-256 | Result |
|---|---|---|---|
| `coupon.12d` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | same | byte-identical |
| `coupon.cel` | `0b6dc846387e97c18464eab5ce7ee0709c2cdfde85620496e479dd99e5b1988c` | same | byte-identical |
| `coupon.cvg` | `45d0efb9264d8dc755e7c4096ef8f821887c16120c3b5ad2de0c800f1f72adc2` | same | byte-identical |
| `coupon.dat` | `0377ac55cc4c55cc6e5c35b48ab906a4386dd2f9b52e827fcb095b4848027c17` | same | byte-identical |
| `coupon.sta` | `62cd9c24c1fb208d227c0afc5970741a0bfaa41b73c1d6a39ab98acc4999d32d` | same | byte-identical |
| `spooles.out` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | same | byte-identical |
| `coupon.frd` | `d535fc83e767b55443820af99c8585794173e391aa37612003f4fddb17ea25c9` | same | equal after the single `1UTIME` normalization; normalized SHA `d9e59635235aaaf7052980196734a9f75c25b1f9090234659adaf4d53fcbe690` |
| `ResultsForLastIterations.frd` | `9f020065a769cf6a3ab8a5ca766ad6a4d9f7a06de9972c5e941ae4d172a3e523` | same | equal after the single `1UTIME` normalization; normalized SHA `a724f885890c9ff14caebef1e0d2bde52cdc838026379087c3c55954d67c8738` |
| `solver.stderr` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | same | byte-identical |
| `solver.stdout` | `96f289f5d42a44ad1f668d79a6cce758d6ccd809b8d74c6120a60c6522c80322` | `7aac85a60be2b8cccff79d7e90fe0120db436b094ece663f16d6d7721c26767b` | trace records are present only in the trace case; inherited events match |

The parser found 24 inherited event records in each capture: 8 attempt04
contact-count events and 16 convergence events. Their lines and order match
each other and the historical baseline, with the pinned event digest
`ad68cfa1029e76441b3a41b11ede539e1d18d8ad9198d01761bb36e674eb2ae3`.
The trace capture contains 1,680 finite `CCXPT_MAP` rows, 1,680 finite
`CCXPT_TRIAL` rows, and zero `CCXPT_UNMAPPED` rows. All 1,680 map rows have
nonzero native `isol`. Trial rows cover all 16 CVG identities, exactly match
the per-state native contact-element counts (56 for each of the first two
states and 112 for each of the remaining fourteen), and have unique element
and Gauss-point IDs within each state. Trial spring energy is unavailable in
all rows because `energy_enabled` is zero; the emitted zero placeholders are
not treated as measured energy. No generation-to-trial state join is claimed.

The verifier record SHA-256 is
`546a3fe1d1a6a53007eed820be9badeeea5064f22b3708049f5e1375111ef71c`; its
status is `PASS_MATCHED_STATIC_REGRESSION_TRACE_CAPTURE`. This establishes
matched-resource output equivalence for this static coupon and complete trace
coverage under the frozen contract. It does not qualify force, mechanics,
physical contact, or the current joint; mechanical acceptance, force
qualification, joint acceptance, and release remain false.
