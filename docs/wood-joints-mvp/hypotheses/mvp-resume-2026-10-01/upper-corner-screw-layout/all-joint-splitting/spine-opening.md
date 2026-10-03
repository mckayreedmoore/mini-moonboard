# Reviewed knee-spine opening test

## Question and finite criterion

Can supported spreading of the recorded bore, washer and face forces remove
all perpendicular opening in the two reviewed 104-axis knee spines?

The answer is tested at one plane clear of the complete radial support of
every bore. The local-v gap is **9.7219133485 to 31.14735578436 mm**, and the
test plane is its midpoint. The post bores and first side bore are wholly
below it; the second side bore is wholly above it. Bore-wall pressure on a
full local-u cylinder cannot extend outside its center-v plus/minus radius.

For the isolated high-v timber part, the only nonzero recorded external
normal-v force is therefore the second side bore's complete signed
resultant. The existing washer pressures and timber-face contacts act in
local u or grain, while physical timber and hardware gravity acts along
grain. Spreading those fields on their supported surfaces cannot change
this scalar balance. Free couples are retained; they cannot change force.

**Necessary condition for a zero-perpendicular-tension route:** the signed
required normal resultant at this cut must be at most 0 N, subject to the
1e-6 N arithmetic tolerance. A positive result establishes an opening
requirement under the frozen forces, not a physical failure load or an
invented capacity ratio. One failure is sufficient to reject that route for
the present force allocation; a pass at this one cut does not qualify a joint.

An unsplit host and its lateral bolt actions might provide a different load
allocation. This test does not solve that bypass or claim that it is absent.
The 108-axis proposal changes the load path and remains separate/unadopted.

## Producer and known answer

[spine-opening.py](spine-opening.py) authenticates the published all-joint
receipt/source closure, reviewed four-u-bore spine geometry and the completed
physical-gravity helper. It evaluates both spines in all six original cases.
The original mechanical point/free-couple six-component cut wrench is saved
separately; only its normal force is certified independent of supported
spreading. No replacement full physical stress field is claimed.

The new arithmetic coupon checks an exact 100 N opening pair, the same pair
spread inside two disjoint supports, the reverse compression sign, refusal
of a cut intersecting a support, and a hand-calculated full wrench containing
nonzero free couples. Previously established geometry/volume integration is
reused rather than introduced as a new method.

API: `build(output)`. Parent owns execution. Output must be a fresh child of
this folder's ignored `rawlocal/spine-opening/`.

```sh
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  .venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/all-joint-splitting/spine-opening.py \
  --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/all-joint-splitting/rawlocal/spine-opening/attempt01
```

The output always preserves `splitting_resistance_established=false` and
`complete_joint_acceptance=false`: the recorded material set supplies no
applicable perpendicular tensile resistance for comparison. This test does
not modify geometry, select the proposal, execute a frame/native/CAD solve,
or authorize physical work.

## Parent calculation

The first run completed arithmetic but stopped while serializing an external
source path into its receipt. Its raw child is preserved without an accepted
receipt. The correction changes only path serialization and repeats source
authentication before final writes. Parent reran the corrected producer into
fresh `rawlocal/spine-opening/attempt02/`.

The known-answer checks pass. **All twelve spine/case states fail the necessary
condition for zero perpendicular tension under the recorded force allocation.**
This rejects that allocation's zero-tension route; it does not compare an
opening demand to a known timber fracture capacity.

| Case | Left required tension (N) | Right required tension (N) |
| --- | ---: | ---: |
| `a12-rear` | 313.475321 | 5.012134 |
| `a12-forward` | 328.537747 | 4.563403 |
| `a12-left` | 361.460505 | 4.344728 |
| `k12-right` | 4.266832 | 353.465997 |
| `k12-rear` | 5.086143 | 305.283445 |
| `a1-rear` | 37.466760 | 3.755040 |

These resultants are lower bounds without the additional opening contribution
from normal bending. They are not replacement forces for individual bolts.
The complete original point cut wrench, with both shears, torque and bending
moments, is retained in each output state.

| Artifact | SHA-256 |
| --- | --- |
| Corrected producer / snapshot | `03310b9b2ea83df62ed403172d1fdd57b6903028bd45a1b67e598ea79ae101a6` |
| `attempt02/checks.json` | `d6065cdcb6ac2d2348b07c920143c793b774afe2c93982525bd137e88f9eb292` |
| `attempt02/receipt.json` | `8ce3300059a90ddf8b884cea555a2561c65b0a6264933b457c2fbd83c82915c7` |

The receipt binds 500 sources and two outputs. Post-run verification found an
unrelated inherited washer receipt overwritten after execution. Parent
preserved the erroneous bytes and restored the original receipt byte-for-byte,
matching its frozen hash. Independent final verification confirmed all 500
source pins and both output hashes, with no mismatch. No washer solve, new
resistance, or changed force was used to obtain the scalar opening result.
