# Tangential contact: matched six-tetrahedron cube

The small shear coupon reproduces the penalty moment-transfer discrepancy
without the full frame. Halving the maximum increment approximately halves
the penalty moment residual. With the same deformable ground supported only
at its bottom, MORTAR passes the external force/moment checks on this coupon.
**This is not a local contact validation or a frame acceptance.**

## Exact comparison

Reuse the frozen 100 mm cube formed by six C3D10 tetrahedra. Ground is the
existing 120 × 120 × 100 mm C3D8 brick. Both use E=7,000 MPa and ν=0.3;
no gravity is applied. Nine top nodes receive equal downward nodal loads
totaling 120 N (not a uniform-pressure traction). Top X/Y are held during
seating, then top X is prescribed to 1 mm, Y stays held, and Z stays free.
The actuator is an intentional coupon boundary, never a free-board support.

The normal/tangent slopes are 10,000/100 N/mm³ and μ=0.3, a numerical
assumption. Both formulations use the same history at maximum increments
0.25 and 0.125, with automatic cutbacks. The original fully fixed ground is
retained as one comparison. The second comparison fixes only its four bottom
nodes, allowing the master surface and ground brick to deform. This changes
ground compliance and is explicitly separate from the original model.

| Ground configuration | Formulation | Increment | Loaded moment about Y, Nmm |
| --- | --- | ---: | ---: |
| All eight ground nodes fixed | Penalty | 0.25 | 30.00031 |
| All eight ground nodes fixed | Penalty | 0.125 | 15.00031 |
| Bottom four ground nodes fixed | Penalty | 0.25 | 30.00037 |
| Bottom four ground nodes fixed | Penalty | 0.125 | 14.99923 |
| Bottom four ground nodes fixed | MORTAR | 0.25 | -0.00000010 |
| Bottom four ground nodes fixed | MORTAR | 0.125 | 0.00065590 |

For bottom-supported MORTAR, the maximum absolute loaded moment component is
0.001346 Nmm at 0.25 and 0.000819 Nmm at 0.125. All force residual components
are below 0.1 N and moments below the unchanged 1 Nmm gate at both full-step
endpoints. Realized mean foot X motion is approximately 0.99965 mm, so this
test involves actual sliding rather than just actuator motion with a stuck foot.

The fully fixed MORTAR runs report zero DAT ground RF and nonzero free slave
RF. Applying the penalty interpretation to those outputs leaves a missing
120 N reaction. Those runs are **output-semantics unresolved**, not evidence
that mortar loses force equilibrium. No free contact RF is counted as an
external support. Bottom-supported MORTAR makes noncontact bottom SPC forces
available and the external balance is interpretable there.

## Audit and limits

External forces are bottom/all-ground SPC reactions, actuator X/Y reactions,
and the known top Z nodal load counted exactly once. All moments use actual
`x+u`; all support displacements and prescribed actuator endpoints are checked.
Top free-Z RF must agree with its specified nodal load. Free master/slave RF
is diagnostic only. Wood Z displacement alone is **not** a contact gap when
the ground deforms; local contact geometry is not yet audited.

The [exact-version formulation research](contact-formulation-options.md)
explains why MORTAR nodal/weak-law output cannot use the penalty DAT pointwise
auditor. Local-law, inactive-region, mesh and broader load-history checks remain
open. The reduction with increment size supports, but does not prove, the
frozen contact-mapping hypothesis. Next test the actual inclined leg/foot
coupon with the same noncontact-ground support approach before considering
any full-frame formulation change. The
[actual inclined-leg follow-up](leg-shear-coupon.md) now passes global checks
for both MORTAR increments, while remaining bending-dominated and locally
unvalidated.

## Evidence and replay

[The report](../fea/results/contact_shear_coupon/report.json) includes every
endpoint, support configuration and archive hash. The
[raw archive](../fea/results/contact_shear_coupon/solver_evidence.tar.gz)
contains all eight decks, output files, contexts and exact launch generators.
Earlier exploratory runs remain separate in ignored generated directories.

```sh
docker run --rm --user "$(id -u):$(id -g)" -e OMP_NUM_THREADS=2 \
  -v "$PWD:/work" mini-moonboard-fea:box-v1 \
  python3 -m fea.contact_shear_coupon --max-seconds 60
# Repeat with --bottom-supported for the compliant-ground comparison.
uv run pytest -q tests/test_contact_shear_coupon.py
```
