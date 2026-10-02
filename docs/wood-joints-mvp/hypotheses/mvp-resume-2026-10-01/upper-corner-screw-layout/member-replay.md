# Member replay after four upper screw moves

This is a fresh saved-force calculation for `frame-250-attempt02`, retaining
the intended 250 lb upper limit, 2× vertical force, 300 N horizontal force,
100 mm front-face lever, gravity and separate 25 kg accessory allowance.
All six nominal-gap forces come from the relocated operator, not an older
frame. No new frame or native solve is performed.

## Results

| Check under its declared hypotheses | Preserved layout | Four moved screws |
| --- | ---: | ---: |
| Peak normal interaction with effective timber restraints | 0.614384 | 0.628421 |
| Intact-prism compatible face shear/torsion / 180 psi | 1.039209 | 1.021524 |
| Conservative same-cut shear component bound | 1.202715 | 1.189165 |
| Isotropic coefficient-5 sensitivity | 1.337436 | 1.318027 |

All applicable rectangular normal/stability checks stay below unity in the
same declared timber-restraint scenario. The new shear/torsion comparison
still exceeds the unchanged normal-duration allowance. Relocation reduces
this exception but does not resolve it or establish a physical failure.

The governing shear/torsion cut remains `base_rail_top`, K12-rear,
2116.3359375 mm from its start, after the station, on the negative-grain half.
Its simultaneous actions are:

| Action | Demand |
| --- | ---: |
| N, tension positive | −1294.978362 N |
| Vu / Vv | −334.739244 / +1040.454938 N |
| Torque T | −53849.850360 N mm |
| Mu / Mv | −144177.809785 / −13632.653071 N mm |

This is a declared compatible intact-prism stress field, with free warping
and no local concentration factor. The cut remains near the outer-cleat
transfer region; local disturbed stresses are not established by this beam
screen. Neither a larger allowable nor new member dimensions are adopted.

## Geometry and census

The replay covers 20 frame timbers, 24 blocks, all 264 member/case balances,
55,176 signed cuts and 34,704 applicable bore-free rectangular traces.
Source material/grain frames, four corrected top STEP overrides and existing
finished holes remain bound. All 160 previously matching saved sections and
131 changed-STEP exclusions retain their separate geometry scopes.

Four new receiver slices are conservatively excluded around the relocated
nominal shaft stations: two on the top rail and one on each side. The
4.1402 mm occupied shaft envelope is an analysis exclusion, not the owner's
1/8-inch pilot instruction. Old saved hole exclusions are also retained;
the saved STEP has not been recut or repaired. This screen assigns no local
resistance at either the old or new hole slices.

The nominal states retain rank 296/297 and finite fixed-force seating bounds.
They provide simultaneous forces, but no unique pose, seating-motion envelope
or strict assembled-frame tangent stability. The four long 2×6 members retain
their existing conditional weak-direction restraint duties. No complete
member, joint, formal criterion or physical release is accepted.

## Outputs and reproduction

The [elementary member table](member-checks.md) preserves all member envelopes.
Local raw outputs remain ignored:

| Artifact | SHA-256 |
| --- | --- |
| `../member-screen-attempt02/four-screw-layout01/member-results.json` | `54f3888581717d2579b0dd6ea7dcd754501ec2890a9f4869059f476f2d0965c5` |
| Same packet `action-section-arrays.npz` | `ddfa310266661ea5ba6e188d2bf473121d99158d50921c84760744519e2a7caf` |
| Same packet `geometry.json` | `c61139087fac34e8094f2336f15dd6de5c0112d26d37b9535526f47332f453af` |
| `../member-stability-attempt01/four-screw-layout01/checks.json` | `aceebc0beaee1cc178450b52b2a16a32924803c3210dc0c115c0fee7a3a7c574` |
| `frame-250-attempt02/comparison.json` | `bea6cbc330af3cdb20499d774a8f6bb24481d687c3150adb01ede18e4c1d50ca` |
| `frame-250-attempt02/response.npz` | `0625196497b0dbc7b297724d7b9947f7c7c61bb282cd4d9681705629302c76c7` |

Both maintained producers accept `--frame` for explicit physical operators.
The member producer's `--summary` keeps this child revision's table separate
from the preserved current working-model table. Use fresh output directories:

```sh
packet=docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 \
  .venv/bin/python "$packet/member_screen.py" \
  --frame "$packet/upper-corner-screw-layout/operators-attempt02" \
  --clearance "$packet/upper-corner-screw-layout/frame-250-attempt02" \
  --summary "$packet/upper-corner-screw-layout/member-checks.md" \
  --output "$packet/member-screen-attempt02/four-screw-layout02"
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 \
  .venv/bin/python "$packet/member_stability.py" \
  --frame "$packet/upper-corner-screw-layout/operators-attempt02" \
  --clearance "$packet/upper-corner-screw-layout/frame-250-attempt02" \
  --members "$packet/member-screen-attempt02/four-screw-layout02" \
  --output "$packet/member-stability-attempt01/four-screw-layout02"
```

Source hashes and executed producer snapshots are checked before and after
the arithmetic. Ruff passes. No software tests or review loop were run.
