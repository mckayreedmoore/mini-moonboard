# Current header load paths

The six block/header interfaces contribute at most **7.404 × 10⁻¹² N**
of net Y force in the current six nominal states. Their 72 individual
lateral bolt states have 70 zero actions and two along-X actions. The header's
185.724 N connection-zone Y shear therefore must be attributed to the
surrounding load paths before it is used to assess a particular bolt joint.

This calculation identifies those paths using the existing response and
point actions. It leaves the geometry, stiffness, authority and all physical
release flags unchanged. Local resistance remains conditional and incomplete.

## Physical actions retained

For every case the header has 394 saved point actions:

| Role | Point actions per case | Main direction or function |
| --- | ---: | --- |
| Candidate bolt lateral components | 24 | Twelve Z-axis bolts; current lateral actions are zero or along X |
| Outer-seat bolt ties | 12 | Z force at the twelve through-bolt axes |
| Kicker screw lateral components | 20 | X/Z transfer at ten Hillman axes |
| Kicker screw withdrawal ties | 10 | Outward +Y transfer at the front Y face |
| Timber/panel contact cells | 116 | 52 kicker Y-face cells and 64 other Z-face cells |
| Discrete body loads | 212 | Recorded equivalent dead-load forces and free couples |

The producer compares **1,092 physical point wrenches** to their signed raw
force/operator rows, using the actual body datum. All agree exactly in this
execution. All six whole-header balances close: maximum residual is
6.789 × 10⁻¹³ N / 3.201 × 10⁻⁹ N·mm. The equivalent nodal dead loads retain
small, self-equilibrated Y terms; their K12-rear maximum is 0.000202006 N.
They are retained in the calculations.

The current nominal source preserves bounded, nonunique seating. It supplies
saved simultaneous forces, with complete-joint and physical-release flags
false. This worksheet adds no displacement or stiffness envelope.

## Z through-bolt load path

Header grain is +X. Its recorded envelope is Y = −175.7…−36 mm and
Z = 238.9…277 mm. The target shafts run along ±Z.

Some saved equivalent tie points lie on the other timber member's outer
seat, as far as Z = 416 mm. A pure Z force can be moved along its shaft line
to the header's own seat without changing its force or moment. The producer
performs that relocation, preserving the saved free couple:

| Header tie family | Own header seat line | Force on header |
| --- | --- | --- |
| Center-post pairs | Z = 277 mm | −Z, inward compression |
| Center-principal pairs | Z = 238.9 mm | +Z, inward compression |
| Inner-knee pairs | Z = 238.9 mm | +Z, inward compression |

All 72 tie states fit this direction-based construction. The largest
equivalent-point shift is 177.1 mm; the resulting moment change is exactly
zero. The relocation is an elementary line-of-action identity. Recorded
external boundaries identify the nominal seat line; actual washer/nut
contact distribution and metal spreading remain their existing evidence
requirements.

The header receives these forces through compressive seat bearing. Local
load transfer must preserve the accompanying timber contact and bending
couples. Existing through-bolts supply a concrete mechanical path across Z;
their adequacy is assessed with the recorded same-state bolt/washer/wood
checks, rather than by assigning a tensile-perpendicular allowable to wood.
This attribution alone establishes no complete reinforcement capacity.

## Y kicker load path

All ten kicker/header screw stations lie at Y = −36 mm, Z = 257.95 mm.
Withdrawal applies +Y to the header. The 52 compression-only kicker contact
cells act toward −Y on that same face. Their different X/Z positions retain
the same-state force and moment distribution.

The largest nominal outward point load is:

| Case / axis | Point XYZ, mm | Force on header XYZ, N |
| --- | --- | --- |
| A12-forward / `kicker_header_left_5` | −1000, −36, 257.95 | 0, +290.233146, 0 |

All 60 screw states are retained, including the zero state. Fifty-nine have
positive withdrawal above 1e-8 N. The primitive gross-beam normal field at
the screw face is evaluated on both sides of each load station:

`sigma_X = N/A − M_Z*y/I_ZZ + M_Y*z/I_YY`, with y = +69.85 mm and z = 0.

Forty-six of 60 states have tensile signs on both sides, including 45 active
withdrawal states. Six have compressive signs on both sides; eight include
a near-zero sign or a sign change. At the largest withdrawal state the
before/after signs are approximately zero / +0.056748 MPa. This is a
gross-beam bending-side selector. It supplies neither local perpendicular
stress nor a splitting resistance.

