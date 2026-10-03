# References from the accepted common knee shaft fields

[knee-common-references.py](knee-common-references.py) produced the parent's
frozen saved-field arithmetic result in
`rawlocal/knee-common-references/attempt01/`: exit 0,
**COMPLETE_SAVED_COMMON_REFERENCE_COMPARISONS**. Its import remains inert;
`prepare(output)` authenticates sources and identities using the standard
library. Parent-only `build(output)` computes the comparisons and exports
the end sources. This result annotation consumes the saved outputs; no
further build, test, review or engineering execution was performed.

The only force authority is accepted
`rawlocal/knee-common-shafts/attempt01/`: twelve common receiver equilibria,
24 shaft states, and 48 outer ends. The original producer remains frozen at
`540d2b4311de1fc46de1995305519bbfab2dc9efceedf3dda2b0e95f98784288`;
the accepted source Markdown remains frozen at
`34c289d3d442fc190ebcdfb189a265bcaac7c8d74e6c9a553f4f3fbbb9620c54`.
Old isolated shaft force fields, stresses, end moments, and passes are not
inputs to these comparisons. Original global per-axis T is retained only as
source-join metadata; the redistributed T is the demand.

## Actual arithmetic result

The parent build authenticated **150 exact source bindings** and recorded
**nine output hashes**, with sources unchanged before and after consumption.
Actual exports contain **24 source joins, 24 shaft comparisons, 2,880 smooth
section records, 1,728 bore records and 48 signed own-end sources**. The
summary lists zero smooth, nominal-thread, full-area wood-mean or local
wood-peak diagnostic exceedances and zero required wood/bore reference
nulls. These are the named conditional reference comparisons.

| Quantity | Actual peak demand | Named reference / peak index | Governing witness |
| --- | --- | --- | --- |
| Smooth steel envelope proxy | 288.891026 MPa | 507.454137 MPa; **0.569294849** | `a12-left`, `knee_outer_left_side_1`, element 8, x = 49.2125 mm |
| Separate nominal-thread tension | T = 316.672080 N; 15.435305 MPa | 507.454137 MPa; **0.030417143** | `k12-right`, `knee_outer_right_side_2` |
| Wood full-annulus mean | 1.482354 MPa | Perpendicular base 4.309223 MPa; **0.343995577** | `k12-right`, `knee_outer_right_side_2`, nut / inner frame block |
| Wood active-area mean | 1.677223 MPa | Perpendicular base 4.309223 MPa; **0.389216971** | `a12-left`, `knee_outer_left_side_2`, head / spine |
| Wood local pressure diagnostic | 3.495809 MPa | Perpendicular base 4.309223 MPa; **0.811238834** | `k12-right`, `knee_outer_right_side_2`, head / spine |
| Bore nominal full-D pressure diagnostic | 13.367035 MPa | Minimum Fe = 30.681670 MPa; **0.435668416** | `a12-left`, `knee_outer_left_side_1`, spine, x = 37.563258 mm |

At the governing smooth section the simultaneous demands are
**T = 111.500370 N, V = 338.058328 N and M = 7,146.989316 Nmm**.
The reported proxy combines that one section's envelope stresses; the peak
thread demand above belongs to its separate state. At the peak bore witness,
the saved traction/grain angle is 52.586327 degrees, the directional Fe is
33.198252 MPa, and the corresponding diagnostic ratio is 0.402642721.

The largest own-seat wood pressure moment is **1,179.093383 Nmm**, at the
`k12-right` side-2 head/spine end. Its physical signed XYZ vector is
approximately `(0, -1069.785781, -495.801966)` Nmm about its own seat at
`(1254.125, -77.302644, 365.787553)` mm. The nut on that same shaft has
**995.477372 Nmm** about its own seat. Downstream work must consume the
individual signed rows and datums, not use this peak for both ends. The
exported maximum hardware-contact pressure is **177.703678 MPa**, at the
`k12-right` side-1 head/spine end; it has no hardware capacity comparison.

All complete-joint, actual-material, washer-flexure, adoption and physical
release flags remain false. The first-order pose limitation below remains
unresolved by this arithmetic; no generic physical failure is asserted.

## Simultaneous steel comparison

Every one of the 120 saved section samples in each shaft state is processed,
giving **2,880 records**. T, both signed V coefficients, and both signed M
coefficients come from the same case, axis, element, and section coordinate.
Independent bending/shear peaks are not combined. For the retained smooth
6.35 mm circular shank:

