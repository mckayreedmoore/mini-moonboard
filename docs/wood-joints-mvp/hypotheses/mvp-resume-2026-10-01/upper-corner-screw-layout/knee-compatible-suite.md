# Finite first-order knee suite adapter

**Bounded K loaded-shaft method COMPLETE, conditional: all 24 states now close
after the parent's numerical contact-entry correction.** This original frozen
suite's exit 2, ten closures and fourteen method stops remain historical
evidence. The final completion annotation below gives the corrected result.
The preparation and mechanical sources remain frozen. This extends the
accepted local first-order method to the existing K requirement: four continuous
knee-side shafts and six current force cases, with all three receiver fields,
two signed lateral planes and one physical axial tie per shaft. The accepted
`a12-left / knee_outer_left_side_1` witness is reused exactly. There are **23 new
states**, with no repeated selected solve, geometry placement, stiffness branch,
preload, friction or frame run.

## Frozen evidence and coverage

| Existing input/result | SHA256 |
| --- | --- |
| Original `knee-compatible.py` producer | `8bfd4aab145e468f477a04a23073feebab9d9c3a0b4bb4cc1bc2407399fb3413` |
| Original `prepare-attempt02/input-contract.json` | `f2876952e6b71d59acdbf20dacaef233444402e50bfcc6d3b9ec1967f2cad01f` |
| Matched parent coupon | `c76aacdd80d42adc6ae7a080ea3ae3ab4b614cb1dcce2709a429e764a11fa1cd` |
| Coupon execution receipt | `515f38a54c30b961f8c9edbd9de0f49f73b8e52f6bd5f4eee71de01778240482` |
| Accepted selected witness | `866817f4c62ab542b6c79e5912a01777c5322930aaf21a96ea4be7b9125ee246` |
| Selected witness execution receipt | `7088673c7e3b1afa78e2a53438bff9e9f475444f1014a7fc018329156df2eb27` |

The force authority remains assessment `1a82cd2a`, model `b5f9b87b`, rows
`cdf21878`, operators `c9483639`, comparison `bea6cbc3` and response `06251964`.
All 13 directly consumed upstream sources in the original contract are checked.
The parent's separate 50 mm frame work does not replace these inputs.

| Shaft | Six cases | Existing result reused | New API evaluations |
| --- | --- | --- | ---: |
| `knee_outer_left_side_1` | a12-rear, a12-forward, a12-left, k12-right, k12-rear, a1-rear | a12-left | 5 |
| `knee_outer_left_side_2` | Same six | — | 6 |
| `knee_outer_right_side_1` | Same six | — | 6 |
| `knee_outer_right_side_2` | Same six | — | 6 |
| **Total** | **24 states** | **1** | **23** |

The prepared plan retains the exact original boundary index, five source row
indices, one signed tie tension, receiver order and frozen bearing/endpoint/
placement pointers for each state. It preserves the 24 bearing fields, 96
static endpoint fields and 96 placement witnesses. It performs no placement
search or source mechanics replay.

## Unchanged mechanical API

[knee-compatible-suite.py](knee-compatible-suite.py) imports the frozen original
producer only in explicit parent `run` mode. Each new state is passed with its
actual full receiver wrenches and exact three-receiver geometry to
`run_witness(contract, state, geometry)`. The original source, assembly, contact
functions and independent point-traction recovery are unchanged. The original
API's return labels are hardcoded to its selected state; the adapter corrects
only those output metadata labels from the actual supplied state and records
the backend labels for provenance. No mechanical global is changed.

The shared constants and definitions remain:

| Quantity | Frozen value/scope |
| --- | --- |
| Bore and wood-seat stiffness | K20 = 20 MPa/mm |
| Smooth shaft | 6.35 mm diameter; E = 200000 MPa |
| Head/nut contact stiffness | 10000 MPa/mm |
| Receiver grip | 38.1 + 88.9 + 88.9 = 215.9 mm |
| Bore | 7.5 mm diameter; 0.575 mm radial clearance |
| Elements and variables | 8 elements per receiver; 25 shaft nodes; 108 variables after gauge |
| Gauge | Middle receiver's two transverse translations and two tilts fixed at common datum |
| Physical axial transfer | One prescribed tie; both outer normal stacks carry full T; middle normal bolt load zero |
| End contacts | Frozen rigid washer and concentric 5 mm head/nut flat-circle hypothesis |
| Geometric/prestress terms | No T-dependent geometric stiffness, geometric shortening or preload stiffness |
| Numerical closure | 1e−6 N mixed gradient and recovered force; L×1e−6 Nmm recovered moment; 150 Newton iterations maximum |

