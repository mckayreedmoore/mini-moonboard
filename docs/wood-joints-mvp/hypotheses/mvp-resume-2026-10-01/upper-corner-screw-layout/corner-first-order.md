# First-order corner forces and independent timber equilibrium

The simpler local model completes both actual upper corners in all six
nominal-gap cases: **12 block states, 24 two-bolt host models and 48 bolt
states**. The original frame force source, geometry, hardware, clearances,
contact laws and numerical tolerances remain unchanged. This packet replaces
the geometric-shortening branch for the continuation's local timber-force
recovery; it does not replace the integrated frame response.

## Why the local method changed

The [frozen traction recovery](cleat-traction.md) found that nominal bore,
washer and face forces left a right-cleat moment residual of 2660.691104
N mm. The residual was explained by the old fixed-axis `T G q` term,
whose rigid-rotation work is `T n × B(wL-w0)`. The balanced energy-dual
reaction alone did not supply physical timber tractions.

[corner-first-order.py](corner-first-order.py) privately imports the frozen
rail/side mechanics and actual left geometry. It sets each beam block's
geometric matrix to zero before evaluation. Thus geometric shortening,
preload stiffness and their energy, gradient and Hessian terms are omitted
together. Elastic bending, direct axial stretch, circular bore clearance,
compression-only face contacts and the two outer series-contact seats remain.
No balancing free couple or altered applied load is introduced.

This is a first-order model at reference geometry. Finite rotations and
second-order force geometry are outside its scope. The source 250 lb × 2,
signed 300 N horizontal force, original 100 mm lever, gravity and 25 kg
accessory allowance remain active.

## Engineering known answers and independent checks

Four cantilever coupons use each actual bolt family and receiver partition.
A 10 N tip force must give `FL^3/(3EI)` tip deflection, `FL^2/(2EI)` rotation,
and root reactions `-F` and `-FL`. Maximum returned relative error is
**8.462564e-12**. The coupons evaluate beam mechanics, not software tests.

Each loaded host is then checked independently by summing its bore forces,
its own washer-pressure samples and its face-cell forces at their reference
points. The cleat receives its own bore and nut-seat forces, opposite face
forces and its current mapped weight once. Pressure centroids carry their
own moments; no duplicate end couple is added.

| Maximum absolute component residual | Left | Right |
| --- | ---: | ---: |
| Host force, N | 0.00001926 | 0.00001144 |
| Host moment, N mm | 0.0004126 | 0.0002726 |
| Whole-cleat force, N | 0.00001514 | 0.00009912 |
| Whole-cleat moment, N mm | **0.0009814** | **0.0044996** |

All retain the original local tolerances. The old 2660 N mm discrepancy is
absent from the new first-order physical force inventory. This establishes
reference-geometry force/moment consistency, not complete wood resistance.

## Returned same-state witnesses

| Corner / witness | Case / axis | Returned demand |
| --- | --- | ---: |
| Left maximum axial tie | A12 left, rail_1 | 613.610019 N; simultaneous bore V 469.844766 N |
| Left maximum bore lateral | A12 left, side_2 | 975.110965 N; simultaneous T 469.059102 N |
| Right maximum axial tie | K12 right, rail_1 | 707.883638 N; simultaneous bore V 523.984519 N |
| Right maximum bore lateral | K12 rear, side_2 | 1098.756946 N; simultaneous T 505.698235 N |
| Left maximum smooth elastic steel proxy | A12 left, side_2 | 177.546233 MPa |
| Right maximum smooth elastic steel proxy | K12 right, side_2 | 202.182515 MPa |

Maximum sampled wood-seat pressure is 6.578867 MPa left and 7.403196 MPa
right. These are K20 contact samples, not an adopted peak-pressure wood
capacity check or a continuum maximum. Fresh component resistance comparisons
must use these new same-state forces rather than the earlier allocations.

Five host states in each corner retain neutral tangent modes, including the
seven-mode A1 rail state. Their returned poses are representatives, not motion
bounds or assembled tangent stability acceptance. The cleat and hosts remain
rigid; concentric rigid washer profiles, K20 wood foundations, smooth elastic
bolts and the declared head lands remain hypothetical.

## Reproduction and provenance

The parent executed one serialized local run after the cantilever coupons.
No CAD scene, native solver, software test or integrated frame was run by
this packet. Use a fresh child:

```sh
packet=docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 \
  .venv/bin/python "$packet/corner-first-order.py" \
  --traction-producer-sha256 2834a9a9fd25083da16034b498b3356197a4a6b2b53ffb35663077c5f93f7764 \
  --output "$packet/rawlocal/corner-first-order/attempt02"
```

| Artifact | SHA256 |
| --- | --- |
| Producer | `6e3f899ac99d6eef629ac12570b6ea31ea5c3914467c1c7399b7bcdd8d320563` |
| `rawlocal/corner-first-order/attempt01/checks.json` | `b15b57d3879fdca2dac607d11a2ad127acd1008f6c2a6f546333a1b26c754cfe` |
| `rawlocal/corner-first-order/coupon-attempt01/checks.json` | `9766109a7bd9ca2833753f91d56ed4d9b65638b1736b4a617a7ab42d36d9d94e` |

The full result authenticates 18 consumed sources, stores the independently
recovered cleat and host action inventories, and preserves the executed
producer snapshot. All earlier geometric-shortening results remain history
within their original scope. Whole-host exterior cuts remain reusable because
their complete interface wrenches are preserved; internal timber sections
use the new equilibrated actions. Local group/splitting, finished-opening,
washer-metal and delivered-hardware resistance remain separate unfinished
checks. Complete joint acceptance and physical release remain false.
