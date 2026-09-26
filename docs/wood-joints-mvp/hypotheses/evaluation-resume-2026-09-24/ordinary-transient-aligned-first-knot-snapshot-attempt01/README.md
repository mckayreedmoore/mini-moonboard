# Aligned diagnostic: immutable first-knot snapshot

This snapshot preserves the first accepted point at 0.001 s from the running
aligned 100 N reference diagnostic. It includes DAT and FRD outputs read
unchanged across capture, the source input freeze, and log/status prefixes
ending before increment 2. [snapshot.json](snapshot.json) binds their hashes
and records that the source process remained live; this is not a terminal
execution record.

Stable bytes do not establish complete output. The DAT contains 100 of the
105 requested pair-statistics reports: pairs 001–033 have complete triplets,
pair 034 has only part of its CF report, and pair 035 is absent. Pair 034's
zero force and NaN centroid/normal are present; its later fields are missing.
The [contact audit](../aligned-first-knot-contact-audit-attempt01/README.md)
preserves this distinction. The motion and energy records cited below are
available, but this snapshot cannot establish the state of all 16 bore pairs.

The increment converged after 25 iterations with q=2.3186867121e-5 mm,
maximum loaded-node motion 1.85158802e-5 mm and maximum controller rotation
6.64389479e-8 rad. The actual force is 0.0298 N per side at this knot.
The prescribed force impulse is 1.49e-5 N s per side, now identical for the
linear ramp and endpoint trapezoid on this interval.

Native external work is 3.454843e-7 N mm, internal energy 4.795230e-8,
kinetic energy 2.971466e-7 and elastic contact energy 4.636793e-9 N mm.
The reported energy discrepancy is 4.251326e-9 N mm, or 1.230541%.
Matching prescribed impulse does not explain or close that discrepancy.
The independent work and momentum audits are separate from this capture.

q is a finite-patch displacement observation. It need not equal the isolated
rigid-pair translation estimate, and its difference alone is not a momentum
error. Local deformation and subsequent contact behavior require actual
field and per-body accounting. This point does not establish bore seating,
time accuracy or joint acceptance. Raw DAT/FRD files remain local evidence.