For every returned state, the result retains all three independently recovered
six-component receiver wrenches and their source targets, 72 bore quadrature
fields, both outer annular normal traction fields, beam fields and normal
transfer. Two lateral planes are never solved independently as separate bolts.
All source receiver drives remain the negatives of the current full per-bolt
operator wrenches. Face contacts, neighboring bolts and whole-body loads are
not added to this isolated boundary.

## Same-state smooth-beam and pressure diagnostics

For each reported beam position, both curvature and third-derivative components
from that state are retained. With `M = |EI curvature|`,
`V = |EI third derivative|`, `A = πd²/4` and `I = πd⁴/64`, the adapter uses the
existing corner envelope proxy:

```text
sigma = |T/A| + M d/(2 I)
tau = 4 V/(3 A)
VM_proxy = sqrt(sigma² + 3 tau²)
```

T is the one actual saved axial tie for that source state. M and V come from
the same reported element position; peak M and peak V at different positions
are not combined. The two bending and two shear components enter by vector
norm. As in the existing corner proxy, cross-section normal and shear envelopes
are combined; this is not an exact fiber-level VM stress field or a thread,
runout, head-fillet or delivered-hardware result.

The exact declared sensitivities are **634.317671 MPa (92 ksi)** and
**310.264078 MPa (45 ksi)**. Each field reports both ratios, and each state's
summary identifies its peak proxy and whether a declared sensitivity was
exceeded. These values are explicitly supplied sensitivity inputs; model
material-null metadata does not create an additional criterion. The suite's
equilibrium status reports physical closure, while the parent inspects the
stress diagnostics separately.

Bore peak pressures for each of the three receivers are compared with the
existing nominal minimum Fe reference, **30.6816699545976 MPa**. Each outer wood
seat reports its peak and full-annulus mean pressure, peak/mean concentration
and both pressure comparisons with the frozen perpendicular compression mean
reference, **4.309223308230226 MPa**. These are nominal/mean-reference diagnostics;
they are not pointwise joint resistances or wood acceptance ratios. There is
no transfer of the static endpoint screen's `0.9228431822` reference to these
compatible fields, and no new capacity is calculated.

## Accepted selected witness and rocking-center position

The parent reported selected exit 0 and accepted its local physical closure.
Cached arithmetic is:

| Quantity | Accepted cached result |
| --- | ---: |
| Newton history entries | 20 |
| Maximum independent receiver force residual | 1.3066188131460876e−9 N |
| Maximum independent receiver moment residual | 1.7136562746600248e−7 Nmm |
| Single physical tie | +95.46010885208088 N |
| Required reference outer-center opening | −0.23879147621049318 mm |
| Same-position smooth VM proxy peak | 192.47938729087358 MPa |
| Peak position | x = 60.32499999999993 mm, element 9 |
| Bending / shear at that position | 4762.395472545951 Nmm / approximately 28.0067 N |
| VM / declared 92 ksi sensitivity | 0.3034432053381555 |
| VM / declared 45 ksi sensitivity | 0.620372775770947 |
| Maximum bore pressure | 16.332041803547604 MPa |
| Maximum head-end / nut-end wood-seat pressure | 1.345698416156855 / 1.2829452251917846 MPa |

The negative reference opening describes the **rocking center position** of
tilted annuli. Their compression-only point pressures remain nonnegative and
the tie remains positive. A center closure can be negative while the contacted
portion of the annulus is compressed. It does not mean negative physical
tension and does not trigger a center-pose bound. The first-order model still
uses direct bolt stretch plus the two signed center closures, with no geometric
shortening.

## CLI and finite disposition

