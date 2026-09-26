# Independent review: finite-actuator momentum audit, attempt 02

The frozen producer (`audit.py`, SHA-256
`d03ee3ea95c00f7137a07cf8d3a5b474bfd5f0c03786686838a66eeb935bbf1f`) and
report (`report.json`, SHA-256
`b4a8ada753a7f00a6c1e5a3697d53a25e7cdb1ae07a6bc70a855eec99f2e9f95`) match
the supplied pins. The report binds the five-state snapshot and its mesh,
material, contact, DAT, FRD, STA, and serialized-input artifacts. The
parent-run record (`parent-execution.json`, SHA-256
`83a908620a33fb847b0c2e3943489f4fdb8db89df96aec698afed3deb75da24f`) also
binds the executed `dynamic_momentum.py` and C3D10 deck-parser helper hashes.
The producer does not itself hash those imported helpers; the run record
supplies that execution identity.

The report selects accepted states at exactly `0.0005`, `0.001`, `0.0015`,
`0.002`, and `0.0025 s`. Complete contact coverage is present at the first
four states only: 35 pairs with the ordered CF/CFN/CFS triplets at each
state. Exact decimal matching selects accepted-state indices `[0, 1, 2, 3]`;
there are three cleat intervals, and the `0.002`–`0.0025 s` cleat balance is
withheld because its final contact report is incomplete. The corrected
attempt01 ambiguity is therefore resolved.

The serialized MPC has 662 physical terms, bound by map SHA-256
`8e2385047929f0bcb61e737786697b4b378f79113204baa40ec9f6e4e79dfced`. With
proxy coefficient `+1`, `q_proxy + Σ(aᵢuᵢ) = 0` maps physical force as
`target RF × (−aᵢ)`. The reported cleat ownership map contains ten interfaces:
cleat-slave pairs 1 and 2 use `+CF`; cleat-master pairs 5, 9, 13, 17, 20, 22,
24, and 26 use `−CF`. Only the first-request total `CF` force is summed;
`CFN` is a duplicate output and `CFS` is not added. The global actuator
resultant is near zero as expected from the serialized weights, while the
cleat subbody receives the nonzero mapped resultant.

The two mass operators remain distinct: Gauss8 physical consistent mass and
the source-reconstructed CalculiX 2.21 four-point reference mass. The latter
reconstructs the untransformed reference operator; neither result claims
native equality for contact transforms or solver internals. The report
includes 15 positive-density bodies (3 wood and 12 steel), excludes four
zero-density nut carriers and massless controls, and reports global masses
of `11.7756009963 kg` (Gauss8) and `11.7756010093 kg` (four-point). FRD
velocity bounds account for binary32 conversion followed by `%12.5E` decimal
printing; DAT RF/CF and reported-time tokens use their decimal half-quantums.

I found one bound-propagation omission: the producer's actuator and contact
impulse bounds include each first-order product term but omit the product of
the time and force half-quantum bounds. The original report's rounding bounds
should therefore be read as first-order bounds. The token-only
[`rounding-bound-addendum.json`](rounding-bound-addendum.json) adds the exact
`δt·δRF_average` and `δt·δF_average` terms per interval and component. Its
reproducer is [`rounding_bound_addendum.py`](rounding_bound_addendum.py),
SHA-256 `9e29185f039da9a03c919f4693f72cd0cd6fdd96bd1bd91c20dd841ecca81c9d`;
the addendum JSON SHA-256 is
`d2128b99a1621bd2e8feafb65ba134c6261aff5e0c9b588fa9c2453e0f807977`. It
verifies the raw DAT, STA, contact-manifest, MPC, and mesh-report pins, re-reads
the serialized MPC weights and CF source tokens, and verifies the pinned
canonical contact-output audit against the frozen DAT. It does not integrate
mass.
The largest omitted cleat actuator cross term is `4.21325e-17 N·s`; the
largest contact cross term is `2.20165e-14 N·s`. The largest corrected cleat
component bound is `1.1268032881e-9 N·s`, versus a peak residual of
`1.9233600058e-11 N·s`. All 24 reported global component checks and 18
complete-cleat component checks remain within the corrected bounds. The
global cross terms are at most `8.8e-32 N·s` and do not change the stored
floating-point bounds.

This review does not rerun mass integration, the native solver, or CAD. It
accepts only the reported linear-momentum bookkeeping over this captured
prefix, with the second-order print-token terms supplied by the addendum. The
result is not joint strength, stiffness, thread-engagement, resistance, or
mechanical acceptance. Endpoint trapezoidal integration does not bound
between-increment force variation, cutback-time error, or solver equilibrium
residual; no impulse interval from `t=0` is available.
