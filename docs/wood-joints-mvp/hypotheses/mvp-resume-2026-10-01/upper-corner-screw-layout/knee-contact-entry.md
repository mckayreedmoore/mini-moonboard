# Knee loaded-shaft contact entry: conditional completion

**Bounded K loaded-shaft method: COMPLETE, conditional.** The parent corrected
the numerical step for a loaded neutral direction, retained ten accepted old
state files byte for byte, and generated fourteen new closed states. The frozen
terminal suite reports `conditional_first_order_equilibrium_all24`: all four
continuous knee-side shafts in all six current force cases close their three
receiver wrenches independently from bore and outer-seat point tractions.

This completes the recorded finite loaded common-shaft method requirement.
It asserts no other joint capacity, complete elastic timber qualification,
actual hardware/wood acceptance, shared-group/body-pose result or physical
release. The isolated force-boundary scope remains unchanged and adds no blanket
new prerequisite. No further state is pending within this bounded K requirement.

## Exact numerical change and known answer

The parent-owned frozen [knee-contact-entry.py](knee-contact-entry.py) changes
only step selection when the neutral tangent direction is loaded. For each
inactive circular bore it finds the forward intersection of the existing
relative-motion ray with its existing radial clearance. For relative position
`r`, direction `v` and gap `g`, the exit distance is

```text
lambda = (−r·v + sqrt((r·v)² − (v·v)(r·r − g²))) / (v·v)
```

The candidate crosses that contact by the recorded numerical step margin;
the unchanged full-potential Armijo rule still decides acceptance. The contact
law, gap, K20 stiffness, beam stiffness, gauge, Newton closure checks and
tolerances remain unchanged. The crossing margin is a numerical step scale,
not a changed bore geometry or physical penetration criterion. No prestress,
geometric shortening, preload or friction term is added.

The parent's analytic circular-foundation coupon uses `g = 0.575 mm` and
`k = 13 N/mm`, with known loaded answer
`u = (g + |F|/k) F/|F|` and zero pose for zero force. That coupon stiffness is
an independent numerical known answer; the physical model remains K20.

| Coupon force, N | Maximum pose error, mm | Saved result |
| --- | ---: | --- |
| (2, −3) | 3.774758283725532e−15 | matched |
| (−0.2, 0.1) | 2.886579864025407e−15 | matched |
| (0, 0) | 0 | matched |

Only cached outputs, numerical source definitions and hashes were read for
this documentation. No coupon, mechanical evaluation, review, native solve,
frame run, CAD run or software test was executed to produce these leaves.

## Scope, complete census and physical recovery

The force authority remains `operators-attempt02`: assessment `1a82cd2a`,
model `b5f9b87b`, rows `cdf21878`, comparison `bea6cbc3`, response `06251964`.
The unchanged input contract is `f2876952…cad01f`. Each state uses its two signed
lateral planes and **one physical axial tie**, together with the actual full
six-component source wrench for each of three receivers. The planes are never
treated as independent bolts. Each outer normal contact transfers full T;
the middle receiver has zero normal load from this bolt.

The same continuous 6.35 mm Euler–Bernoulli shaft spans the 38.1 + 88.9 + 88.9 mm
grip in three 7.5 mm bores. There are eight elements per receiver, 25 beam nodes,
72 bore quadrature fields and both outer annular normal traction fields per
state. The middle receiver's four transverse rigid pose coordinates remain
the gauge. All three receiver forces and moments are recovered from reference
point tractions independently of the Newton gradient. The original 24 bearing
fields, 96 static endpoint fields and 96 geometric placements remain frozen.

| Physical shaft | a12-rear | a12-forward | a12-left | k12-right | k12-rear | a1-rear | Old reused / new |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `knee_outer_left_side_1` | closed, old | closed, old | closed, old | closed, new | closed, new | closed, new | 3 / 3 |
| `knee_outer_left_side_2` | closed, old | closed, old | closed, old | closed, new | closed, new | closed, new | 3 / 3 |
| `knee_outer_right_side_1` | closed, new | closed, new | closed, new | closed, old | closed, old | closed, new | 2 / 4 |
| `knee_outer_right_side_2` | closed, new | closed, new | closed, new | closed, old | closed, old | closed, new | 2 / 4 |
| **Total** | **4 closed** | **4 closed** | **4 closed** | **4 closed** | **4 closed** | **4 closed** | **10 / 14** |

