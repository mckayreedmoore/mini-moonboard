# Shared-edge motion fixture: input-reading failure

The first frozen case, `shared_slave_motion`, exited with code 201 after
0.319 seconds while reading the input deck. Docker records
`OOMKilled=false`; no solution increment was accepted. The second case,
`cross_role_motion`, was not run under the frozen stop-on-failure rule.

The first native fatal error is on the first `*NODE` row, whose coordinates
are printed as `0.0000000000000000E+00`. Later errors report undefined nodes
and a failed prescribed-motion boundary card. These are input-reading
failures, not a mechanical convergence result or evidence about the joint.
The parser diagnosis and any lexical correction belong in a separate packet.
All frozen inputs and captured outputs are retained unchanged.

Parent validation matched all 14 frozen file hashes and all
6 captured native-output hashes. The frozen verifier reports
`FAIL` because serial execution did not complete. Synthetic verification
passed before launch; this failure demonstrates that those checks did not
establish native lexical compatibility.

| Artifact | SHA-256 |
| --- | --- |
| `input-freeze.json` | `7993e5a5b1fd025e302d1a9d77a167bb7ab19e09a002fd5b9ccb8697b20761da` |
| `execution.json` | `2748ad7e155d7d3f0b0f4d2d8e4148723d6cbb7ffd452b402cd9772514fb13d6` |
| `verifier.py` | `4e10a3a565be8e12c880fab198a09919dd638e992559d2b090216f165f7868ec` |
| `verifier.json` | `1c35d067269fb231ab6a35965099cd3748b4ca6a16c04f9e1dcff331a7d3e35e` |

No method applicability, current-joint mechanics, structural criterion, or release is accepted.