Preparation performs hashes, metadata extraction and arithmetic on cached
fields only. It does not import the mechanical backend or execute a solve.
The parent runs the serial 23-state extension after its readiness decision.
The selected result is read from its original location and hash; its full
fields are not duplicated into a replacement witness.

```bash
KNEE_PACKET=docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout
.venv/bin/python "$KNEE_PACKET/knee-compatible-suite.py" prepare \
  --out "$KNEE_PACKET/rawlocal/knee-compatible-suite/prepare-attempt01"

.venv/bin/python "$KNEE_PACKET/knee-compatible-suite.py" run \
  --input "$KNEE_PACKET/rawlocal/knee-compatible-suite/prepare-attempt01/suite-plan.json" \
  --out "$KNEE_PACKET/rawlocal/knee-compatible-suite/suite-attempt01"
```

The preparation command is recorded for reproduction; once its child exists,
use its plan for the parent run or choose a fresh preparation child. All output
directories must be fresh descendants of ignored `rawlocal/knee-compatible-suite`.
Each new state gets a full mechanical result; every state gets a separate
arithmetic diagnostic receipt bound to its source result. `suite.json` contains
24 rows with full recovered receiver wrenches, closure results and diagnostic
peaks, and the terminal receipt binds every generated output. A returned method
stop or backend exception is recorded for the affected exact state; other
finite states are still attempted once. No retry, law change or sweep occurs.

This answers the recorded finite local K requirement within its isolated force
boundary if all 24 physical recoveries close. It makes no shared-group/body-pose
claim. That limitation introduces no blanket prerequisite. Complete elastic
timber qualification and actual hardware/wood acceptance are not asserted.
There is no frame, native, CAD, test, review, staging or commit operation.

## Prepared machine receipt

The metadata-only preparation is
[suite-plan.json](rawlocal/knee-compatible-suite/prepare-attempt01/suite-plan.json)
and its [execution receipt](rawlocal/knee-compatible-suite/prepare-attempt01/receipt.json).
All 20 direct original/upstream source and result pins matched; the exact
selected witness is retained at its original path. Ruff passed for the adapter.
The plan is 150,742 bytes and retains the selected cached stress arrays plus
the 24 finite boundary entries. No additional mechanics were executed.

| Prepared item | SHA256 |
| --- | --- |
| Adapter producer | `9798402070802a1804f4c9797fea336cda66951179340c1255e7122315990304` |
| `prepare-attempt01/suite-plan.json` | `223c0ad8919de48f271fde46141f2040f6fbed51f56c9dd1add8efff8d06421a` |
| `prepare-attempt01/receipt.json` | `7f01c8edba24bead4ab65b932306fa85e5e2c5bf654d9430d8032691b19ace2c` |

The parent subsequently executed that serial command once. Its terminal result
and the remaining exact states are recorded below; the command is a reproduction
receipt, not an instruction to retry this frozen attempt.

## Parent finite execution annotation: 10 closures, 14 method stops

The parent reported terminal **exit 2**, `STOP_finite_suite_method_defects`.
All 24 states were reported: the accepted selected witness was reused exactly,
and 23 new states returned fields after one API call each. No solve, retry or
law change was performed to make this annotation.

| Frozen terminal artifact | SHA256 |
| --- | --- |
| [suite-attempt01/suite.json](rawlocal/knee-compatible-suite/suite-attempt01/suite.json) | `0d7dff18b38d82130be212b1fc53fbb18a97c0e6f0c3a8c4a13e58fa3375910f` |
| [suite-attempt01/receipt.json](rawlocal/knee-compatible-suite/suite-attempt01/receipt.json) | `3180d95e9b7f146da7bc2dce40ec3d88c10b6152e3da9f06b70e11a9226187f1` |

The terminal receipt's 49 generated output hashes and all 24 result references
matched the cached files. The original producer remains `8bfd4aab…fb3413` and
the suite adapter remains `97984020…990304` (full values above).

**PASS** below means `conditional_first_order_equilibrium` with independent
three-receiver reference-traction closure. **STOP** means
`STOP_method_or_boundary_defect`; no physical failure is established.

