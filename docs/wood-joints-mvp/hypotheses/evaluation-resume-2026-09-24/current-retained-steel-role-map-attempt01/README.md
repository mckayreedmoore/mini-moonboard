# Retained steel elastic role map, attempt 01

## Result and scope

This source-only map binds all 60 retained frame-bolt component-role rows on
the 12 retained axes in full-frame manifest attempt04 to the existing generic
isotropic steel elastic scenario family. Each axis has the five modeled roles
`head`, `head_washer`, `nut`, `nut_washer`, and `shaft`. For each modeled bolt,
the source `head` and `shaft` rows share one physical-bolt identity key, while
all five component rows and their source masses remain distinct. Washers and
nut are not folded into that bolt identity.

The map carries the conditional reference values `E = 200,000 MPa`,
`ν = 0.30`, and derived `G = 76,923.0769 MPa`, plus the existing eight-case
`E = 180,000/200,000/220,000 MPa` by `ν = 0.25/0.30/0.35` sensitivity grid.
These are generic elastic input options only. Applying one uniformly to the
60 retained roles would require those stacks to be included in a future model
and their current-candidate recheck to be resolved. The map does not include
them by default, select a model run, or change full-frame manifest readiness.

The join is exact at the source-record level: each retained axis ID and its
two recorded member references match exactly five topology entities with the
same axis/role identity; all 60 entity IDs are unique. Recorded axis directions
are unit vectors. Each source mass center is on its recorded axis within the
producer's `1e-8 mm` perpendicular-offset check. This is a geometry-identity
consistency test, not a fit or delivered-part measurement. The source does not
establish physical head-to-nut order, received hardware identity, delivered
dimensions, alloy/grade, yield, fit, engagement, or resistance.

The material sensitivity family passes an isotropic fourth-order stiffness
tensor invariance check under a proper nontrivial rotation for all nine
scenarios (maximum component error normalized to `E` is `3.93e-16`). This
checks the orientation independence of the generic isotropic E/nu options; it
does not assign an orientation or solver material.

No solver body, element, DOF, material card, mass allocation, CAD change,
native solve, connection acceptance, or release is produced. The retained
roles stay separately inventoried and unassigned by default in the current
full-frame input manifest.

## Reproduction

From the repository root:

```sh
python3 -B docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-retained-steel-role-map-attempt01/produce.py --self-test
python3 -B docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-retained-steel-role-map-attempt01/produce.py --verify
```

`--self-test` checks the 12-axis/60-role positive join, isotropic rotation
invariance, and fail-closed controls for a missing role, duplicate axis,
receiver mismatch, and zero axis direction. `--verify` checks every pinned
input and reconstructs the complete JSON and canonical record digest.
`--write` is for a fresh attempt only and creates the JSON exclusively; it
refuses to overwrite existing output. The producer does not run native code or
modify the frozen inputs.

## Source pins

| Source | SHA-256 |
| --- | --- |
| Retained role source-to-topology map, attempt03 | `308a329a0b40db454d5b0e27c9ec2eca92d66eec96bfb222df5f7b7185bef4d4` |
| Topology producer | `16645507e1910e038e83b5acc0026b9fb12940db0f194732b355b4ef76a982f9` |
| Current full-frame manifest, attempt04 | `9e682e28c3d4c3c0594863f82c6b74d19dee2700f3856d34e1a26f69082e4f11` |
| Attempt04 manifest README | `7e60cb16f2100fe9da50ccc2617eaeb3a5fba35dd5461d4cce49319bbd15bf9f` |
| Attempt04 manifest producer | `966e4b5918fefe06741ca828a3b4c3f6d353b735a1fc70df6a98a91b4e98b1f4` |
| Full-frame manifest source producer | `0774aa06a560a72411d6fd80da00bd82e81320c7b9191dc36c75641f9f8c9df6` |
| Current material-map status note | `0ad2c85c9fdc6f3cd17a46c57639b4e63c6fd0119d565b45121715f1c1831e6f` |
| Current material scenarios | `dd76354c0fa68a01a336cef22fe1cf854baaaf1ceda22dd11ceb881a274bb3c4` |
| Generic steel scenario definition | `e97f7df51e6553698e1542079d722022cdbbedad83f740ee42d85b56e6b394c3` |
| Steel scenario helper | `0cf45f5194231f61500df14ed580adb9742f6b0c7df659382ea658c7598e8d02` |
| Referenced CalculiX 2.21 manual | `16b6bab5a3f1a40a21fff62379f95c804a58d93758ab2e9a489b18d911dc20c8` |
| Reviewed candidate steel map JSON | `13ed1afcfbc9343207b9e8eb498f8fb3762ec2cdbe0719963f26037cc77027cc` |
| Candidate map README | `a4ca6688d6bece7c4653c421ed52f74f681de10985896d5d4454f89314662222` |
| Candidate map producer | `b625579bc032e32a1100c39f31e50cfea65f74b2137394d500e8055436ca1b26` |

The older scenario helper's 32-body WJ04 identity is not inherited. The current
material-scenarios policy permits reusing its generic E/nu numbers as proposal
values; this map separately records the retained-role option and leaves it
excluded by default. A source change requires a new numbered attempt rather
than regeneration of these bytes.
