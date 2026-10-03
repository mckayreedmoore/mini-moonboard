# Fresh gravity-frame demand export

Prepared [producer](knee-bridge-response.py): parent execution follows a complete
gravity-frame response. SHA-256:
`15c1121c54120c3aaba2bb295d6ac434d5384884be7dc6b5f2c6d03858c8df5d`.

Call `build(output, comparison_path, expected_comparison_sha256)` with a fresh
immediate child of `rawlocal/knee-bridge-response/` and the exact saved comparison
hash. Import performs no arithmetic, solves or writes. The parent supplies the
comparison only after its twelve zero/nominal states are complete.

The export contains **624 fresh nominal global bolt states and 396 screw
states**, with signed axial demand, each lateral plane's components, and the
simultaneous peak screw records. It compares new forces with the original
global vectors and records the largest changed row in each of the six cases.
It preserves the original 250 lb × 2, signed 300 N, original hold lever and
unchanged screw laws. All consumed source/output byte bindings are checked.

The [integration manifest](knee-bridge-integration.md)'s **24 internal bolt
allocations remain separate**. They are not new global connector rows and are
not recomputed by this export. Historical local reallocations, member checks
and component acceptance stay tied to their original force fields. This
producer supplies fresh demands only; it establishes no new resistance,
actual changed-hole stiffness, compatibility, adoption or physical release.

Ignored children retain the source snapshot, `global-demands.jsonl`,
`summary.json` and a source/output `receipt.json`. No software tests, review
loop, native/CAD runs or additional force solve are part of this export.