The local requirement is therefore specific: evaluate the actual kicker
withdrawal/contact distribution on the bending tension side where applicable,
together with its X/Z lateral screw actions. The Z-axis block/header bolts
do not span a Y crack plane. A section Y shear magnitude alone does not
identify the direction, application face or reinforcement of this path.

[The splitting basis](splitting-basis.md) applies the official NDS provisions
to these paths. Generic screw withdrawal resistance, header net-section
arithmetic and local perpendicular tension retain their distinct scopes.
No tensile-perpendicular design value is inferred from Fv or Fc⊥.

## Receiving segment at the tension-side probe

The largest active withdrawal state with tensile gross signs on both sides
is `k12-rear / kicker_header_left_1`: +Y 223.037504 N at X = −200 mm.
The saved finished section at that station is connected, with area
5135.251826 mm² and centroid Y = −107.572737 mm. Its exact saved covariance
is rotated from the source Z/−Y frame into Y/Z; simultaneous moments are
shifted to that centroid before evaluating a linear normal field.

The purchased nominal length is 63.5 mm and the source head origin is
Y = −17.74375 mm, along −Y. The full nominal tip lies at Y = −81.24375 mm.
This gives a conservative full-length receiving interval from the header
face −36 mm to that tip; actual head/tip/thread engagement is unqualified.
The historical 50.8 mm occupied CAD length remains an analysis envelope.

| Elementary connected-section field | Before cut | After cut |
| --- | ---: | ---: |
| Y where sigma_X = 0 at screw Z, mm | −107.966453 | −107.956186 |
| sigma_X at header front face, MPa | +0.756057 | +0.755595 |
| sigma_X at full nominal tip, MPa | +0.280740 | +0.280501 |

The entire nominal receiving interval stays on the tension side in this
linear field, with at least **26.712436 mm** between the tip and the
zero-normal-stress plane. The finished-section refinement therefore supports
the tension-side load-entry interpretation for this state. No existing
compression-side connection is established by the receiving segment.

This closes the bounded location/sign question raised by the splitting basis.
It establishes no local sigma_Y, fracture resistance, actual thread profile
or medium/heavy load classification. The applicable combined-load transfer
requirement remains open; the Z through-bolts provide no direct Y bridge.
Recalculate this path after an integrated panel correction changes the forces.

## Frozen inputs and output

| Input | SHA-256 |
| --- | --- |
| Current comparison | `0ff0dfc00c112a906910641141fd242f4a58295aa3324ca569132a3fa2d388a5` |
| Current response | `774c3bbddf8061f6b9d1cfdd5f22efbeb1025bd57431a249912ae8e60a731f52` |
| Member point/cut arrays | `3f89ad4290e93a2fed4a2526ae2cafa143ac64f3bac7bf40d46c71cd646b23e9` |
| Member geometry | `ecfeee2627fc67d91ce89acd5253bf99a4d79b06451c94ced6b915a664009f9d` |
| Current header interface actions | `fcdd3e85f7856220504de79f818724dbf271f029f1066143ec8335f59ed966a4` |

[load_paths.py](load_paths.py) pins those inputs, the current model/row/operator,
member report, nominal hardware input, section-frame plan and its own source.
All twelve pins are checked before and after the
arithmetic. The output preserves every Z tie state, Y screw state, per-role
wrench, scope statement and residual.

| Artifact | SHA-256 |
| --- | --- |
| Producer | `4361c8e47e8404057a76bba997d785020d2622f63db5583915d1f90cad7ad1a2` |
| [Current result](results/attempt03/result.json) | `fc01abc2ce52d1848c686dfb0f400f0fd41f277fbceefa417a13657add47b3e9` |
| [Initial topology result](results/attempt01/result.json), preserved | `124c4700a46c652390b424aa864e39473738eaec7da441222d11a801bf17eb41` |

Reproduce to a new direct child of the owned `results/` directory:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python \
  docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/header-local-transfer/load_paths.py \
  --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/header-local-transfer/results/replay
```

Both results and their exact producer snapshots are preserved and ignored.
The empty `attempt02/` contains no accepted result; a NumPy boolean
serialization error was corrected before the current run. Ruff check/format pass. This
work is saved-array arithmetic; no frame/native/CAD solve or software test
was run. The owned source and summary are published by the parent.
