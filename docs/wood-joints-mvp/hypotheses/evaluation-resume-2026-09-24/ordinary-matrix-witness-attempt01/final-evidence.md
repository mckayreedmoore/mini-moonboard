# Final artifact evidence

The final producer and focused test snapshots now match their live files byte for byte. SHA-256: producer and `producer.py.snapshot`, `681602021c6802dcad860b0461d49fe45dea5b920e7ab05dabad5bbd134e0b73`; tests and `tests.py.snapshot`, `4676bad9cb1f82d20547060fd5e93a4731041a9c329b884d8db60ddb566434e5`. The frozen `audit.json` hash is `ff4b701f4df42b45e8e69c914a7208c822f1673148125755df4a697a34d74413`.

The audit's `.sti`, `.dof`, and input-deck hashes still match attempt04 (`dbea44f6ecc01d9aec870dc347f04215540938f949910c545da945c5add9a06e`, `965347fe1eaa33fe1e8f8025bc0a79a51447d501ff61f06f9541b8982303ad0b`, and `1508d20c992f739896f071c15a21cd7f31b5d964d5d8d7e3c210147effb96817`). Every source path recorded in `audit.json` matches its recorded hash. The report additionally records native-log hash `26f92623834d781cac0ea73d502f3aa6d8f058512e49c5e7a7e88eea095caa8a`; that matches attempt04's `preflight.log`, though the report has no corresponding `source_paths.native_log` entry.

`pytest -q tests/test_wood_joint_current_matrix_witness.py`: **13 passed**. Findings are unchanged: the declared cleat-only translation passes this one unloaded tangent witness with scaled residual `1.3753733031805013e-12`; the affine-strain comparison has positive quadratic form. The artifact makes no total-nullity, response-readiness, capacity, or structural-acceptance claim.
