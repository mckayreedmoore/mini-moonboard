# Common receiver equilibrium for the four existing knee side shafts

The parent completed frozen `rawlocal/knee-common-shafts/attempt01/` with
`COMPLETE_12_CONDITIONAL_COMMON_RECEIVER_EQUILIBRIA`: the symmetric engineering
reference matched and all twelve common receiver equilibria closed their
combined signed full wrenches. Parent session 22086 exited 0; the original
150-step limit was unchanged. The [producer](knee-common-shafts.py) remains
byte-exact at SHA256
`540d2b4311de1fc46de1995305519bbfab2dc9efceedf3dda2b0e95f98784288`.
This annotation reads the frozen outputs only. The parent's independent
pin/recovery audit remains separate; no new run, test, review, or staging is
performed. Structural acceptance and physical release remain false.

This is the next numerical step after the authenticated common-pose conflict.
That preceding report is
`rawlocal/knee-bridge-common-compatibility/attempt01/report.json`, SHA256
`05741edf258ad5608d8db7414e7b2e52426ac01d6aa6e17c2bf1f06e79f28f7f`.
Its six minimum maximum residuals span 1.4996668–5.8565503 scaled mm.
The new model does not fit those isolated states or use their iterates.

## Bounded physical system

Each side has two retained continuous steel beams and one shared six-coordinate
pose for each of its spine, base side, and inner frame block. There are 200
transverse beam coordinates and 18 receiver coordinates, totaling 218.
The retained 25-node beam discretization, eight elements per receiver,
circular radial bore norm, and annular series-seat law are reused from
[knee-compatible.py](knee-compatible.py),
[knee-contact-entry.py](knee-contact-entry.py), and the authenticated
[fresh shaft adapter](knee-bridge-continuous-shafts.py).

The model retains Kwood = 20 MPa/mm, Khead = 10000 MPa/mm,
Ebolt = 200000 MPa, the 6.35 mm shank, 7.5 mm bores, 0.575 mm radial
clearance, and 215.9 mm wood grip. It preserves the existing concentric rigid
washer/head hypothesis and annular quadrature. It adds no preload, friction,
geometric stiffness, shaft torsion, thread-root resistance, or capacity.
The axial steel field is the exact uniform-tension extension of the continuous
shaft, because its retained bores supply no axial distributed load.

The prescribed load is **each receiver's combined two-shaft signed full
wrench** from the fresh nominal-gap source, including all three force and
three moment components. Each shaft's original force, moment, and tension are
diagnostics; the new solution can redistribute them. The three combined target
wrenches remain separate throughout loading and independent traction recovery.
The middle receiver's wrench must close too.

For a shared side origin O, each source moment is translated by
`M_O = M_datum + (datum - O) cross F`. The implementation rejoins the signed
raw rows, receiver ownership, point loads, and D blocks before constructing
these targets. The imposed external wrench is the negative of the target
connector wrench. Moment coordinates use `1000*theta`; physical moment
recovery remains in N mm about the recorded origin.

All other interfaces retain their fresh source forces. Their saved global
port motions and rigid coordinates are neither imposed nor updated by this
local calculation. No common frame displacement field or global feedback is
claimed. The four added internal v ties require their own passive law and
common elastic seat field; this task does not qualify them. Actual changed
hole stiffness, splitting, capacities, global stability, and structural
acceptance remain outside this result.

## Axial sharing without another prescribed shaft tension

For each shaft, the common poses determine the signed outer opening

`a = n dot [u_inner(nut seat) - u_spine(head seat)]`.

Let eta_h and eta_n be its two relative transverse end tilts. The retained
series-contact function supplies a dual energy C(T, eta), its closure c,
moment m, and fixed-T tilt tangent. Its derivative with respect to tension is
`C_T = -c`. With steel compliance `c_s = L/(E*A)`, eliminate the shaft's
tension through the concave maximization

`V(a, eta_h, eta_n) = max_(T >= 0) [C(T, eta_h) + C(T, eta_n) + T*a - c_s*T^2/2]`.

For positive tension this yields the physical compatibility equation

`a = c_s*T + c_head_stack(T, eta_h) + c_nut_stack(T, eta_n)`.

