# Permanent-load frame and timber comparison

Parent completed one gravity-only case at zero and nominal clearance in
`rawlocal/dead-load-check/parent-attempt06`. Both states meet the original
frame equilibrium, connector-law, no-slip floor and method-domain gates.
All **88 member/state balances** and **11,568 bore-free signed cut traces**
are recovered from their simultaneous new force vectors.

## Loads and reference basis

Use the original **224.9499553141194 kg** modeled frame and **25 kg** equipment
allowance at **1g**, with no climber, horizontal hold force or live couple.
The existing equipment multiplier **1.1111358300342407** is applied once to
original gravity `e[:,0]`, `W[:,0]` and `F[:,0]`. This is no additional dead-load
amplification. The original 250 lb × 2 / 300 N / 100 mm six-case source stays
unchanged. Clearance geometry, elastic operators, contacts and all hardware
laws remain unchanged.

Permanent timber references use **C_D = 0.9**, from the authenticated
[2024 NDS Chapter 2](https://web-media.awc.org/wp-content/uploads/2021/12/17210153/AWC_NDS2024_20231129_AWCWebsite_Chapter2.pdf),
Table 2.3.2. Only Fb, parallel Ft/Fc and Fv receive the factor. Beam/column
stability factors are recomputed; Emin, Euler references, perpendicular
compression, elastic stiffness, steel and hardware are unchanged. The
unchanged shear helper recovers original stresses at 180 psi before the
comparison receives 0.9. Existing candidate timber restraints and intact-prism
shear/torsion hypotheses are retained.

| Permanent-load comparison | Maximum ratio | Signed witness |
| --- | ---: | --- |
| Normal/stability with candidate timber restraint | **0.174220** | `base_rail_top`, nominal gap, station 1069.825 mm |
| Compatible face shear/torsion | **0.132797** | `base_header`, zero gap, station 1067.015 mm |
| Conservative component bound | **0.181737** | Same header cut |
| Coefficient-5 isotropic sensitivity | **0.211934** | Same header cut |

All applicable normal comparisons are inside the inherited stability domain;
none exceeds its declared reference. Bores, clipped terminal profiles and
unsampled stations remain outside the method. These indices qualify no
complete joint or product.

## Frame gates and numerical adapters

Zero/nominal maximum force residuals are 1.64e-12 / 3.54e-12 N; moment
residuals are 2.78e-9 / 2.66e-9 N mm. Finite-law errors are 4.04e-7 /
2.32e-7 N; held-floor motion is below 2.61e-14 mm, with zero released-floor
force. Maximum positive spring motion is 0.02081 / 0.04926 mm, within the
unchanged 10 mm domain. Zero-gap rank is 300. Nominal rank is 296 and uses
the existing bounded fixed-force seating certificate. No unique frame pose,
strict stability or full motion envelope is accepted from that certificate.

Source gravity columns differ only by their case-specific floating projection:
maximum differences are 1.71e-13 mm in e, 6.83e-13 scaled N in W and
4.55e-13 N in physical F. Original column zero is retained without averaging.
Explicit absolute checks are 1e-8 mm / 1e-12 scaled N / 1e-9 N, respectively;
solver force, law, floor and domain tolerances are unchanged. Both adjacent
signed components sharing each physical plane ID are mapped together; 88
planes produce 176 target components. The inherited floor and analytic disk
coupons complete before the two frame states.

Earlier outputs remain preserved: attempt01 stopped on missing OSQP;
attempt02 on an inappropriate byte-equality assertion for gravity projection;
attempt03 on duplicate plane-ID mapping; attempt04 on a list conversion in
member recovery; attempt05 completed frame/member arithmetic but stopped on
NumPy boolean JSON formatting. Attempt06 corrects those implementation issues
and completes the comparison. None is a physical frame failure or changed
mechanics method. Original input files and all partial outputs are retained.

## Frozen engineering receipt

| Source or output | SHA-256 |
| --- | --- |
| Original six-case comparison | `bea6cbc330af3cdb20499d774a8f6bb24481d687c3150adb01ede18e4c1d50ca` |
| Original six-case response | `0625196497b0dbc7b297724d7b9947f7c7c61bb282cd4d9681705629302c76c7` |
| Executed producer | `ffdb2ee797000c055cd67c6e46ac80e549b4865a79346e728074625767bf213d` |
| Permanent `comparison.json` | `20802196776a89ea8b041832b413ef8d8613493b1bf36f89a3810807c5166e75` |
| Permanent `response.npz` | `9ff6f4ca177029b2c03acfb5425be9f943ad34679c8ab59013eb36764dd92f14` |
| Permanent `same-cut-states.csv` | `29c1c2ac520aa82960c045f79e858967388d4fee7d3098d6970ecefdc1de8bf3` |

The comparison binds all direct/transitive source hashes, 44 unchanged finished
STEP identities and output files. The earlier bottom-helper snapshot is
retained; its current helper differs only in recorded geometry-change metadata.
Source point actions, physical load columns, operator wrenches, opposing cuts
and all member balances are checked. No CAD import or native solve runs.

Runtime: Python 3.12, NumPy **2.2.6**, SciPy **1.15.3**, OSQP **1.0.4**.
API: `run(output: Path) -> dict`. CLI reproduction, using a fresh child:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 uv run --no-project \
  --with numpy==2.2.6 --with scipy==1.15.3 --with osqp==1.0.4 python -B \
  docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/dead-load-check.py \
  --run --output <fresh-child-of-rawlocal/dead-load-check>
```

Together with the [rated-case duration comparison](member-duration.md), this
completes the finite rated/permanent timber comparison under the parent's
stated cumulative-peak hypothesis. It provides no Hillman resistance,
full-joint qualification or physical release. Formal authority and all eight
physical flags remain unchanged. No software tests or agent review loop ran.
