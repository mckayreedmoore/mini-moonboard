# Released-gusset connector sensitivity

This is a numerical development trial for the current wide frame, not a bolt
load rating, joint-capacity result or construction approval. It changes no CAD,
hardware selection or machining schedule.

## Question and model

Can the archived gusset mesh exchange force through the eight actual bolt-axis
locations, with its previously bonded interfaces released, while preserving
force/moment balance and rigid-body freedom?

Both gussets use their original solid elements. Four connector points per side
are interpolated on the proper rim or post interface at the actual bolt axes.
Quadratic triangular shape functions reproduce affine displacement and the
force resultant/first moment. Nearest face nodes are 1.356–7.543 mm away from the
bolt axes; snapping to those nodes is avoided. Negative corner interpolation
weights are normal for this quadratic interpolation, not negative contact areas.
No washer pressure patch, bore bearing or local hole stress is resolved.

Three independent translational springs connect each point to a support motion
sampled from the archived parent frame. The gusset has no other fixed nodes,
header tie, applied gravity or contact constraint. Spring stiffnesses of 100,
1,000 and 10,000 N/mm in all three axes are **chosen numerical parameters**,
not sourced properties, calibrated bounds or equivalent axial/lateral bolt
stiffnesses. Each run includes nine inherited 1,000 N Cartesian parent-load
bases and six rigid translation/infinitesimal rotation controls.

The implementation uses native CalculiX [linear equations](https://www.feacluster.com/CalculiX/ccx_2.18/doc/ccx/node269.html)
and [SPRING2 elements](https://www.feacluster.com/CalculiX/ccx_2.18/doc/ccx/node68.html).
The documented equation's first variable is the dependent virtual-point DOF;
the six solid-face DOFs remain independent. Spring data follow the native
[*SPRING definition](https://www.feacluster.com/CalculiX/ccx_2.18/doc/ccx/node329.html).
The actual executable is the pinned CalculiX 2.21 image recorded in the archive;
documentation pages above describe the 2.18 interface.

## Rejected attempt and verified formulation

The first formulation prescribed support motion directly on spring anchors
adjacent to dependent virtual DOFs. It ran without solver errors but left the
gussets motionless, including under rigid translation controls. All 45 cases
failed the preset balance/control gates. The [rejected archive](../fea/results/gusset-connector-trial-rejected.tar.gz)
retains its original generator and complete nested run evidence. Its forces
must not be interpreted as bolt demands or physical failure.

The revised formulation holds the spring anchors at zero and applies the
equivalent distributed point load `k * u_parent`. For a point displacement
`u_point = sum(w_i * u_i)`, its energy is
`0.5*k*u_point² - k*u_parent*u_point`, differing from
`0.5*k*(u_point-u_parent)²` only by a constant. Thus it retains the same linear
stiffness and equilibrium equations while avoiding the direct prescribed-anchor
path that failed. This is an equivalent-load reformulation, not extra bracing
or an increase in assumed connection stiffness.

The reported physical connector force in this trial is
`RF_fixed_anchor + k*u_parent = k*(u_parent-u_point)`.
The fixed-anchor RF alone is **not** the total connector force. Node loads use
the existing length-safe CalculiX number formatter. The exact source of the
failed native prescribed-anchor behavior has not been established beyond this
reproduced formulation-specific contrast; no general solver-defect claim is made.

## Results and acceptance

All 45 revised cases passed the predeclared numerical gates:

- Exact step/node inventory and point-constraint agreement within 1e-7 mm.
- Independent spring-law force agreement within 0.01 N.
- Each gusset's net force within 0.01 N and world-origin moment within 1 N·mm.
- Each connector's rigid-motion control force within 0.001 N.

Maximum rigid-motion force was below 1.5e-10 N; maximum point-constraint error
was below 4.7e-9 mm. These controls do not establish mesh convergence, contact
behavior, actual material stiffness or strength.

| Assumed connector stiffness, each axis | Maximum connector resultant over nine frozen-motion bases |
| --- | ---: |
| 100 N/mm | 0.1623 N |
| 1,000 N/mm | 1.5810 N |
| 10,000 N/mm | 13.5673 N |

**Do not compare these small forces to bolt resistance and declare a pass.**
The one-way parent motions came from a fully bonded frame. They cannot change
when this gusset connection is released, and may suppress the relative motion
that a genuinely coupled frame develops. The stiffness sweep is neither an
upper nor lower bound on actual demand. It establishes an inspectable connector
method and shows that the assumed connection stiffness materially affects its
response.

## Next engineering action

Use the verified point-connector formulation in a coupled whole-frame trial:
duplicate gusset interface nodes, remove the artificial gusset bonds, and join
the intended rim/post points across the actual bolt locations. Allow the parent
members to redistribute deformation under the applied loads. Keep any remaining
bonded interfaces explicit; separately address admissible header bearing/contact,
connector calibration, mesh convergence, axial/washer action and material
failure modes before actual connection qualification. Do not resize lumber or
reduce hardware based on the one-way trial.

The [accepted numerical archive](../fea/results/gusset-connector-trial.tar.gz)
contains all decks, native outputs, field/point maps, gates and source hashes.
Three focused tests check quadratic/affine interpolation and wrench preservation,
reconstruct all decks, replay every native result, inject an equilibrium failure,
and verify that the first attempt remains rejected.

```sh
uv run pytest -q tests/test_gusset_connector_trial.py tests/test_gusset_recovery.py
```

Independent correctness, testing and architecture/package-consistency reviews
reported no substantial findings. The broader focused regression passed 39
tests, including prior gusset recovery, interface ownership, bolt-reference and
native-control checks. Ruff and `git diff --check` were clean. This is a
numerical/software review checkpoint, not professional structural approval.