Maximum independently recovered receiver residuals across all 24 are:

- Force: **8.178873613928772e−7 N**, record 20,
  `a12-left / knee_outer_right_side_2`, new contact-entry result.
- Moment: **4.6654471134388587e−5 Nmm**, record 6,
  `a12-rear / knee_outer_left_side_2`, unchanged accepted old result.

Both meet the frozen numerical closure tolerances of 1e−6 N force and
`L × 1e−6 = 0.0002159 Nmm` moment. The iteration limit remains 150.
The earlier fourteen `STOP_method_or_boundary_defect` records remain preserved
as numerical iteration-limit evidence; their new closed records supersede
their pending method disposition without rewriting those files or claiming a
physical failure.

## Same-state smooth-shaft sensitivity and four-shaft pressures

The peak accepted same-state/same-position smooth-beam envelope proxy remains
the original byte-identical record 2,
`a12-left / knee_outer_left_side_1`: **192.47938729087358 MPa** at element 9,
`x = 60.32499999999993 mm`. Its actual single tie is 95.46010885208088 N,
bending resultant 4762.395472545951 Nmm and same-position shear resultant
28.00667462274078 N. The exact declared 634.317671 and 310.264078 MPa
sensitivities give ratios **0.3034432053381555** and **0.620372775770947**.
The existing envelope formula combines T, both bending components and both
shear components at each position; no different-position peaks are combined.
It remains a smooth-section diagnostic, with no actual thread, root, head
fillet or hardware acceptance claim.

The following maxima include **all six closed states** for each shaft.
Record indices are zero-based entries in the frozen terminal `states` array;
they point to the existing physical result files and hashes below. Printed
values are rounded; raw records retain full precision.

| Physical shaft | Max bore pressure, MPa | Max bore / existing Fe index | Witness case / record |
| --- | ---: | ---: | --- |
| `knee_outer_left_side_1` | 16.332041804 | 0.532306156 | a12-left / 2 |
| `knee_outer_left_side_2` | 12.076612884 | 0.393610025 | a12-left / 8 |
| `knee_outer_right_side_1` | 16.013251112 | 0.521915891 | k12-right / 15 |
| `knee_outer_right_side_2` | 11.784073048 | 0.384075347 | k12-right / 21 |

All four bore maxima occur in their named outer spine at
`x = 37.56325831863119 mm`. The existing nominal minimum Fe reference is
30.6816699545976 MPa; these pressure/reference indices are diagnostic.

| Physical shaft | Max wood-seat peak, MPa | Peak / mean Fc reference index | Max full-annulus mean, MPa | Mean / Fc reference index | Peak and mean witness case / record |
| --- | ---: | ---: | ---: | ---: | --- |
| `knee_outer_left_side_1` | 2.285435849 | 0.530359112 | 0.769655034 | 0.178606440 | a12-forward / 1 |
| `knee_outer_left_side_2` | 4.324982443 | 1.003657071 | 1.504820853 | 0.349209300 | a12-left / 8 |
| `knee_outer_right_side_1` | 1.393247108 | 0.323317454 | 0.463245781 | 0.107500992 | k12-right / 15 |
| `knee_outer_right_side_2` | 4.464659167 | 1.036070505 | 1.558190685 | 0.361594323 | k12-right / 21 |

The seat peak is at the head end on the outer spine in each listed witness.
Both ends share the listed full-annulus mean `T/A` in that state. The existing
perpendicular compression **mean reference** is 4.309223308230226 MPa.
The side-2 peak/reference indices exceed 1 while their full-annulus mean
indices are 0.349209300 and 0.361594323. Those local concentrations are reported
explicitly; this mean reference supplies no adopted pointwise failure
criterion. Pressure indices provide no complete timber or joint resistance.
The static endpoint screen value `0.9228431822` is not inherited by these
compatible fields, and no other capacity is transferred.