Both outer stacks carry that shaft's full T. No middle axial bore load is
invented. The implementation brackets this monotone scalar equation and uses
the retained seat function; it does not adjust a load, gap, or stiffness to
obtain a solution. It restores the fixed-T baseline energies that the isolated
transverse solver subtracted, so the reduced potential contains the actual
axial work and elastic energy.

For an active annular compression field, define S0 as active area, mu as its
area-weighted transverse coordinate, and D as
`k*sum_active(area*(x-mu)^2)`. For a head/wood series stack, differentiation
of the retained washer moment balance gives

`dc/dT = 1/(Kh*S0h) + 1/(Kw*S0w) + (mu_h-mu_w)^2/(D_h+D_w)`,

`dm/dT = (mu_h*D_w + mu_w*D_h)/(D_h+D_w)`.

These derivatives give the condensed tangent. If A maps the common poses to
opening and B_h/B_n map them to relative tilts, add

`outer(v, v) / [c_s + dc_head_stack/dT + dc_nut_stack/dT]`,

where `v = A + sum_ends[(dm/dT)*unit(eta)*B]`, to the retained fixed-T tangent.
This couples opening, tilt, and force sharing without another tension
coordinate or numerical penalty. The physical potential adds the retained
beam/bore energy and the source wrench work, and the parent solver searches
its equilibrium from zero common coordinates.

## Gauges and unloaded contact

Six common rigid modes use the base pose as their coordinate reference.
There is also one genuine unloaded mode: both outer receivers translate
together along the shafts relative to the base. The implementation verifies
that this vector changes no local beam/bore/end map or opening and does no
source work before choosing spine x = 0 as its representative. This removes
seven coordinates, leaving 211 free coordinates. No normal stiffness or
reserve is supplied to that mode. Final recovery checks the removed
coordinates' reactions as well as all three physical receiver wrenches.

At zero tension, separate seat closures are not unique. For the retained
rotating annular quadrature, the head has the smaller discrete transverse
support radius r. The unloaded condition is

`a + r*(|eta_h| + |eta_n|) <= 0`.

Here r comes from the existing quadrature points; it is not an extra washer
radius, geometric reserve, or capacity. The code records the slack explicitly.
The old T=0 helper returns a zero-energy closure placeholder at nonzero tilt.
That placeholder would produce false pressure if directly integrated.
Recovery therefore uses an admissible zero-pressure witness: all unloaded
tilt lies at the head contact, and half the available axial slack is assigned
to each end's head-contact closure. This is an arbitrary representative,
marked nonunique, with no force or stiffness. The separate unloaded closures
are not asserted to be physical observations or unique predictions.

The unchanged contact-entry Newton implementation is reused with its 150-step
budget and Armijo potential check. Its bore ray entry is supplemented by an
entry event for the actual unloaded seat inequality. At exactly zero opening
and zero tilt, the axial tangent uses the active-side generalized derivative
of `max(a, 0)^2/(2*compliance)`; the force and energy are zero. A loaded neutral
direction with no bore or seat event stops with an explicit unsupported
direction. Other unloaded contact modes retain the solver's null-space
treatment. No fictitious support is added.

Acceptance of a numerical state requires independent bore and annular point
traction sums to recover each combined signed full wrench to 1e-6 N and
215.9e-6 N mm. The common mixed-gradient tolerance is 2.159e-7 N so the
1000 mm rotation scaling also honors that physical moment tolerance.
Convergence alone does not pass recovery or any structural criterion.

## Executable API and parent execution

Import reads no evidence and imports no numerical library. The callable API
is `prepare(output)` and parent-only `build(output)`. Each output must be a
fresh immediate child of `rawlocal/knee-common-shafts/`; prior states are
preserved. The CLI defaults to standard-library preparation:

```bash
python3 docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/knee-common-shafts.py \
  --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/knee-common-shafts/prepare-parent01
```

The parent's completed build used the following entry point. `attempt01`
is now frozen and must not be overwritten or rerun for this annotation:

```bash
uv run --frozen --no-sync python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/knee-common-shafts.py \
  --build \
  --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/knee-common-shafts/attempt01
```

Build requires Python 3.12.3, NumPy 2.5.2, and SciPy 1.18.1, matching the
retained runtime and uv.lock. It first runs one small engineering reference:
two translated identical shafts at symmetric stations under 200 N centered
axial demand must share 100 N each and recover the analytic steel-plus-seat
opening. Per-shaft and combined receiver forces and moments are checked about
an offset datum with nonzero known moments. The retained beam/contact
engineering reference receipts are authenticated too. A new reference mismatch
stops before candidate cases. The reference is a method check, not acceptance
of the candidate or a software test.

