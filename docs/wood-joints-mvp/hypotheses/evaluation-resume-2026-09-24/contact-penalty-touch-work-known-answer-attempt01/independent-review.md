# Independent native-evidence review

Read-only review of the completed exact-touch penalty work fixture. No inputs,
outputs, verifier records, or native execution artifacts were changed.

## Identity and integrity

The 10 entries in `input-freeze.json` and all 9 entries in
`output/penalty_touch_work/execution.json` independently re-hash to their
recorded SHA-256 values. The captured `coupon.inp` hash matches the frozen
input deck hash. Native execution records the pinned image and binary hashes,
Docker CLI and container exit code 0, 0.421 seconds elapsed, and
`OOMKilled=false`. `coupon.sta` records five accepted increments at times 1–5,
with one increment per step and 3, 7, 3, 5, and 2 Newton iterations;
`coupon.cvg` contains the corresponding 20 iteration rows.

## Raw response checks

From the raw DAT nodal rows, mean TOP U3 is
`[0.001, 0, -0.005, 0, 0.001] mm`; summed TOP RF3 is
`[2.157945e-9, -2.578611e-26, -399.519900, -6.840552e-16,
-1.083670e-14] N`. Independent trapezoidal integration, including the
initial zero-displacement/zero-reaction reference, gives segment work
`[1.078972e-12, -1.078972e-12, 0.99879975, -0.99879975,
-5.760380e-18] N·mm`.

Raw DAT ELSE plus CELS endpoint energies are
`[2.32843e-23, approximately -4.0e-40, 0.9991998,
-1.128759e-19, -1.128759e-19] N·mm`. The compression and unloading
work/energy differences are respectively `-0.0004000500` and
`+0.0004000500 N·mm`, within the frozen work screen. At compression the two
body ELSE values are each `0.3998398 N·mm`, penalty CELS is `0.1995202
N·mm`, and their sum is `0.9991998 N·mm`. Tiny negative unload values remain
as printed.

The raw DAT contains all 15 finite SLAVE/MASTER CF, CFN and CFS identities.
At compression CF and CFN are `(approximately 0, 0, 399.5199) N`, with
origin moments `(399.5199, -399.5199, approximately 0) N·mm`; CFS is zero.
The exact-touch CF norm is `6.84e-16 N`. The 10 raw section-resultant rows
are finite; at compression the opposed force and origin-moment closure norms
are `2.55e-9 N` and `8.05e-14 N·mm`.

The raw FRD contains five fields each for DISP, FORC, STRESS, CONTACT and
ERROR. Every DISP, FORC and STRESS field covers all 54 mesh nodes with finite
components; CONTACT rows are finite as well. At compression the recorded
contact field has COPEN range `[-0.0009988, 0] mm` and CPRESS range
`[0, 99.88]` in the deck's units.

These checks support the bounded two-body method-fixture result recorded in
`RESULTS.md`. They do not establish a current-joint constitutive or resistance
claim. In particular, the fixture has explicit exact-touch path breakpoints;
it does not qualify unresolved open-gap quadrature, shared-edge MPC behavior,
curved-bore onset, or structural acceptance. MORTAR was not used. The frozen
verifier's remaining inherited mechanical threshold assertions are retained;
this note independently checks the output identities and principal raw
quantities above rather than restating every threshold calculation.

## Source hashes

| Artifact | SHA-256 |
| --- | --- |
| `input-freeze.json` | `9cf04eb2d38c5a82ddf050535a0a303043176bb17cedf76e09b328d961d9bcc4` |
| `expected.json` | `053039f39b33c5e3c1f1d1d19e88e8fa9967d6da7aea42fd9450bf80b56d1a26` |
| `verifier.py` | `f0a4684eee8895d8196206e7431b676cf8c4c76e384cd9c6dfac543de1eee30f` |
| `pair_output.py` | `c729729c9f7d520dfaa4d835e5a0c2ce633ab9e12e0e60aef931b1c98df03496` |
| `verifier.json` | `6becb6d9c4cc875bcb06379078e97f86c2108318ef3df76a20f6b3c8be693bcd` |
| `execution.json` | `c399472c88fb5c225c7774159eec199a935af688d55c4b74d80b74df47ed6c05` |
| `output/penalty_touch_work/execution.json` | `8a33e6c7f305a1641e3be923d82aa0406c178e1bc61598ec0b5ecf22de702360` |

The nine native output hashes are pinned in the nested execution record and
were each independently matched to their files.