The required reference outer-center opening of the peak VM witness remains
`−0.23879147621049318 mm`: a **rocking center position** of the tilted annuli,
with nonnegative compression-only point pressure and positive physical tie.
It is not negative physical tension and introduces no pose bound. The normal
position relation still includes only direct axial stretch and signed center
closures, with no geometric shortening.

## Frozen raw receipts and witness hashes

| Parent artifact | SHA256 |
| --- | --- |
| Frozen `knee-contact-entry.py` producer | `dd20bb23b96e7e7e5f913a573108e1274b13179a7420c5fae01e3653fcae6bd8` |
| [Contact-entry analytic coupon](rawlocal/knee-contact-entry/coupon-attempt01/coupon.json) | `3301215eaef7b83ec4ac1d940615f44e2004e112029f1d3c64b99a6f8a84f3b1` |
| [Coupon receipt](rawlocal/knee-contact-entry/coupon-attempt01/receipt.json) | `d2d4fc452e237e706a9e0eec5835e617000c157dda3d2608152c8d355a25b8bf` |
| [All-24 suite](rawlocal/knee-contact-entry/suite-attempt01/suite.json) | `b707952e5ad740ad2ebc0306bce17a37e4718e88c1164cba568d9a39a6e8b79a` |
| [Terminal receipt](rawlocal/knee-contact-entry/suite-attempt01/receipt.json) | `63224d7d4e25bd8705123f75dc60663f6b4fcb8ab998d149ed2507ec79ee5e43` |

| Record | Exact raw result for pressure, stress or residual witness | SHA256 |
| --- | --- | --- |
| 1 | [Left side 1 seat peak/mean](rawlocal/knee-compatible-suite/suite-attempt01/state-01.json) | `022db565a2f985a1af725e4c133eaa8a0aba2c9d59e0afd74174b096acd5e622` |
| 2 | [Left side 1 bore / all-24 VM peak](rawlocal/knee-compatible/witness-attempt01/witness.json) | `866817f4c62ab542b6c79e5912a01777c5322930aaf21a96ea4be7b9125ee246` |
| 6 | [All-24 moment residual](rawlocal/knee-compatible-suite/suite-attempt01/state-06.json) | `7266a8e4344eb6da574c3200326740b719e24c52bf3c5c29ab631cf3b3b74757` |
| 8 | [Left side 2 bore and seat peak/mean](rawlocal/knee-compatible-suite/suite-attempt01/state-08.json) | `9b4638774d58d3bff59762f7c8f7378eb3655ac879903fc60b6ff9ce1daddad0` |
| 15 | [Right side 1 bore and seat peak/mean](rawlocal/knee-compatible-suite/suite-attempt01/state-15.json) | `6365411433c37d1171170086bf705f9467afde4ca967b10789413447335d10a6` |
| 20 | [All-24 force residual, corrected state](rawlocal/knee-contact-entry/suite-attempt01/state-20.json) | `0bf6b66a76d9c446fdf90f3b0fbd1d2c0ab4e87f43552f9c88eb3b3a0821e666` |
| 21 | [Right side 2 bore and seat peak/mean](rawlocal/knee-compatible-suite/suite-attempt01/state-21.json) | `5bad36678cc952edea07532ddb685d8c4de1b218aa1538713c44381bbac93a61` |

All sixteen generated output hashes, twenty inherited source receipts, three
direct parent source hashes and all 24 result references matched cached bytes.
The ten reused entries retain their previous exact result path and hash. The
machine suite records every new/reused state path, hash and all three full
receiver wrench recoveries. Original producers `8bfd4aab…fb3413` and
`97984020…990304`, original source force contract and failed attempt remain
preserved. These documentation leaves return to the parent for publication;
no code, raw evidence, staging or commit was changed.
