# Curved-leg section preflight

**Geometry and external-load references only. Native section recovery remains
unqualified. No solver was run and no stress was reconstructed.**

The straight C3D10 coupon deliberately excludes curved midside geometry. The
saved actual-leg response has displacement, fixture reactions and energy, but
does not request native section output or stresses. Therefore it cannot supply
the missing section observations simply by reparsing its results.

[`leg_section_preflight.py`](../fea/leg_section_preflight.py) reuses the
[retained independent-leg archive](../fea/results/independent_leg_response/evidence.tar.gz),
checks its SHA256 and reconstructs each archived response deck byte-for-byte.
It selects whole inner-ply elements whose four corner nodes have mean world
Z below 1400 mm. This produces a **jagged conforming cut**, not a planar cut.

| Archived mesh | Lower-subbody elements | Opposed internal cut faces | Maximum cut-edge midside deviation, mm |
| --- | ---: | ---: | ---: |
| 40 mm | 1,496 | 22 | 0.3527202125 |
| 25 mm | 3,665 | 26 | 0.1984618685 |

The preflight checks shared six-node faces and midside ownership, connected
lower/upper selections and cut, opposed winding, and closed oriented edge
topology on the full subbody boundary. Every loaded floor node is included;
no fixed bore node is included. These are topology/corner-orientation checks,
**not curved-face area, Jacobian, surface-normal or integration qualification**.

## Independent reference resultants

Actual archived CLOAD fields are parsed separately, with per-step `OP=NEW`,
finite force values, valid DOFs, duplicate rejection and the solver's 20-character
value-field limit. Parsed vectors must match the reconstructed load context.
The reference point is fixed world **(1266.825, 900, 1400) mm**. All six-vectors
are ordered **Fx, Fy, Fz, Mx, My, Mz**, in N and N·mm, in global axes.

For the inner-only 1 N cases, expected force/moment **exerted by the upper
portion on the lower portion** is the negative external floor resultant:

| Applied floor direction | Expected Fx, Fy, Fz | Expected Mx, My, Mz |
| --- | --- | --- |
| +X | −1, 0, 0 | 0, 1400, 503.998387952 |
| +Y | 0, −1, 0 | −1400, 0, 0 |
| +Z | 0, 0, −1 | −503.998387952, 0, 0 |

Symmetric sharing gives half these vectors on the selected inner ply;
outer-only loading gives zero. All nine original cases are retained. This
fixture has no gravity/contact or load on the selected subbody besides the
floor loads. The upper section and floor moments use the same fixed reference;
do not compare native centroid moments without the appropriate translation.

## Replay and next qualification

```sh
uv run pytest -q tests/test_leg_section_preflight.py
uv run python -m fea.leg_section_preflight
```

The command emits complete selected element IDs, opposed face pairs, source
identities and reference vectors as JSON, always with `qualified: false`.
Tests include deliberately wrong midside ownership, misplaced fixture/floor
nodes, an insufficiently curved cut, disconnected topology and damaged load
tokens. The original archive and all previous numerical failures are unchanged.

Next verify curved-face geometry/integration and declare local force/moment
and refinement criteria before requesting native section output in a separate,
bounded **contact-free** diagnostic using these same loads and meshes. Compare
both opposed section resultants with the independent subbody references and
retain the original external equilibrium/energy checks. An eventual pass would
qualify only the tested homogeneous section-recovery path—not fastener forces,
ply sharing, contact interfaces, timber resistance or the full board.