`A = pi*D^2/4`, `I = pi*D^4/64`,

`sigma = abs(T)/A + norm(M)*D/(2*I)`,

`tau = 4*norm(V)/(3*A)`,

`smooth_vm_proxy = sqrt(sigma^2 + 3*tau^2)`.

This reuses the retained smooth circular-section envelope convention. It
combines section stress envelopes, not coincident fiber stresses; it is not
an exact fiber-level von Mises field or a thread-root calculation. The
conditional yield scenario is the pinned Grade 5 92 ksi machine-test minimum,
converted to **634.317670971456 MPa**. It is not a claim of delivered material
or test-derived NDS Fyb.

The owner-directed **1.25 reference convention is applied once**:

`steel_reference = conditional_yield / 1.25`,

`smooth_reference_index = smooth_vm_proxy / steel_reference`.

Saved T/V/M and pressures are unchanged. The unfactored yield ratio is also
reported, making the single reference divisor explicit. No second force
multiplier or yield reduction is applied.

Nominal thread tension is a separate 24-row comparison:
`sigma_thread = max(T, 0)/At`, where the pinned 1/4-20 nominal tensile area is
`0.0318 in^2 = 20.516088 mm^2`. Its reference index uses the same yield/1.25
convention once and also reports its unfactored ratio. It is never combined
with smooth-shank bending or shear as one physical section. Delivered root
area, shank exposure, transitions, engagement, head/nut strength and washer
capacity remain unqualified.

`SUPPORTED_COMPARISON` means the named finite reference index is at most one.
`EXCEEDANCE` means it is above one. Neither status is complete-joint acceptance
or an observed physical failure. Each shaft retains its own governing section
and its separate nominal-thread result.

## All wood seats and bore reference applicability

All **48 wood ends** retain their own solved T, own pressure moment, force
direction and pinned grain. Reference selection uses the force-normal/grain
angle: perpendicular uses the conditional dry DF-L No. 2 base **625 psi**;
parallel uses **1350 psi**; an oblique route stays null with an explicit
reason. The actual accepted four shaft axes are perpendicular to their
outer receivers' pinned longitudinal grain. The nonstandard inner blocks
retain their hypothetical final-section material scenario; no grade is
inherited from ripped stock.

For each saved wood annulus, build reports its full-area mean, active-area
mean, local quadrature peak, and each ratio to the applicable base reference.
Those demands are recomputed from saved weighted pressure/area records.
The local peak ratio remains a diagnostic against the named base reference,
not an adjusted joint-utilization rule. No wood duration, size, bearing-length
or steel 1.25 factor is added. Actual support masks, grain, grade, rigid
washer spreading, and the hypothetical concentric head/nut lands remain
unqualified. The metal-contact pressure is exported separately and receives
no invented washer or head capacity.

All **1,728 saved bore samples** are exported. The nominal full-D reference
uses the pinned 6.35 mm scenario, **5600 psi parallel** and **4450 psi
perpendicular**, with grain joined to the actual receiver. The conservative
minimum nominal reference is **30.6816699545976 MPa**. For a nonzero saved
traction direction, the existing conditional directional expression is also
reported:

`Fe_theta = Fe_parallel*Fe_perpendicular /`
`(Fe_parallel*sin(theta)^2 + Fe_perpendicular*cos(theta)^2)`.

An unloaded sample has no load direction; its directional reference is null,
while its zero pressure still has a finite minimum-Fe comparison. The
three-receiver connection has no adopted single-shear capacity here. These
pressure/Fe diagnostics do not qualify thread-bearing occupancy, actual
D versus Dr, group behavior, end distance, cuts or splitting. An unsupported
orientation is kept explicit; no old bore pass fills it.

## Forty-eight signed own-end moment sources

`washer-ends.jsonl` is keyed by
`(case_id, axis_id, end_role, receiver_member)`. Each row contains the
redistributed common tension, physical signed force and **own-seat M**, in
world XYZ and the recorded transverse basis. Head force on wood is +T n;
nut force on wood is -T n, where n points head to nut. `signed_T_n` follows
that projection; `normal_compression_T_n` is positive T at both ends.