| Physical shaft | a12-rear | a12-forward | a12-left | k12-right | k12-rear | a1-rear | PASS / STOP |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `knee_outer_left_side_1` | PASS | PASS | PASS (reused) | STOP | STOP | STOP | 3 / 3 |
| `knee_outer_left_side_2` | PASS | PASS | PASS | STOP | STOP | STOP | 3 / 3 |
| `knee_outer_right_side_1` | STOP | STOP | STOP | PASS | PASS | STOP | 2 / 4 |
| `knee_outer_right_side_2` | STOP | STOP | STOP | PASS | PASS | STOP | 2 / 4 |
| **Total** | **2 / 2** | **2 / 2** | **2 / 2** | **2 / 2** | **2 / 2** | **0 / 4** | **10 / 14** |

The maximum recovered residual across the ten closed states is
`2.684109290385095e−7 N` in force and `4.6654471134388587e−5 Nmm` in moment.

### Peak restricted to the ten closed states

Filtering the frozen rows to `independent_reference_equilibrium_closed = true`
gives the accepted-state peak at the original reused
`a12-left / knee_outer_left_side_1` witness. At element 9,
`x = 60.32499999999993 mm`, its same-state/same-position smooth-beam proxy is
**192.47938729087358 MPa**, from `T = 95.46010885208088 N`,
`M = 4762.395472545951 Nmm` and `V = 28.00667462274078 N`.
The declared 92 ksi and 45 ksi sensitivity ratios are respectively
**0.3034432053381555** and **0.620372775770947**.
Stress and pressure values from the fourteen stopped last iterates are retained
as method diagnostics; they are not accepted equilibrium predictions or
physical failure results. No static endpoint capacity is inherited.

### Exact stopped states and residual witnesses

All fourteen have the saved defect:
`Local iteration budget exhausted; compatibility has not been established`.
The retained last iterates exhausted the frozen 150-iteration budget. Residuals
below are the maximum absolute components of independently recovered receiver
wrenches, not only the free-coordinate Newton gradient. Display values are
rounded; linked frozen results retain full precision and all receiver fields.

| Frozen result | Case | Shaft | Max force residual, N | Max moment residual, Nmm |
| --- | --- | --- | ---: | ---: |
| [state-03](rawlocal/knee-compatible-suite/suite-attempt01/state-03.json) | k12-right | left side 1 | 30.031736 | 1714.232012 |
| [state-04](rawlocal/knee-compatible-suite/suite-attempt01/state-04.json) | k12-rear | left side 1 | 52.205802 | 1736.363114 |
| [state-05](rawlocal/knee-compatible-suite/suite-attempt01/state-05.json) | a1-rear | left side 1 | 35.991839 | 5355.241429 |
| [state-09](rawlocal/knee-compatible-suite/suite-attempt01/state-09.json) | k12-right | left side 2 | 78.654536 | 3243.802283 |
| [state-10](rawlocal/knee-compatible-suite/suite-attempt01/state-10.json) | k12-rear | left side 2 | 22.439436 | 545.274864 |
| [state-11](rawlocal/knee-compatible-suite/suite-attempt01/state-11.json) | a1-rear | left side 2 | 20.854784 | 9929.930282 |
| [state-12](rawlocal/knee-compatible-suite/suite-attempt01/state-12.json) | a12-rear | right side 1 | 53.087789 | 1767.726488 |
| [state-13](rawlocal/knee-compatible-suite/suite-attempt01/state-13.json) | a12-forward | right side 1 | 60.990010 | 2071.438534 |
| [state-14](rawlocal/knee-compatible-suite/suite-attempt01/state-14.json) | a12-left | right side 1 | 35.030579 | 1943.355505 |
| [state-17](rawlocal/knee-compatible-suite/suite-attempt01/state-17.json) | a1-rear | right side 1 | 25.520419 | 742.956833 |
| [state-18](rawlocal/knee-compatible-suite/suite-attempt01/state-18.json) | a12-rear | right side 2 | 22.160638 | 539.461602 |
| [state-19](rawlocal/knee-compatible-suite/suite-attempt01/state-19.json) | a12-forward | right side 2 | 46.842969 | 1676.483453 |
| [state-20](rawlocal/knee-compatible-suite/suite-attempt01/state-20.json) | a12-left | right side 2 | 80.917798 | 3336.151458 |
| [state-23](rawlocal/knee-compatible-suite/suite-attempt01/state-23.json) | a1-rear | right side 2 | 28.444481 | 1336.637904 |

