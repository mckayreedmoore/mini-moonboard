# Testing result review — attempt 02

**Result: PASS for the frozen software-resultant fixture.** The single authorized run completed within its bounds, the output and audit hashes reconcile, the final output inventory is complete, and independent arithmetic on the raw final rows confirms the reported equilibrium. This result does not qualify a product, material, washer, or candidate joint.

## Provenance and completion

The receipt hash is `fa97942ad86cebfe1a35f0c1a50a05574a43b2a480d8f63a4ed9e1cc123d738d`; it binds freeze SHA `87894949d0f9aa45ca479fa290fb2ae8c354884d290b9ac0e13e2a902522c8aa`, execution SHA `f85c0e2fd531ac1d436d050445f19a1a0061011bbac3e8b5863439520d4ddb9c`, raw `.dat` SHA `e9c394487369fe2cda62bab88cce887d00a7608841b06a230a4d43ef894d2bc4`, and audit SHA `c7fd63db20195c398528d769305ee31676016a10622572541bbd0b252987a4db`. The current frozen inputs, authorization, launch wrapper, parent-readiness record, execution record, and captured output hashes match the receipt. The execution and receipt output maps agree for all nine `model.*` and `native.*` artifacts.

The authorization and execution commands match: pinned image digest, network disabled, one CPU, 1 GiB memory, and a 60-second timeout. The solver banner reports CalculiX 2.23. The container reached a terminal state in 5.596 seconds and returned 0. The `.sta` file records all ten increments, each on its first attempt, ending at time 1.0; `native.stdout` ends with `Job finished`, and stderr is empty. The parent ledger has exactly one matching run row, with one of one launches consumed and terminal; its active slot is idle. No retry occurred or is authorized.

The raw `.dat` contains ten output states for each expected nodal block: `GROUND` U/RF (160 rows each), `UPPER_GAUGES` U/RF (two rows each), and `LOAD_PATCH_NODES` U (45 rows). It contains one final CF, CFN, and CFS record at each state. The final ground translations and constrained gauge translations are zero. The verifier replay returned 0 and reproduced `frozen-output-audit.stdout` byte-for-byte; the stored audit JSON is identical to that stdout.

## Result checks

I independently reintegrated the final displaced pressure faces using the pinned three-point TRI6 rule, then summed the raw contact and nodal reaction rows about the origin. The pressure wrench is `(-0.00401963, -0.00401522, -36.737114) N` and `(-96.6745003, 96.6725598, 0.00002520) N·mm`. The raw CF and CFN rows agree at printed precision, with positive z force; CFS is zero. The independently summed ground reaction is `(0.00346348, 0.00346633, 36.737115) N` and `(96.6749114, -96.6731446, -0.00000206) N·mm`.

All frozen gates pass. The pressure-wrench difference between the solver’s discrete rule and six-point comparison is below `3e-14 N` and `2e-11 N·mm`. CFN and CF errors are `4.1e-6 N` and `8.4e-7 N·mm`, against limits of about `0.02735 N` and `0.07735 N·mm`; CF equals CFN and CFS is zero within the `0.01` limits. The ground-reaction errors are below `7.3e-7 N` and `0.000715 N·mm`. Gauge in-plane RF L1 is `0.001114 N`, below `0.023674 N`. Independently summed upper-body closure is `4.1e-6 N` and `8.4e-7 N·mm`; whole-model closure is `7.3e-7 N` and `0.000715 N·mm`, each below the frozen `0.1` limits.

The verifier consumes integrated force and origin-moment resultants. It does not parse the requested `CDIS,CSTR` fields or gate contact area, pressure distribution, or footprint. The pass therefore supports only the software load-transfer/resultant behavior represented by this hypothetical isotropic fixture. It does not establish local contact adequacy, actual material or hardware performance, joint resistance, candidate acceptance, fabrication readiness, or climbing release. Preserve this run as the sole launch for this freeze; do not retry it.
