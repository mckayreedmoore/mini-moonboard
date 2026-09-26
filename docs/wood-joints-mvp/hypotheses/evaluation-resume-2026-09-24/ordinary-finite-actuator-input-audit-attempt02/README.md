# Current-joint finite-actuator diagnostic readiness

The parent checked the final [input bundle](../ordinary-finite-actuator-k1e4-attempt02/input-freeze.json)
against the frozen current K1e4 source. All 23 source pins and 12 child pins
match. The physical mesh, materials, contact fragment, nut coupling, rigid
carriers and element output sets are unchanged. The node-file set adds only
the two massless drive nodes; the physical motion monitors remain unchanged.
The [independent input audit](audit.py) and [report](report.json) verify the
actual serialized cards, not just the producer's metadata. The producer and
transient/history checks pass 29 focused tests; Ruff and formatting checks
cover the producer, tests, launcher and independent audit.

This is ready for one bounded diagnostic, not a complete-joint mechanics
acceptance. The [scalar benchmark](../spring-actuator-validation-attempt01/README.md)
supports the massless dependent proxy and separate spring/target method.
The [current scale review](../current-finite-actuator-scale-attempt01/independent-review.md)
supports an initial 200 N/mm numerical actuator with a target rising to
1.15 mm over 0.1 s. The exact input contains 201 piecewise-linear samples of
the quintic ramp. Adaptive implicit integration uses alpha zero, initial and
maximum increment 0.0005 s, minimum 0.000001 s, and at most 10,000 increments.
All 42 output requests use frequency one. One node-file request retains the
physical and drive nodes for U/V/RF; DAT requests physical work-monitor U
and separate drive-node U/RF. The 35 contact-pair reports and global contact
records remain requested. There are no CLOAD or TIME POINTS cards.

The actual MPC is `q_proxy + sum(a_i U_i) = 0`, with proxy node 117162 as
the first dependent term and target node 117163 outside the equation. Use
`w_i = -a_i` from these serialized terms to reconstruct physical q; the old
normalized physical-dependent equation is not the new coordinate definition.
The largest difference from the original unit weights is 5.031e-17. Target
RF must be checked against `200*(q_target-q_proxy)` on the actual output.
Target work, the actuator's own energy, transferred work, physical energy
and contact diagnostics stay separate. The K1e4 contact penalty remains an
unadopted numerical sensitivity, and rigid nut coupling remains a diagnostic
engagement assumption. Neither is validated by this drive change.

The parent will run this case alone with four solver threads, a 10 GiB
container memory limit and a 10,800 s runtime bound. Existing sampled stops
remain q above 3 mm, loaded-node displacement above 5 mm, or nut-controller
rotation above 0.01 rad in magnitude. These are sampled diagnostic controls,
not continuous guarantees. A smaller-timestep comparison, full force/work
accounting, observed contact engagement and justified joint properties remain
necessary before interpreting this response as joint mechanics. No geometry
change or structural criterion pass is recorded.

Attempt01 is preserved as an unexecuted preparation snapshot. Attempt02 has
identical solver input bytes and removes two stale force-pattern metadata
fields while recording the final producer snapshot. Its input-freeze SHA-256
is `8ea71d56271212b39ef8fc948b0ac8d3d312fb7afd74480c512bf4d75572ba32`;
pilot SHA-256 is `840daddc53194bb2956d214d4e7d83cb69a21a93f3e830ab915f754ebc16791b`.
Execution status belongs to the case's separate execution record, once created.
