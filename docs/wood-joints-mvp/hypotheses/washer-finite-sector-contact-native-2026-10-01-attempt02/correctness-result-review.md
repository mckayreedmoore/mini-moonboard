# Correctness review: finite-sector contact attempt 02 result

**Decision:** `PASS_FINITE_CONTACT_RESULTANT_METHOD_FIXTURE` for the bounded software result only. This review binds to freeze SHA `87894949d0f9aa45ca479fa290fb2ae8c354884d290b9ac0e13e2a902522c8aa`, parent output receipt SHA `fa97942ad86cebfe1a35f0c1a50a05574a43b2a480d8f63a4ed9e1cc123d738d`, execution SHA `f85c0e2fd531ac1d436d050445f19a1a0061011bbac3e8b5863439520d4ddb9c`, frozen-output-audit SHA `c7fd63db20195c398528d769305ee31676016a10622572541bbd0b252987a4db`, and raw `model.dat` SHA `e9c394487369fe2cda62bab88cce887d00a7608841b06a230a4d43ef894d2bc4`. Every listed raw-output and audit-input hash matches. I independently parsed the final-time DAT rows and recomputed the resultants; the decision does not rely on the frozen audit payload.

The run used one CPU, 1 GiB, and a 60-second timeout. `execution.json` records exit 0, 5.596 seconds, and terminal container cleanup. All ten `.sta` increments reached time 1.0 on `ATT=1`. The raw DAT contains the requested final displacement and RF blocks for 160 ground nodes, both gauges, and all 45 pressure-face nodes (`model.dat:4004`, `model.dat:4167`, `model.dat:4330`, `model.dat:4335`, `model.dat:4340`).

Using the final pressure-face displacements and the frozen TRI6 coordinates, my independent current-face integration gives pressure resultant `(-0.00401963, -0.00401522, -36.73711402) N` and origin moment `(-96.67450027, 96.67255980, 0.00002520) N·mm`. Current patch area is 18.36855724 mm² and centroid is `(2.63163261, 2.63168525, 1.49947558) mm`. The pinned three-point solver rule and the independent six-point rule differ by `1.42e-13 N` in force norm and `1.55e-11 N·mm` in moment norm, below the unchanged 0.02 N and 0.05 N·mm limits.

The raw final contact records at `model.dat:4389`, `model.dat:4408`, and `model.dat:4427` report:

| Check | Observed | Frozen limit |
| --- | ---: | ---: |
| CF and CFN force | `(0.003463482, 0.003466349, 36.73711) N` | Same wrench as pressure plus gauges within 0.02735 N |
| CF and CFN origin moment | `(96.67450, -96.67256, -0.00000210) N·mm` | Same wrench as pressure plus gauges within 0.07735 N·mm |
| CFS force and moment | Exactly zero in all six reported components | 0.01 in force and moment units |
| Constrained gauge RF L1 | 0.00111342 N | 0.02367371 N |
| Ground RF wrench error | `7.27e-7 N`; `0.000715 N·mm` | 0.02735 N; 0.07735 N·mm |
| Upper-body balance residual | `4.02e-6 N`; `8.38e-7 N·mm` | 0.1 N; 0.1 N·mm |
| Whole-model balance residual | `7.27e-7 N`; `0.000715 N·mm` | 0.1 N; 0.1 N·mm |

The pressure is downward, the slave contact resultant is upward, and the ground vertical RF is upward. CF equals CFN exactly in the reported output; CFS is zero. All fixed frozen limits pass without adjustment. Ground displacements are zero. The gauge's constrained in-plane RF is small relative to its frozen limit; its free-z RF components are approximately `-2.93e-14 N` and `1.05e-14 N`, so they are not support reactions.

One immaterial verifier detail: `verify.py` places both x/y RF components from each gauge node into the gauge wrench, although node 45's x DOF is free. The raw node-45 free-x RF is `1.02e-15 N`, contributing about `5.6e-15 N·mm`; recomputing the wrench from constrained DOFs only gives the same result at every declared gate. This does not change this run's pass, and no frozen code or input was changed.

The output supports only software-level load transfer and resultant extraction for this hypothetical isotropic fixture. It does not establish local contact pressure or stress accuracy, metal/washer behavior, wood response, a material or product capacity, joint resistance, candidate acceptance, or any physical operation.
