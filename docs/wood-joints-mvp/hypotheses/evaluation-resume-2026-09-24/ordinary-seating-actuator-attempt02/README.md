# Ordinary-patch seating actuator input — attempt 02

**Superseded for coefficient text serialization.** A later audit found that
218 of 663 attempt-02 coefficient tokens exceed the CalculiX 20-character
`F20` field; six exponent tokens are truncated and fail to parse. Preserve
this attempt's report and deck as history, but use
[attempt 03](../ordinary-seating-actuator-attempt03/) for the bounded text
representation. The work-conjugate physical wrench pattern is unchanged.

This folder contains a linearized relative-displacement actuator input only;
it does not contain a seating response case. Attempt 02 adds six helper-source
hashes to [`actuator.json`](actuator.json), while the parent verified that its
[`actuator.inp`](actuator.inp) bytes are identical to
[attempt 01](../ordinary-seating-actuator-attempt01/). The deck SHA-256 is
`9c52cb6d7dd3f2118799e2b6b91f0cc51e03a7a1bc78cd5b5208842a1a975bd8`; attempt
02's report SHA-256 is
`66f16b3a6157780c563fa03ad976e0caccd6d604023fa007432dec1da2e1054d`.

The scalar observation is
`q = u_cleat·N − u_principal·N`, linearized at the common source datum
`(89.05, 42.906715329, 486.256134997) mm`, where
`N = (0, −0.766044443118978, 0.6427876096865394)`. Reference node `117162`,
DOF 1, is the independent actuator coordinate. The equation carries 662
physical coefficient entries dual to paired `+N` and `−N` unit-resultant
wrenches: 151 cleat nodes and 180 principal nodes, each with two in-plane
force components. Their reconstructed force and moment residuals are recorded
in the report.

These are work-conjugate measurement coefficients, not applied loads. The
deck prescribes no actuator value and contains no analysis step or external
load. No native solve was run. All other relative motions remain unconstrained;
global supports, preload, friction, and stabilizing stiffness are absent. It
also assigns no joint stiffness, seating force, material response or capacity;
physical thread engagement remains unverified. The current
[rigid-mode matrix preflight](../ordinary-rigid-preflight-attempt01/README.md)
precedes a separately bounded seating case. This input is setup for that later
case and does not replace it.

The report pins inventory, contact classification, mesh deck and mesh report
hashes. Its `helper_source_sha256` field lists the six source pins added in
attempt 02.
