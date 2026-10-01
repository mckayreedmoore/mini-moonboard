# Implicit bounded contact capture — attempt06 hardening

Attempt06 is an offline-only source-delta package based on the exact archived
source input carried by attempt05. The archive SHA-256 is
`9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7`.
Attempt05's `source-pins.json` SHA-256 is
`a671a0c53266cfae4986c403d63fb31c9180c8fafbf885e5018e52621efb2570`, and its
patch SHA-256 is
`e536c707f83c9ef11ffdfc55480d750ffd7b9dc68a73abd3e72c648eb20b4dba`.
Attempt06 preserves those files and regenerates a complete additions-only
patch against the same pinned source archive; it is not a patch layered on top
of attempt05's generated patch.

The writer and reader now enforce the frozen energy invariant: when `nener==1`,
every generated trial point must have a joined, enabled, finite energy row, and
the accumulated energy must remain finite. The writer leaves trial and run
completion false when that evidence is missing or invalid. The reader enforces
the rule unconditionally, so a caller setting `require_energy=false` cannot
accept an incomplete `nener==1` stream. With `nener==0`, energy rows must be
absent and the summary value must be `NA`.

Capture generation starts only in the `iexpl<=1 && mortar==1` branch that also
contains the corrected-state, trial, and iteration-link hooks. Explicit
execution remains outside this capture contract and cannot start a generation
that later lacks an iteration link. The package adds offline controls for
multi-step explicit execution, no capture path, destination collision without
overwrite, provenance-hash mutation, and combined pass-1 plus pass-2 row-cap
overflow.

The attempt06 source pins record readiness and native-execution authorization
as false. No current-joint input is frozen. No Docker build, patched solver
build, or native solver run was performed. The patch only adds capture code;
it changes no solver arrays, contact law, loads, controls, or contact decisions.

From this directory, run the offline controls with:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -v
```

The suite compiles and runs only standalone C sink harnesses. It does not
compile the patched CalculiX sources, invoke Docker, run a solver binary, run a
coupon, or freeze a current-joint input. A passing suite establishes offline
reader, sink-harness, and patch-preparation behavior only. The attempt06 packet
is being handed off for three fresh independent reviews; readiness and native
execution remain false pending parent validation.
