# Current ordinary-joint material mapping

The [material map](material-map.json) binds the current three timber members
and sixteen hardware-envelope mesh owners to explicit elastic scenarios.
The cleat's longitudinal grain follows local N, the rail's follows X, and the
principal's follows T. Two right-handed radial/tangential alternatives retain
the uncertainty in stock orientation. These are recorded material assumptions,
not measurements of delivered wood or accepted joint properties.

Four mutually exclusive input fragments combine those two grain alternatives
with either generic elastic assignments for all sixteen metal envelopes or
four nut element sets reserved for a later rigid representation. Select one
fragment; do not combine them. The nuts are solid cylindrical display envelopes
without internal bores. Assigning generic steel to those envelopes does not
establish physical nut compliance. The reserved branch emits no rigid-body or
thread-engagement constraints itself. Neither branch is a complete response
model, and none has been selected for a native joint run.

The parent froze the producer and fragments against the current STEP inventory,
mesh report, saved deck, material-source documents and helper hashes; see
[parent-freeze.json](parent-freeze.json). The map SHA-256 is
`9e1cbc8945d33683de3cb71ba716581919f508466d8a27b181865da4cc675fd4`.
The fragments contain material, orientation and section assignments only.
No loads, contacts, restraints, capacities or solve steps are added.

All four focused material tests pass, including a forced fresh-checkout path
that verifies every archived mesh member before reading the two required mesh
files. The parent ran these with the twelve changed access tests: sixteen
passed. The numerical response and material sensitivity remain to be evaluated.
