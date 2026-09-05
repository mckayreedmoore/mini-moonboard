# 2×12 support-envelope study

**Decision study, not changed CAD or construction approval.** Keep the current
2×12 geometry provisionally. The existing downward cases do not justify a
larger footprint by themselves; the exploratory normal cases expose a load-basis
decision that cannot be settled by adding a modest amount to the legs.

This reuses the [frozen hybrid stability input](../fea/results/hybrid/2x12/stability.json)
and the existing two-toe equilibrium equations. Mass stays 216.3 kg and centroid
Y stays 734.3 mm. Extensions are **massless, rigid support-envelope changes**,
not redesigned legs. Actual longer legs or runners change mass, centroid, joint
forces, floor bearing and collision/tool clearances and must be modelled anew.
The published bulk FEA is not rerun or relabelled as a contact simulation.

## Compared envelopes

Positive Y faces the climber. “Leg-side” means the positive-Y floor toe;
“kicker-side” means the negative-Y toe. These precise names avoid confusing
front/rear with the board's backing face. Extensions move extreme floor toes,
not leg attachment points or foot centres. No member is proposed across the
climbing/fall space, and no pad or anchor is included.

All 12 main-panel rows are checked for each of the same six load vectors.
Columns have identical Y/Z in this 2D model. Row 12 governs the finite minima
below; ties with no destabilizing moment are recorded as row 1.

| Envelope | Support span mm (in) | Down + outward 300 N factor | Out/down normal factor | In/up normal factor |
| --- | ---: | ---: | ---: | ---: |
| Current | 1635.7 (64.4) | 2.17 | 0.76, uplift | 0.66, uplift |
| Leg-side +150 mm | 1785.7 (70.3) | 3.68 | 1.00 rounded, **still uplift** | 0.66, uplift |
| Leg-side +300 mm | 1935.7 (76.2) | 7.06 | 1.26, below 1.5 | 0.66, uplift |
| Both sides +300 mm each | 2235.7 (88.0) | 7.06 | 1.26, below 1.5 | 0.81, uplift |
| Both sides +600 mm each | 2835.7 (111.6) | No overturning demand | 1.93 | 0.93, uplift |

Every option exceeds the 1.5 moment-screen target for all four existing
downward cases. This is not a sliding, lateral, utilization or standards pass.
The normal vectors remain exploratory—not established governing climbing loads.
See the [load-basis audit](hybrid-load-basis.md) before selecting a design envelope.

## Exact theoretical thresholds

Let W be dead weight, c its Y centroid, (y,z) the force application position,
(Fy,Fz) its force, and k the target moment factor. With D=W−kFz > 0:

`T = (Wc − k*y*Fz + k*z*Fy) / (W − k*Fz)`

Both toe inequalities require `a ≤ T ≤ b`, in addition to `a < c < b`.
The script checks all 12 row positions. Its threshold helper explicitly rejects
D≤0 rather than applying a division formula outside its valid domain.

| Exploratory case | Extension to just avoid uplift, k=1 | Extension for k=1.5 |
| --- | ---: | ---: |
| Outward/downward normal | Leg-side 152.3 mm (6.0 in) | Leg-side 416.5 mm (16.4 in) |
| Inward/upward normal | Kicker-side 778.9 mm (30.7 in) | Kicker-side 2704.1 mm (106.5 in) |

Covering both k=1.5 extremes would require a theoretical 4756.3 mm (187.3 in)
support span with this frozen mass/centroid. **This is not a recommended frame.**
It shows why the normal-load basis needs resolution before resizing the CAD.
Thresholds are rounded for display; fabrication dimensions must not be taken
from them. Exact k=1 means incipient lift, not a usable safety margin.

Extending the opposite support does not improve the governing toe's moment
ratio. It can reduce the magnitude of a negative reaction without eliminating
the need for an impossible floor tensile reaction.

## Sliding and remaining scope

Once both supports are compressive, extending toes alone does not change
aggregate friction demand `|Fy|/(W−Fz)`. It is 0.0903 for the ±300 N/downward
cases, 0.3178 for out/down normal, and 0.6810 for in/up normal. These are demands,
not measured floor coefficients or approved values, and have no sliding factor.
The script reports no friction result if any checked row uplifts.

Next analysis should include the load audit's separately labelled mass and
hold-stand-off sensitivities, kicker positions and lateral/off-centre loading.
Those are **not included here**. Neither are flexible joints, floor irregularity,
pad interference, buckling, individual foot contact, or transient movement.
The [joint plan](hybrid-joint-next-steps.md) identifies the next connection work.

## Reproduction and decision gate

`uv run python -m fea.hybrid_footprint` regenerates the
[machine-readable sweep and thresholds](../fea/results/hybrid/footprint_sensitivity.json).
The source input hash is recorded. Run
`uv run pytest tests/test_hybrid_footprint.py tests/test_stability.py` for the
analytic equilibrium, threshold, extension, friction and reproducibility checks.

Before replacing the current CAD footprint: establish intended utilization and
dynamic/lateral load envelope, determine mass and floor-interface bounds, then
select a physical leg/runner concept outside the climbing space. Recompute its
CAD mass/contact geometry, rerun clearance checks, and evaluate actual joints
and unilateral floor contact. The current drawings remain unchanged while those
choices are unresolved; no shape is being silently represented as validated.