Own M is summed from the saved weighted wood pressure forces about that
end's named seat datum. The corresponding hardware pressure acts on the
beam with the opposite force/moment. Build checks these point sums against
the saved wrench transported from the axis datum, the source contact moment,
and hardware/wood balance. It calls no contact or washer-flexure solver and
does not substitute a moment from an arbitrary force lever.

Rows include both annular pressure summaries, signed physical wrenches,
seat datum, source axis datum, transverse basis, contact closures/tilts,
catalog washer envelope, hypothetical land/ring radii, Kwood20/Khead10000,
zero preload and 215.9 mm grip. Pressure points are referenced through their
exact source path/hash/pointer instead of duplicating their arrays. Each
source join also names accepted report/receipt, geometry/boundary pointers,
original 540d producer, and the redistributed-demand policy.

This supplies the washer worker's own-end T/M and pressure inputs. Even a
steel reference exceedance exports its end sources. **N09_complete remains
false**: no washer steel stress, flexure, spreading, support-mask acceptance
or capacity comparison is performed.

## Shared-pose and other limits

The accepted common solution's peak shared rotation is
**0.098015958 rad, about 5.616 degrees**, at the left spine in `a12-left`.
Build records the actual saved rotation norm for every shared receiver.
These are gauged, first-order poses. Finite rotations, geometric shortening
and geometric stiffness were not solved or rechecked; the arithmetic does
not qualify their omission or turn those poses into measured frame motion.
The saved translation norm at this same rotation witness is **1.002230 mm**
at the side-origin datum `(-1174.75, -91.765365, 348.551553)` mm; it is not a
peak displacement of the whole frame. Steel and seat indices above remain
conditional on these saved first-order fields, with
`finite_rotation_rechecked: false`.

The four added internal v ties and external frame feedback remain separate.
Timber splitting/cuts and the parent's other 30 joint duties are outside
this leaf. Native, CAD, equilibrium, washer-flexure and software-test/review
execution counts are zero for this API. All complete-joint, proposal-adoption,
actual-material and physical-release flags remain false.

## Frozen sources and prepared closure

The implementation authenticates the entire accepted receipt's source and
output closure, then pins the applicable material and hardware reference
records. No mutable tracker or new field solve becomes authority.

| Source | SHA256 |
| --- | --- |
| Accepted common `receipt.json` | `7abd870ca5a3923937cc44ada389704f9977e0d3bb9ed0f546abb06ba283ffda` |
| Accepted common `report.json` | `dd6228320aaeaef898e68b738c05ade574be9fa28e8c7473648e9f21b5c7b2b0` |
| Accepted common `input-contract.json` | `7a38255a5e4bfcc49e7e2fd74b12117de7673dca769c6b17611a29cd0aa0f3a6` |
| Accepted common engineering reference | `24b3eb2e865b00cf02fb448bbfb533cf37a11b56a37b8cce127cb928c0c34183` |
| Pinned `material-inputs.json` | `0f33ad8fd517673a4ebbed36c4a30c1cfe07e0d8163165bdc804af91d958fc5a` |
| Pinned `fastener-inputs.json` | `ac8c5ca36105e3eab48f58c868794fc8a42d77cd54dfa5c76fb41f0934fd2ac2` |
| New reference producer | `cf0649425267b1e727b3a4876a544fb8e885f7510d2d41c7c7a7affccb325c37` |

`rawlocal/knee-common-references/prepare-attempt02/` reports
`PREPARED_SAVED_COMMON_REFERENCE_API`: **150 exact bindings** unchanged before
and after preparation, 24 source joins, and
`saved_field_arithmetic_executed: false`. Preparation reads sources, validates
identities and reference metadata, and writes no stress/pressure comparisons.
AST parsing and Ruff completed; no software test or review ran.

The preparation receipt SHA256 is
`948cd94ea0f463810c04ad6a5d790a2995ff789ff16222f9d8e4b27ceecb931f`;
its source-join export is
`9f2bf95d0ff1845d749b6a1ae749a565418a6821bf3518f1f887e9498216da88`.
The first preparation snapshot is also preserved.

### Frozen actual build closure

The frozen arithmetic receipt and reusable outputs are in
`rawlocal/knee-common-references/attempt01/`. The receipt pins the unchanged
`cf064942...325c37` producer and the same source joins as preparation.

