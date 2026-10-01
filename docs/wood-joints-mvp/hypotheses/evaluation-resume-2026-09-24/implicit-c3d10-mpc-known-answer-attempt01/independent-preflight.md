# Independent preflight: implicit C3D10 free-MPC known answer

Status: **PASS for the bounded analytical/deck preflight; no native result.**
This review is read-only apart from this report. It does not qualify a joint,
contact response, or structural criterion.

## Reviewed bytes

| Artifact | SHA-256 |
|---|---|
| `design.md` | `1e23150c7dfca4ab4039f6b53f88151be450415298209f29a99ac067e488e325` |
| `expected.json` | `2838d69cc41271fa8d7e4642752b59641fd7afccb534fabb6a3262eacfc26fff` |
| `input/direct.inp` | `a390ecb6648c01d52dd417d16816936c39eb381b84a0714d4daa3b12fbf9a35f` |
| `input/mapped.inp` | `8166c7368487bff69f1c31b8fe08f29aa16e12dbc8a74d77396a9802f572a67d` |
| `reference.py` | `590f0ded1fbb49a9ca543a81d6701b4ece9bcb5e74b3650e0feeb26c3ca331c9` |
| `acceptance.json` | `1784d17470797363ce1f11272dbda8859988f64994f22769ded89c961c70df83` |
| `verifier.py` | `0dc37241d58e21c618fea23cee1c74c429831bb3368811fe83350e302f88b705` |
| `run.py` (parent-owned, inspected) | `485a928ca067fc187eb00957e7b391f002a4f8c508694c4dc44bd99cdd0825c2` |
| `parent-oracle.json` (parent-owned) | `68bd867f10ed41474e09d86c9264aba5ca08bd103c4a75a85132a63331d3c438` |

The source archive SHA-256 is `9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7`; its reviewed `e_c3d.f`, `nonlingeo.c`, `tempload.f`, and `gauss.f` member hashes match the pins in the design. The local 2.23 manual PDF hash also matches: `a0bf3fc03f374912ff2bf28da3f7dfb6a61428dd7f41b281a2e7e1fdb318f330`.

## Geometry, loading, and oracle

Both decks contain the same straight-sided unit C3D10 tetrahedron, node ordering, `E=1`, `nu=0`, `rho=6`, and physical boundary conditions. The volume is `1/6 mm³`, so the total mass is `1 tonne`. Direct and mapped cases use exactly the same ten physical U1 loads, `-0.05 N` on corner nodes 1–4 and `+0.2 N` on midside nodes 5–10, scaled by the table `(0,0), (0.1,0.1)`. The source interpolation and step-time basis make the applied acceleration `a(t)=t mm/s²`; the initial load is zero.

For the mapped case, node 1 U1 is the dependent term in
`U1(1)+U1(2)+U1(3)+U1(4)-4*U1(11)=0`. Node 11 U1 remains free and nodes 2–10 U1 remain independent. This is an invertible coordinate substitution with determinant 4, not a tie of all physical nodes. The dependent-node load is retained, so the check exercises the transformed load as well as the free-coordinate mass action.

The shape-function integrals independently give row sums `-rho*V/20` at each corner and `+rho*V/5` at each edge node. I checked the pinned four-point C3D10 quadrature directly: because the shape functions sum to one and the rule integrates each quadratic shape function, its `M*1` row sums reproduce the stated vector to floating precision (maximum discrepancy in my calculation was `6.7e-16 tonne`). The reference recurrence was also recomputed independently for all 100 increments; U, V, and ELKE matched every `expected.json` state. `reference.py --check` passes. The first expected state is U1 `2.5e-10 mm`, V1 `5e-7 mm/s`; the terminal state is U1 `0.000166675 mm`, V1 `0.005 mm/s`, ELKE `1.25e-5 N·mm`.

The pinned source uses four-point tetrahedral integration for the C3D10 `rho*N_i*N_j` mass integrand. That underintegrates its degree-four entries: the ten-scalar-DOF mass matrix has rank at most four, so the exact-integral matrix in `parent-oracle.json` is an analytical coordinate-algebra reference, not the matrix assembled by 2.23. This does not invalidate the stated rigid-translation oracle, whose row sums and kinetic energy are exact under this rule; it does prohibit claims about arbitrary C3D10 mass modes or a full mass-matrix qualification.

I independently reconstructed the axial four-point matrices with the stated material: sampled M has rank 4, K has rank 9 with the uniform translation as its null mode, and `K+4M/dt²` has rank 10 at `dt=0.001 s`. Cholesky of the equivalent scaled effective operator `M+(dt²/4)K` succeeds. The source's initial-acceleration branch also forms `M+beta*(tinc/10)^2*(1+alpha)K`; here the stiffness coefficient is `2.5e-9 s²`, and the corresponding matrix is positive definite in the same reconstruction. Its startup right-hand side is zero because the table starts at zero, so the startup solution is zero. This is the solver's built-in initial-acceleration treatment, not a user-added support or stabilization; it is a bounded source check, not a native solver result.

## Output and execution boundary

The acceptance contract requires 100 accepted `.sta` increments, 100 DAT U/V and BODY energy states, ten physical nodes in each FRD DISP/VELO state, normal completion, and mapped node 11 U/V from DAT. This split is appropriate: controller 11 is not element-connected and is not expected in FRD. The verifier's `--self-test` passes its synthetic positive case and rejects both missing-state coverage and perturbed motion. The selected tolerances are explicit in `acceptance.json`.

The parent-owned runner is serialized and binds the two deck hashes, source archive/member hashes, manual PDF, parser, image, and binary; no run was launched here. `parent-review.json` and the parent-controlled freeze remain required before execution. A later native pass would answer only whether this 2.23 rigid-translation/free-coordinate row-sum and load-mapping fixture passes its frozen gates. It would not qualify other C3D10 modes, the current physical-pivot maps, contact, the wood joint, or a physical load history.
