# Current SPRINGA frame first-increment diagnosis

This packet diagnoses the terminal first-increment result from
[`current-springa-frame-a12-rear-attempt01`](../current-springa-frame-a12-rear-attempt01/README.md).
It records the observed cutback pattern, the relevant pinned CalculiX 2.23
source and manual evidence, and a bounded unchanged-physics control diagnostic.

The exact solver source archive, local manual, native run, and source-member
hashes are pinned in [`source-pins.json`](source-pins.json). The diagnosis and
limits are in [`diagnosis.md`](diagnosis.md).

This packet contains no solver inputs and runs no native analysis. A separate
parent-owned controls attempt is outside this packet; its result is not assessed
here. No force from the failed first run is a usable demand, and no solver
convergence establishes joint acceptance.