| Actual build artifact | SHA256 |
| --- | --- |
| [receipt.json](rawlocal/knee-common-references/attempt01/receipt.json) | `172d616910ef2ff898383905eed795c82fa0a63b01e7a5861fef83399dafc5a9` |
| [summary.json](rawlocal/knee-common-references/attempt01/summary.json) | `18e4558eeecea5b75f618fcffb9b4bc694c13b57da3af861f3b13f60abb0800e` |
| [sources.json](rawlocal/knee-common-references/attempt01/sources.json) | `a52fd7b27e94ac1d14ac43bdbe5248189059b10922e3ca949b54717d039d73cf` |
| [source-joins.jsonl](rawlocal/knee-common-references/attempt01/source-joins.jsonl) | `9f2bf95d0ff1845d749b6a1ae749a565418a6821bf3518f1f887e9498216da88` |
| [shaft-references.jsonl](rawlocal/knee-common-references/attempt01/shaft-references.jsonl) | `7fa983ddb218db8b26f4472f65be73e4a3f4b8556c2add5f5308891c7ffc6110` |
| [smooth-fields.jsonl](rawlocal/knee-common-references/attempt01/smooth-fields.jsonl) | `cdc32b04b24bc48e97f330012a6008f1692fe81a07d58f1780c8415da14b5a16` |
| [bore-fields.jsonl](rawlocal/knee-common-references/attempt01/bore-fields.jsonl) | `6480a2f94e80ac192acc0af15ec945c83a14c86ffcda3ce715005313dc0ff866` |
| [washer-ends.jsonl](rawlocal/knee-common-references/attempt01/washer-ends.jsonl) | `95b1217391d814ca13677ba2b6a9930961e72a3b94ead0dd3a762a69adb01651` |

The nine pinned outputs also include `producer.py.snapshot` with the producer
hash above and `.gitignore` with SHA256
`cdbcae15105d6b781e620813c79c7e868740d4e9cc53ce6f5fcbbc12387adf4b`.
This Markdown was not a consumed or pinned source of the arithmetic build;
annotating it requires no replacement of a consumed Markdown snapshot.
The receipt, producer snapshot, outputs, both preparations and accepted
common-shaft source bytes remain frozen.

## Parent API and outputs

The callable entry points are `prepare(output)` and parent-only `build(output)`.
Both use the standard library. The destination must be a fresh immediate
child of `rawlocal/knee-common-references/`. The CLI defaults to preparation.
The parent executed the following arithmetic command; `attempt01` is now
frozen and this command is recorded for provenance:

```bash
python3 -B docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/knee-common-references.py \
  --build \
  --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/knee-common-references/attempt01
```

| Output | Reusable coverage |
| --- | --- |
| `source-joins.jsonl` | 24 exact `(case_id, axis_id)` joins to the accepted common records |
| `shaft-references.jsonl` | 24 section-governing smooth comparisons, separate nominal thread tension, three receiver bore diagnostics and two own-end join keys |
| `smooth-fields.jsonl` | 2,880 same-section T/V/M stresses and once-factored reference indices, with signed physical head-side cut force/moment and cut point |
| `bore-fields.jsonl` | 1,728 local pressure/direction/reference/applicability records |
| `washer-ends.jsonl` | 48 signed own-end T/M, saved-pressure integrals, means/peaks and orientation/reference records |
| `summary.json` | Actual governing witnesses, separate exceedance/null lists, pose limitation and count/status |
| `sources.json`, `receipt.json`, `producer.py.snapshot` | Exact source/output closure and producer identity |

The physical head-side section convention is preserved:
`F_cut = T*n - B^T*(EI*w''')`,
`M_cut = n cross (B^T*(EI*w''))`, with the opposite action on the nut-side
portion. Section M is the saved physical bending vector. No new timber cut
calculation is performed by exposing these shaft fields.

`COMPLETE_SAVED_COMMON_REFERENCE_COMPARISONS` means the requested arithmetic
and exports completed; any actual reference exceedances remain listed.
Required null wood/bore references yield `PARTIAL_NULL_COMMON_REFERENCES`;
source or arithmetic failure yields `STOP_SOURCE_OR_ARITHMETIC`. Neither is
promoted to completion from its census. The build reauthenticates sources
after consumption and preserves its owned outputs on failure.

The bounded arithmetic build and exports are complete. Active work is parent
publication and downstream consumption of the 48 own-end sources. Only these
two new leaves and their assigned ignored outputs are owned. The accepted common producer,
Markdown, raw runs and foreign work remain frozen. Staging, publication and
commits remain parent-owned; no archive or prune occurs.
