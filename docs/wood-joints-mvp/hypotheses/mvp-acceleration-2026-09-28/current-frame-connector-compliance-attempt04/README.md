# Source-bound frame connector compliance, attempt04

Parent executed one serialized, single-threaded reduction under the shared native-ledger lock, with a 300 s CPU and 6 GiB memory cap. No native solve, contact-state selection or physical response was run. All 50 bodies passed in 34.382 s.

The original authenticated CalculiX solid K and DOF identities were retained. All source connector rows and all six separate gravity/climber load maps were retained. The elastic quotient uses the independently checked coordinatewise propagation of the unchanged nodal residual tolerance. Original residuals and nonzero gauge multipliers remain in the assessment; previous rejected attempts remain unchanged.

Outputs: H is 1840 by 1840, D is 1840 by 300, e is 1840 by 12 and W is 300 by 12. Source B is 1840 by 37647. The twelve load columns are six gravity/climber pairs, not six combined loads. Raw physical body wrenches remain in D and W: physical responses require D.T*f=W and q=D*a+e-H*f, together with compatible source laws and floor history.

H reciprocity error is 9.3832183e-11 versus the 1e-8 numerical criterion. The symmetric-part minimum eigenvalue is +2.3942328e-10 mm/N. Maximum chunk nodal relative residual is 9.2617201e-11. Maximum retained original elastic-column body force/moment residuals are 3.9161355e-5 N and 0.02892343 Nmm; these columns are basis terms, not accepted physical loads.

Replay provenance without refactorization: `OPENBLAS_NUM_THREADS=1 .venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-frame-connector-compliance-attempt04/build_compliance.py --verify-record`.

This clears the elastic reduction gate only. It supplies no new accepted load case, gravity-settled contact state, full-frame equilibrium result, bolt resistance, corner pass or fabrication release.
