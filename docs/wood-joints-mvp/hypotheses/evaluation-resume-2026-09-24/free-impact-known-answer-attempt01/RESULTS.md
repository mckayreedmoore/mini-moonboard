# Free-impact attempt01: verifier classification failure

Date: 2026-09-27. The frozen paired test remains **FAIL**. Both pinned binaries
completed all 70 increments normally, without timeout or OOM. The original
solver passes every analytical/output gate. The trace case fails the frozen
MAP pressure-law identity gate: acceptance incorrectly expects ID 1, while
all 7,896 MAP rows report ID 2.

Pinned `surfacebehaviors.f` maps `PRESSURE-OVERCLOSURE=LINEAR` to `L` and
assigns `elcon(3,1,imat)=2.5`; the diagnostic patch emits its integer
truncation, 2. The surface-to-surface formulation mode 1 is a separate value.
The native deck selected the intended linear law. This was a verifier
classification error that the preflight review missed.

The original [verifier result](verifier.json), input freeze and native outputs
remain unchanged. A separate reproducible
[diagnostic](parent-law-id-diagnostic.py) changes only the expected law ID in
memory. Its [record](parent-law-id-diagnostic.json) passes all original
numerical tolerances, accepted-state checks and baseline/trace comparisons.
It does not change the frozen attempt's failed status. The separately frozen
[attempt02](../free-impact-known-answer-attempt02/RESULTS.md) now passes its
fresh native pair with the source-correct ID declared before execution.

The diagnostic checks 7,896 MAP and 5,544 TRIAL rows, with no unmapped rows.
There are 141 CVG iteration identities: 99 contain complete 56-point TRIAL
sets and 42 contain zero contact points and no TRIAL rows. At increment 50,
iteration 1 retains 56 old-set positive-gap trials; later regeneration removes
them. Accepted increments 50–70 have zero contact force and contact energy.
The numerical reference's release energy change remains the frozen
0.0856326% discretization effect, not a claim of exact energy conservation.

Both cases have identical diagnostic error maxima: DAT displacement
4.94e-11 mm, FRD displacement 4.62e-10 mm, DAT velocity 7.16e-9 mm/s,
FRD velocity 1.93e-7 mm/s, body strain energy 4.09e-34 N·mm, kinetic energy
4.97e-10 N·mm, contact energy 4.88e-10 N·mm and CFN component 4.80e-6 N.
These are fixture numerical checks, not current-joint mechanics or capacity.

The input freeze SHA-256 is
`534d22546dc808e97fedd0c3ac82b77aec8ff4f4230a5e64de471c57ff245637`.
The baseline used 1,174,592 output bytes in 1.14 s; the trace used 5,989,151
bytes in 1.25 s. Runs were serialized, one CPU and 1 GiB each, with unchanged
60 s and 16 MiB limits. No reviewed candidate geometry changed.
