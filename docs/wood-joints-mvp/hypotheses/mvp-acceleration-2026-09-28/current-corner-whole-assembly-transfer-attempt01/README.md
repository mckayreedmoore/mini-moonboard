# Complete corner boundary transfer from three accepted responses

This packet checks the left outer post/spine, side/inner-block and block/header
assembly as five connected bodies. It authenticates the A12-rear, A1-rear and
K12-rear exports, then sums all physical endpoint forces about the common
global origin. It changes no geometry or force, launches no solver and assigns
no resistance.

Every one of the 21 states contains 338 source interfaces: 42 internal and
296 crossing the assembly boundary. The boundary is retained as 62 signed
member/receiver/role ports. It includes floor support, panel attachments,
neighboring blocks and original frame interfaces. The assembly therefore has
several simultaneous load paths; it cannot be treated as three isolated
connections in one serial chain.

The equal/opposite internal actions cancel in force and moment. Maximum
internal cancellation discrepancy is 1.46e-11 in the reported N/Nmm
components. Reconstructing each body's interface wrench and transporting its
source residual to the origin agree with the direct endpoint sum within
1.16e-12 N and 1.84e-9 Nmm. Independent force/couple transport and collinear-tie
oracles run before processing the reports.

The complete assembly's external source loads are its own mapped gravity.
Its net boundary force at full load is approximately `(0, 0, +296.839) N` in
all three cases, balancing that gravity. This net sum includes substantial
incoming and outgoing transfers that cancel; it is **not** an individual
bolt/group design demand. The signed port wrenches and connection identities
remain in [assembly-transfer.json](assembly-transfer.json) for onward-transfer
checks. Maximum assembled residual components over all states are
0.000571 N and 1.827 Nmm about the origin.

Existing individual-body raw and interval gates must pass before each state
is processed. Assembly residuals are transported sums of those source
residuals, not a new acceptance test with widened tolerances. The source
`*_side_wrench_at_owner_datum` fields use a connection datum, not the body's
descriptor datum; this producer uses the explicit physical endpoint points
and forces rather than mixing those references. No endpoint free couple is
introduced by this conversion.

Source report hashes are embedded in [produce.py](produce.py) and the output:
the [A12 export](../current-corner-native-demand-export-attempt03/README.md),
[A1 export](../current-corner-a1-rear-case-bound-export-attempt01/README.md),
and [K12 export](../current-corner-k12-rear-case-bound-export-attempt01/README.md).
Output SHA-256 is
`01f4128989a5674f040c5d3a8ce9af3ed4523ec0266518989960a1345ad27f55`.

Reproduce from the repository root:

```sh
OPENBLAS_NUM_THREADS=1 .venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-corner-whole-assembly-transfer-attempt01/produce.py --verify
```

This closes a conditional complete-assembly boundary bookkeeping check.
Internal forces still require compatible member bearing/contact, continuous
bolt and group behavior, splitting and net-section checks, and axial/thread/
washer resistance. Three other load cases and physical stiffness/engagement
bounds remain open. Original LEG/runner resistance is reused; boundary
inventory does not restart its qualification. No fabrication or climbing
release is established.
