# Asymmetric single-hold timber diagnostics

Nine basis load cases were solved on the authenticated 40 mm
`timber-base-development` mesh. Their linear combinations cover 216 selected
single-hold scenarios. **These are not 216 independent solves, a safe-weight
rating, joint resistance checks or approval of the newer panel-insert geometry.**

## Cases and results

Each of A12, K12 and F6 receives separate +1000 N X, +1000 N Y and −1000 N Z
loads. Linear superposition then represents 150/200/250/300 lb climbers at 1×/2×
body weight, with no horizontal force or 300 N at eight 45-degree directions.
Each scenario places the entire prescribed force at one mapped face node.

| Assumed climber | Largest loaded-point displacement among selected cases |
| --- | ---: |
| 150 lb | 1.508 mm |
| 200 lb | 1.909 mm |
| 250 lb | 2.311 mm |
| 300 lb | 2.712 mm |

All four maxima occur at K12 with 2× body weight plus 300 N world +Y, toward
the climbing side. The 300 lb case applies 2668.93 N downward. These maxima
are at the loaded nodes only, not over every node in the frame. Point-load
local stresses are not qualified, and this is not a mesh-convergence study.

The mapped face-node distances are 8.120 mm at A12, 3.631 mm at K12 and
7.596 mm at F6. Applied moments and reaction audits use those actual mapped
coordinates. Unlike the separate floor screen, these nodal cases have no
100 mm hold standoff or equivalent applied couple.

## What the joint results mean

Every scenario includes aggregate left/right leg-to-board forces and moments
about the source-bound joint reference points. Both leg plies form each free
body. The inherited mesh bonds the legs to **rim and upper-panel edges**, so
these actions cannot be assigned directly to the four rim bolts. See the
[interface finding](timber-joint-demand.md).

The floor is fixed in XYZ, all touching timber ideally bonded, and wood modeled
isotropically at E=7000 MPa and Poisson ratio 0.3. Gravity, real connection slip,
contact separation, floor friction, material strength and buckling are absent.
The newer insert-hole geometry and planned wider-principal remedy are not this
mesh. No capacity approval transfers to either revision.

## Verification

The adapter preserves exact accepted node coordinates and connectivity, uses
one actual load node per deck, and audits exact material/support/load definitions,
all three output endpoints, complete floor reactions and loaded displacement.
All nine solved cases pass independent six-component equilibrium checks. Every
superposed case is checked again for force/moment balance.

At each loaded node, the three directional displacement responses form a
compliance matrix. The reported matrices satisfy reciprocal symmetry and have
positive eigenvalues. This is a useful consistency check for a linear elastic
calculation, not proof of the entire stiffness matrix or structural safety.

The [summary and compact archives](../fea/results/timber-asymmetric/summary.json)
bind input/output and source hashes. Archived INP/DAT/LOG/STA/launch metadata
support replay; large FRD display diagnostics remain local, with their hashes
explicitly recorded as omitted rather than claimed as archived.

```bash
uv run pytest -q tests/test_timber_asymmetric.py \
  tests/test_publish_timber_asymmetric.py tests/test_timber_asymmetric_evidence.py
# In a separate working copy with the generated/published destinations absent:
uv run python -m fea.timber_asymmetric prepare
# Repeat inside the documented mini-moonboard-fea:box-v1 container for each hold:
python3 -m fea.timber_asymmetric solve --hold A12
python3 -m fea.timber_asymmetric solve --hold K12
python3 -m fea.timber_asymmetric solve --hold F6
uv run python -m fea.publish_timber_asymmetric
```

The image used was
`sha256:37671083a88ded305c4fcd83960a767dad4c2acb480976cb75fab5df261e2646`,
with two OpenMP threads. Prepared inputs, solver attempts and publication refuse
overwrites. Use the compact publisher above rather than the adapter's optional
full diagnostic archive command when reproducing the checked-in package.

## Design implication

These results do not identify a need to enlarge the entire frame. The next work
remains targeted: resolve backing-bolt edge geometry and qualify the actual
panel, base and leg load paths. A joint-specific model must address the extra
panel-edge bond before isolated upper-bolt demands can be trusted.