If that reference matches, build attempts the six nominal cases on both sides
and writes each new equilibrium and recovery separately. A failed state keeps
its iterate and diagnostics and prevents a completion status. A source change
before or after execution also stops the result. Full-joint and physical
release flags remain false even if all twelve local equilibria close.

## Prepared source closure and retention

The completed lightweight record is
`rawlocal/knee-common-shafts/prepare-attempt02/`. It reports
`PREPARED_COMMON_RECEIVER_EQUILIBRIUM_API`, authenticates **130 exact source
files** before and after preparation, and constructs twelve combined-boundary
packets. Its D/point/source joins have maximum differences of
8.6401997e-12 N and 9.3132257e-10 N mm. This preserved preparation record has
false numerical execution flags and zero coupled attempts; the completed
parent build is recorded below.

| Frozen authority or prepared output | SHA256 |
| --- | --- |
| Fresh gravity operator assessment | `ce69ba58e3c6265d31ab0dfdec1ffac4c019b93fc1106c8f9677ed9b5b2c3f95` |
| Fresh frame comparison | `c3a8ff024fb494032d947aedfd6f00cda8698587b8751b2cec66e4b3af243729` |
| Fresh response arrays | `62bd4116cfb577a0846f4de0d43fbeec6bb704bac7feee530ee673ded1820f90` |
| Immutable fresh shaft input contract | `19f292683521bbc4f4def787fffcaaf686a266631f87fc54a14d888b6920a28b` |
| This implementation / final preparation snapshot | `540d2b4311de1fc46de1995305519bbfab2dc9efceedf3dda2b0e95f98784288` |
| Prepared input-contract.json | `7a38255a5e4bfcc49e7e2fd74b12117de7673dca769c6b17611a29cd0aa0f3a6` |
| Prepared report.json | `3225255dab8a6c79129acc82a0ef755f10050de21e1fbe63839413ec2f35c4ad` |
| Prepared receipt.json | `ca64995c486209e7b3eb5739073a1b77654b76648a73dd59b43292d33168b125` |

The complete source map is in the prepared input contract, report, and receipt.
Inherited historical files remain frozen provenance and method/geometry
references; their forces, capacities, and passes are not adopted here. Saved
isolated states are authenticated by their receipt without fitting or using
their iterates. Standard-library preparation reads only required array rows
through ZIP/struct; it does not call NumPy, SciPy, native, or CAD code.

## Completed parent reference and common equilibria

The frozen engineering reference reports `MATCHED`. The two identical shafts
each recover 100 N under the symmetric 200 N demand and the expected common
opening of 0.051040126161055736 mm. The combined receiver force error is at
most 4.2632564e-13 N and its offset-datum moment error at most 8.6401997e-12
N mm. The known combined moments are -4000 N mm on the spine and +4000 N mm
on the inner block about the reference's recorded offset datum; the base
wrench is zero. Per-shaft signed force/moment references also match.

All twelve states report `combined_full_wrenches_closed: true`, giving
24 redistributed shaft records. Maximum combined traction-recovery residuals
are 1.0068567e-7 N and 1.2430992e-5 N mm, both in right `k12-right`.
Maximum full mixed gradient is 1.0068567e-7 N. The longest history has 44
recorded iterates, in right `a12-rear`, within the unchanged 150-step budget.
The receipt reports all 130 source hashes unchanged before and after build.
The consumed output files match that receipt; independent source/recovery
authentication and publication remain parent-owned.

The following peaks are reductions of the saved fields, with their own
states and positions. They must not be combined into an invented same-state
load vector. Shaft x is measured from its head wood face.