The largest force-residual witness is `state-20`, specifically
`base_side_right`'s Z residual `+80.91779812923494 N`. Its recovered Y moment
residual is `+3336.151457551245 Nmm`. The largest moment-residual witness is
`state-11`, specifically `base_side_left`'s Y moment residual
`−9929.93028164206 Nmm`, with Z force residual `+20.85478379204507 N`.
Those are reference-geometry traction recovery defects at retained iterates;
they do not establish a failed adopted wood/bolt criterion or an incompatible
physical load path.

At this original-suite terminal the finite K requirement remained unresolved
for exactly these fourteen states. The parent subsequently completed the
numerical contact-entry correction recorded below. This historical annotation adds
no run, retry, law change, pose bound, shared-group/body-pose claim, or blanket
new prerequisite. The original negative rocking-center interpretation and
positive physical tie remain unchanged.

## Parent contact-entry completion: all 24 closed

The frozen parent producer `dd20bb23…ae6bd8` corrects only the loaded-neutral
numerical step using exact forward-ray entry into an existing inactive
circular bore. It retains the same K20 law, stiffnesses, gauge, first-order
beam/contact physics, independent traction recovery, Armijo acceptance and
closure tolerances. Its analytic circular-foundation coupon matched all three
cases with maximum pose error `3.774758283725532e−15 mm`.

| Corrected terminal artifact | SHA256 |
| --- | --- |
| [All-24 suite](rawlocal/knee-contact-entry/suite-attempt01/suite.json) | `b707952e5ad740ad2ebc0306bce17a37e4718e88c1164cba568d9a39a6e8b79a` |
| [Terminal receipt](rawlocal/knee-contact-entry/suite-attempt01/receipt.json) | `63224d7d4e25bd8705123f75dc60663f6b4fcb8ab998d149ed2507ec79ee5e43` |

The terminal status is `conditional_first_order_equilibrium_all24`.
The exact ten accepted original result files were reused byte for byte; the
fourteen originally stopped states received new closed results. This original
adapter `97984020…990304`, original producer `8bfd4aab…fb3413`, input contract
and failed iteration-limit result files remain unchanged.

| Physical shaft | Closed cases | Old accepted states reused | Newly closed states | Remaining STOP |
| --- | ---: | ---: | ---: | ---: |
| `knee_outer_left_side_1` | 6 | 3 | 3 | 0 |
| `knee_outer_left_side_2` | 6 | 3 | 3 | 0 |
| `knee_outer_right_side_1` | 6 | 2 | 4 | 0 |
| `knee_outer_right_side_2` | 6 | 2 | 4 | 0 |
| **Total** | **24** | **10** | **14** | **0** |

Maximum independently recovered receiver residuals are
**8.178873613928772e−7 N** (record 20, A12-left / right side 2) and
**4.6654471134388587e−5 Nmm** (record 6, A12-rear / left side 2).
The accepted same-state/same-position smooth proxy peak remains the original
reused A12-left / left side 1 witness: **192.47938729087358 MPa** at
`x = 60.32499999999993 mm`, with declared 92 ksi / 45 ksi sensitivity ratios
**0.3034432053381555 / 0.620372775770947**.

The [contact-entry evidence](knee-contact-entry.md) records every shaft's
maximum bore and wood-seat pressure, full-annulus mean reference indices and
raw witness hashes. Side-2 local peak/mean-reference indices of 1.003657071
and 1.036070505 remain reported diagnostics; they supply no adopted pointwise
failure criterion or other capacity. The negative center opening remains a
rocking-center position with positive physical tie and compression-only
annular pressure, with no pose bound.

**The bounded K loaded-shaft method is COMPLETE, conditional**, for exactly
four shafts and six current isolated force boundaries. No shared-group/body-pose
claim or blanket prerequisite is added. No static endpoint capacity, other
joint capacity, actual hardware/wood acceptance or physical release is
inherited. Only cached metadata, arrays and hashes were read for these final
annotations; no mechanics, code edit, review or test was performed. These
leaves return to the parent for publication.
