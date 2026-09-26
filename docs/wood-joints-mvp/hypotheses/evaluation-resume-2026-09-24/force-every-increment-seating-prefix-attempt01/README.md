# Force-driven seating diagnostic: twenty-state capture

The parent captured an immutable output prefix on September 25, 2026,
12:06:14–12:06:15 UTC, while the source calculation continued. The captured
status file records 20 accepted increments through 0.020 s with no rejected
attempts. This is not the requested 0.025 s terminal result.

The source is `ordinary-transient-seating-100n-every-increment-k1e4-attempt01`.
All 27 input artifacts matched its frozen input map immediately before the
capture. Input-freeze SHA-256:
`f054d6b911fb0d9c9b0a183fa007d16d8a34a422904fd5cbcf73634e87797e66`.
Snapshot manifest SHA-256:
`001cefdb37a52bdf6bc6d1d590310c93d91d7f5b2f7cf0a35ad2e10c097e0d8a`.

The parent copied STA first, then DAT, log, FRD, execution metadata, and the
input freeze. Each binary copy was limited to the source file's size when
opened and hashed during copying. The six files are not atomic with one
another; absent or partial state fields must remain unavailable, and any
later fields do not extend the accepted-time coverage of this snapshot. No
CEL file was copied. No live input, native binary, or geometry changed.

At the last recorded state, the weighted displacement coordinate is
0.851846561 mm, maximum loaded-node displacement is 0.700740980 mm, and maximum
nut-controller rotation norm is 0.000919007 rad. The rotation trend changed
from the preceding increment. These observations motivate contact inspection;
they do not establish bolt/bore contact onset, complete seating, numerical
accuracy, or joint acceptance. Separate work, contact, and energy audits use
this fixed capture rather than growing source outputs.