| Saved quantity | Peak or range | Governing saved location |
| --- | ---: | --- |
| Redistributed shaft T | 316.672080 N | Right `k12-right`, `side_2` |
| Absolute change from original per-shaft T | 21.911240 N | Left `a12-rear`, `side_1`: 65.549049 → 87.460289 N |
| Transverse receiver resultant, `norm(F - n*(n dot F))` | 737.111572 N | Left `a12-left`, `side_1`, base side |
| Shaft section transverse V | 474.255535 N | Left `a12-left`, `side_1`, element 7, x = 33.3375 mm |
| Shaft section bending M | 7146.989316 N mm | Left `a12-left`, `side_1`, element 8, x = 49.2125 mm |
| Shared receiver translation norm at the side origin | 1.310026 mm | Left `a12-forward`, inner frame block |
| Shared receiver rotation norm | 0.098015958 rad | Left `a12-left`, spine |
| Beam transverse displacement norm | 2.302285 mm | Left `a1-rear`, `side_2`, nut-end node x = 215.9 mm |
| Bore relative transverse motion / radial penetration | 1.243352 / 0.668352 mm | Left `a12-left`, `side_1`, spine, x = 37.563258 mm |
| Bore foundation pressure | 13.367035 MPa | Same bore sample as the preceding row |
| Wood annular seat pressure | 3.495809 MPa | Right `k12-right`, `side_2`, head seat |
| Metal head annular contact pressure | 177.703678 MPa | Right `k12-right`, `side_1`, head seat |
| Signed common outer opening | -0.136849 to +0.157923 mm | Right `k12-rear`, `side_1`; right `k12-right`, `side_2` |

All 24 shaft tensions are positive, ranging from 24.465698 to 316.672080 N;
the unloaded-seat witness branch is not exercised by these candidate states.
The largest relative end tilt is 0.045992345 rad, at left `a12-left`,
`side_1`, head seat. Negative signed mean opening can coexist with positive
tension through eccentric annular contact at nonzero tilt. Its sign does not
indicate an observed overlap or loss of equilibrium. Axial opening stationarity
residuals are at most 1.3877788e-16 mm.

These are first-order, gauged poses and elastic-foundation demands. They are
not measured frame motions, qualified bearing/metal pressures, or capacity
comparisons. Finite-rotation effects, geometric shortening, actual elastic
timber fields and changed-hole stiffness remain omitted. The four internal
v ties and external frame feedback remain separate. No prior shaft stress
proxy, isolated per-shaft pass, member cut, splitting resistance, or seat
capacity is silently transferred to the redistributed fields.

| Frozen build output | SHA256 |
| --- | --- |
| `attempt01/engineering-reference.json` | `24b3eb2e865b00cf02fb448bbfb533cf37a11b56a37b8cce127cb928c0c34183` |
| `attempt01/input-contract.json` | `7a38255a5e4bfcc49e7e2fd74b12117de7673dca769c6b17611a29cd0aa0f3a6` |
| `attempt01/report.json` | `dd6228320aaeaef898e68b738c05ade574be9fa28e8c7473648e9f21b5c7b2b0` |
| `attempt01/receipt.json` | `7abd870ca5a3923937cc44ada389704f9977e0d3bb9ed0f546abb06ba283ffda` |

The report identifies each `state-NN.json` by side/case/path/hash, and the
receipt binds those outputs and the unchanged producer snapshot. The
engineering reference state is not part of the twelve-state candidate envelope.

## Reusable saved shaft, pressure, and cut API

Downstream work should consume the frozen JSON records without executing the
producer. Bind the report/receipt/output hashes above first. Select by
`(side, case_id, axis_id)` rather than relying on state numbering. The join
starts as follows; this example only reads saved results:

```python
import json
from pathlib import Path

root = Path("docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/"
            "upper-corner-screw-layout/rawlocal/knee-common-shafts/attempt01")
report = json.loads((root / "report.json").read_text())
inputs = json.loads((root / "input-contract.json").read_text())["contract"]
row = next(r for r in report["states"]
           if (r["side"], r["case_id"]) == ("right", "k12-right"))
state = json.loads((root / row["path"]).read_text())
shaft = next(s for s in state["shafts"]
             if s["axis_id"] == "knee_outer_right_side_2")
geometry = inputs["geometry"][shaft["axis_id"]]
boundary = next(b for b in inputs["boundaries"]
                if (b["case_id"], b["axis_id"])
                == (state["case_id"], shaft["axis_id"]))
```

The existing reusable fields and their conventions are:

