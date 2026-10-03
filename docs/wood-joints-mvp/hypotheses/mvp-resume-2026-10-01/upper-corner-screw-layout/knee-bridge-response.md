# Fresh gravity-frame demand export

Completed [producer](knee-bridge-response.py): parent exported the complete
gravity-frame response's nominal demands. SHA-256:
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

## Completed fresh census

All nine source pins and four receipt artifacts match. **624 bolt and 396 screw
records** cover the six nominal cases. Largest row-force change is **1.418113 N**
in A12-rear; other case maxima are 0.637–1.326 N. Upper-left `edge_2` retains
the peak axial screw demand **1871.246 N** with simultaneous lateral **726.730 N**.
Peak lateral screw demand is **1244.128 N** at upper-left `rim_4`, with axial
**674.389 N**, also A12-rear. These demands leave the recorded panel references
exceeded; no hardware resistance or observed physical failure follows.

| Artifact under `rawlocal/knee-bridge-response/attempt02/` | SHA-256 |
| --- | --- |
| `summary.json` | `da8fcfde95eda2fb6967194c1060e5b55647eeb1ea98efa25e8a9e8260294c70` |
| `receipt.json` | `57163aa9f4e1ed7af338d29c4893f5614c21bd422e841532cf67feb67ac20933` |

Source comparison SHA-256:
`c3a8ff024fb494032d947aedfd6f00cda8698587b8751b2cec66e4b3af243729`.
