# Ordinary-patch seating actuator input — attempt 03

Attempt 03 is the corrected 20-character-safe serialization of the same
linearized relative-displacement actuator. It uses the same frozen inventory,
contact classification, mesh report, and mesh deck as attempts 01 and 02.
Their input hashes are classification
`18bdf1b9736ce6ca2cf2b3dd0488a7651da05f35e531605fd465e7b502363f13`, inventory
`70b396e636175abcad7467dc145029d7126c1ea7dff1d053a61f8c5321e1c1d3`, mesh deck
`117fdc67c8d3f7f7e3bf1df41d842c9d8e7fa57e1c941676bccd882878bb4803`, and mesh
report `1043bd4a7ac03e589d6f8819f98231b33a866ee917d1e9c7099d0104092d0a07`.
The report SHA-256 is
`cc452f06600b72e576616adcd16f521c38f8bdfdcc7d90029f4eee0fb461b9a7`; the
[`actuator.inp`](actuator.inp) SHA-256 is
`f6fe362a50b5ca0af17a22ebd9d7a4b4a0853d461950cceb5fe43e49ec52ccb5`.

The producer writes equation coefficients with `.13e` and rejects any
coefficient token wider than 20 characters. All 663 attempt-03 coefficient
tokens fit that width and parse as finite floats. The focused tests also check
very small positive and negative coefficients after serialization, including
work and observation reproduction within `5e-13` relative tolerance.

The physical owner wrench distributions and the 662 unnormalized physical
equation coefficients are unchanged from [attempt 02](../ordinary-seating-actuator-attempt02/):
equal/opposite 1 N resultants along N, distributed over 151 cleat nodes and 180
principal nodes. Only the normalized coefficient text representation changed.
The measured scalar remains `q = u_cleat·N − u_principal·N`, linearized at the
common source datum. Reference node `117162`, DOF 1, is its independent
actuator coordinate. The six current helper source hashes and matching
producer/test snapshots are recorded in this folder.

This is actuator input only: no actuator value, external load, analysis step,
or native solve is included. It supplies no seating force, stiffness, physical
thread-engagement evidence, material response, or capacity. The current
[rigid-mode matrix preflight](../ordinary-rigid-preflight-attempt01/README.md)
precedes a separately bounded seating case; this deck is not that case.