| Quantity | Saved API | Interpretation |
| --- | --- | --- |
| T, N | `shaft["redistributed_tension_n"]` | The solved shaft tension; both outer stacks carry it. `source_tension_n` is the old allocation, not the downstream demand. |
| V coefficients, N | `shaft["beam_fields"][i]["EI_third_derivative_components_n"]` | Signed two-component `EI*w'''` in the recorded transverse basis; convert to a physical cut force using the convention below. |
| M, N mm | `shaft["beam_fields"][i]["physical_bending_vector_xyz_nmm"]` | Signed physical section bending vector; also stored as two-component `EI_curvature_components_nmm`. |
| Section coordinate | Each beam field's `element` and `x_mm` | Preserve the element's one-sided value at shared nodes. M is linear and V constant within each retained cubic beam element; interpolate that element's endpoints for a cut between saved positions. |
| Receiver full wrench | `shaft["receivers"][i]["independently_recovered_connector_wrench"]` | Force on wood and moment about `geometry["datum_mm"]`. Original-source and redistribution fields are diagnostics. |
| Bore traction and pressure | `shaft["bore_fields"]` | Receiver name, reference point, pressure, radial penetration, and already integrated `force_on_wood_xyz_n`; `force_on_beam_xyz_n` is its opposite. |
| Annular pressure and traction | `shaft["outer_seat_fields"][i]["point_tractions"]` | `wood_contact` acts on the recorded receiver; `head_contact` acts on the bolt. Each contains reference points, quadrature areas, MPa pressures, already integrated point-force vectors, and its integrated wrench. |
| Contact state | Each outer seat's `series_contact` | Head/wood closure, tilt, active area, pressure peak, and moment balance; retain signed closures and nonunique unloaded flags. |
| Common opening and axial residual | `shaft["normal_transfer"]` | Common pose opening, direct steel stretch, stationarity residual, and any unloaded slack. |
| Shared poses / target closure | State `receiver_poses_t_1000theta` / `combined_receiver_wrenches` | Shared origin is `state["reference_origin_mm"]`. Rotations divide by 1000; the base and axial float are gauged. |

For a **cut on the retained head-side shaft portion**, let n be
`geometry["bolt_axis_xyz"]`, B be the two row vectors in
`boundary["transverse_basis_xyz"]`, g be the saved `EI*w'''` components,
and k the saved `EI*w''` components. The signed cut quantities are

`V_xyz = -B^T*g`,

`F_cut_xyz = T*n + V_xyz`,

`M_cut_xyz = n cross (B^T*k) = physical_bending_vector_xyz_nmm`.

They act at `head_seat_point_mm + x_mm*n`. The nut-side portion has the
opposite cut force and moment. The stored `EI*w'''` components alone are not
a signed physical force on wood. Receiver transverse resultants and section
V are different quantities. Preserve the element, side, case, axis, basis,
cut point and signs; do not combine independently governing T/V/M peaks into
a demand that never occurred.

For a **wood-member cut**, use the saved on-wood bore forces and
`wood_contact` annular point forces on the chosen retained side of the cut.
These forces already include their quadrature weights/areas; do not multiply
them again. About a cut datum c, integrate
`F = sum(f_j)` and `M_c = sum((p_j - c) cross f_j)` using the stored
reference points. These are applied shaft-traction resultants on that wood
portion. Its balancing internal cut wrench is the negative of the complete
applied wrench after all applicable external interface/body loads are included.
Rebase a complete receiver resultant with
`M_c = M_datum + (datum - c) cross F`. A complete resultant cannot determine
the force distribution on a partial timber cut; use its point tractions.
Keep the receiver join in `geometry["receiver_order"]` and corresponding
grain vectors in `geometry["grain_xyz"]`. The downstream member assessment
must add its applicable other source-bound interface/body loads and preserve
the actual member/cut geometry. Those inputs are not supplied by these four
shaft fields alone. The annular profile is recorded in
`inputs["model"]["end_profile"]`; it remains the retained concentric rigid
washer/head hypothesis. These are demand/cut data, not cutting instructions,
wood stress solutions, or splitting/seat resistance.

Active work is the parent's independent authentication and interpretation,
then the downstream receiver/cut/seat comparisons using these saved fields.
The bounded common-shaft run is complete; it needs no duplicate execution.
Both preparation attempts, the completed build, and all source/conflict/isolated
records remain preserved. No archive or prune is performed. This annotation
changes only the Markdown leaf; producer and raw outputs remain frozen.
Staging, publication, and commits remain parent-owned.
