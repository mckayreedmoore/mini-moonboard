# Working six-case joint force register

[working-joint-register.py](working-joint-register.py) produced one completed force register
for the original 100 mm frame state. It joins all six case IDs: `a12-rear`,
`a12-forward`, `a12-left`, `k12-right`, `k12-rear` and `a1-rear`. The existing
[machine index](rawlocal/joint-register/attempt01/register.json), its producer,
and historical results remain preserved.

The physical inventory stays at **104 bolt axes, 24 blocks and 66 separate
Hillman panel/kicker screw axes**. Eight top and eight bottom axes use completed
first-order local allocations. Four continuous knee shafts use the completed
contact-entry suite. The other 84 bolt axes retain their current original-frame
forces and saved method records, authenticated against the original response.
The twelve retained frame bolts remain among those 84 axes.

Each bolt has one axial tie. The knee shafts have two lateral planes and three
receivers each. The register separates those plane forces from each receiver's
net bore force, outer-end pressure force/moment distributions, and saved
same-state stress witness. The middle knee receiver acquires no outer tie.
Hillman axial actions remain parametric withdrawal, with no qualified stiffness
or resistance assigned.

## Allocation and equilibrium worksheet

Corrected states carry `integrated_frame_allocation` explicitly as comparison
evidence. Their current forces come from the named local result. Original frame
component ratios are not presented as current local ratios. The remaining 84
axes use `original_integrated_frame` as their current authority. Old block peak
tables are replaced by axis references in the new register.

`allocations.csv` records all **648 plane states** across **624 bolt/case
states**, including exact case, physical axis, plane, ordered receivers,
original/current signed vectors, vector differences, simultaneous original/current
V and T, stress witnesses and source pointers. Repeating T on a plane row is a
join convenience; `single_tie_identity` identifies the one physical tie.

The parent arithmetic run independently sums saved physical bore, seat and
face actions. Top checks compare with the original integrated boundary fields
in the preserved right/left block receipts. Bottom checks compare with the
separately saved preparation boundaries. Both check each host and the whole
cleat at explicit common datums, adding the cleat's own saved weight once.
Knee checks sum saved bore and outer wood-pressure actions against each of the
three original operator receiver boundaries, then sum the two shaft duties on
each side. Those shaft-duty boundaries exclude the other face/body duties;
they do not establish a shared knee-body pose. Header full action inventories
already include body loads; no additional weight is applied. The existing
central ring coupon is joined to its signed source-tie contract.

The completed parent output records that **local corrections preserve interface
equilibrium**. It **does not assert displacement feedback or global
compatibility**. The original frame response is unchanged. End pressure actions
already carry rocking moments; no balancing free couple is added. Saved local
smooth-section stress witnesses retain their exact case and position. The
header nominal section comparisons and central static compression route keep
their declared hypotheses. Complete joint acceptance and physical release
remain false.

## Completed parent attempt03

The saved [register](rawlocal/working-joint-register/attempt03/register.json)
records `COMPLETE_SAVED_FORCE_INTEGRATION`: **six cases, 104 physical bolt axes,
624 bolt/case states and 648 plane states**, plus 396 separate panel/kicker
screw states. It retains 24 blocks and 192 independent interface-equilibrium
receipts. The saved [receipt](rawlocal/working-joint-register/attempt03/receipt.json)
records that directly consumed sources were unchanged before and after writing.

The completed [worksheet](rawlocal/working-joint-register/attempt03/worksheet.md)
lists the explicit original/current force allocations and simultaneous ties.
Its saved boundary-gate peaks are copied here without replaying the accounting:

| Case | Maximum local/source force residual, N | Maximum moment residual, Nmm |
| --- | ---: | ---: |
| a12-rear | 1.51318e-05 | 0.000981442 |
| a12-forward | 1.29129e-06 | 5.90151e-05 |
| a12-left | 9.71977e-05 | 0.00663129 |
| k12-right | 1.92562e-05 | 0.000880055 |
| k12-rear | 1.8774e-05 | 0.0012413 |
| a1-rear | 9.91183e-05 | 0.00449957 |

Frozen completed output hashes:

| Artifact | SHA-256 |
| --- | --- |
| `register.json` | `c34745395481038e32c7474de1798882263de7e54a7cc494949948b4a5e3464c` |
| `receipt.json` | `026fe56a606e453a16faa94aecb4a9302c30ed970260e587ac36061e0104279b` |
| `allocations.csv` | `d062a16abcaacbe979c205c10aa95f03e5673993419152688b23203ec7c66f7d` |
| `worksheet.md` | `10fbfd910fdc059d90548810d3b004d45f51d8ede3e3e55fc6e36059867e7d78` |
| `producer.py.snapshot` | `6ae193808098e432bbc5e1d09c7307c51fd5bcc2f87984ccdec24b4900b9123c` |

## Frozen consumed results

| Source | SHA-256 |
| --- | --- |
| Original frame comparison | `bea6cbc330af3cdb20499d774a8f6bb24481d687c3150adb01ede18e4c1d50ca` |
| Original frame response | `0625196497b0dbc7b297724d7b9947f7c7c61bb282cd4d9681705629302c76c7` |
| Model | `b5f9b87b70c4a9920372a3443a55e37dfe34351fb9ac8210b299c1360fb93626` |
| Row identities | `cdf218780bdabdb8774174c79b37d7c9f554abc6be2e1f817999635e56868b27` |
| Preserved index | `79db8c6830dee42e47dcdcd75c331ce22a67cd3d27e38f9a8b616e820c37d3ca` |
| Index producer and saved snapshot | `c939fd65d340d6c332739525af381b5570290087621fef64e74a8302368c3a6a` |
| Top first-order forces | `b15b57d3879fdca2dac607d11a2ad127acd1008f6c2a6f546333a1b26c754cfe` |
| Top components | `f220673994b6a6c5b6bc0afd104becd61b5bb68f5e22bc700ed07b901b94525c` |
| Bottom first-order transfer | `4d255ba5ebd8f1f93fb41ef90511eb3da49906f4729f33f5f63766e0a0bd78ed` |
| Bottom components | `39e698d7ffec6646e2295f5ce96be0764ea8fbe6654ed3b0e881040b410bcc95` |
| Knee contact-entry suite | `b707952e5ad740ad2ebc0306bce17a37e4718e88c1164cba568d9a39a6e8b79a` |
| Header traction map | `39d63b41dc495659b02cb4ff4fb638a19a491bc09e6ea3fd76a70314db08a837` |
| Nominal header checks | `f582f87a45b80e9f95b5344bad289ce9837d4088135b21fc26c15dfc3e1d462d` |
| Central coupon | `bdc35b60ca03039f6e5acad8c5c81784086368a3472183ae7515f66335fe41bb` |

The producer also pins the original group-boundary packets, knee contract,
header/central contracts and saved receipts. Each knee result is authenticated
using its exact suite path/hash. Current frame method references use the earlier
index's direct output pins. Earlier source closures remain inherited provenance;
foreign temporary files and geometry are not reopened as new inputs. Existing
`cleat-traction.py` wrench arithmetic and `joint_register.py` CSV formatting are
reused; neither mechanical producer runs.

The parent arithmetic attempt01 stopped on a missing
`input_contract_sha256` field in a completed contact-entry witness. All 24
saved knee result schemas have now been inspected. They share the same
mechanical field layout and exact contract scope, but have three provenance
variants under the same `knee_three_receiver_first_order_witness/v1` schema:

| Variant | Count / suite indices | Authentication |
| --- | --- | --- |
| Completed contact-entry witnesses | 14: 3–5, 9–14, 17–20, 23 | Exact output path/hash in the completed suite and execution receipt; producer bound to its saved snapshot; input contract and original sources bound through the receipt's `source_receipts`. These files contain no per-result producer or input-contract hash. |
| Reused historical adapter witnesses | 9: 0, 1, 6–8, 15, 16, 21, 22 | Exact accepted path/hash from the historical suite and adapter receipt; per-result original producer, input-contract, coupon and adapter hashes; exact source-boundary pointer. |
| Reused original selected witness | 1: 2 | Exact selected output path/hash and its execution receipt; original producer, input-contract and coupon hashes. This file has no adapter or source-boundary-pointer field. |

All 24 result byte hashes match the completed suite. All 20 sources declared
in its receipt match their recorded bytes. The implementation checks the
current/historical source-receipt maps against each other and the exact input
contract, including the original comparison, response, model and row hashes.
It preserves the actually recorded per-result hash fields and separately
identifies the serialization producer. Every case/axis identity and suite index
must match its contract boundary; the 14/9/1 variant census is mandatory.
Receiver, plane, single-tie, same-state stress and independent wrench gates
remain in place with their existing tolerances. No force or capacity is changed.

## Parent API and serialized command

The API is `build_register(*, producer_sha256) -> (register, pins)`. It performs
the saved-action accounting in memory without writing. `allocation_rows(register)`
and `worksheet(register, allocations)` format the joined result. The CLI runs
that API once and writes a fresh child of the owned ignored raw directory.

Frozen producer SHA-256:
`6ae193808098e432bbc5e1d09c7307c51fd5bcc2f87984ccdec24b4900b9123c`.
From the repository root, the parent completed this command:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -B \
  docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/working-joint-register.py \
  --producer-sha256 6ae193808098e432bbc5e1d09c7307c51fd5bcc2f87984ccdec24b4900b9123c \
  --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/working-joint-register/attempt03
```

Outputs are `register.json`, `allocations.csv`, a concise `worksheet.md`, the
producer snapshot and `receipt.json` with all direct input/output hashes.
Existing output children are refused. Case/axis/receiver coverage and original
boundary preservation are mandatory before successful output; directly consumed
sources are rehashed before and after writing.

Parent completed the serialized arithmetic run in fresh attempt03; existing
attempt01 artifacts are preserved. This completion annotation uses only the
saved result and worksheet. The worker did not replay arithmetic, mechanical calculations, native/CAD execution,
tests, reviews or research. Ownership of the two leaves and owned raw directory
is returned to the parent, ready for commit. Parent owns integration into the
main README, current register, MVP sheet and shop addendum, and publication.
The completed packet remains active; no archive or prune is proposed. This
annotation changed only this Markdown leaf; no shared source, staging or commit
was changed.

Parent publication includes five parentheses-only string-format lint fixes.
The maintained producer and attempt03 snapshot now match. Attempt02 remains
preserved at producer `87d32263…dde365`, register `d6fbabe7…4ff44` and receipt
`d4490afd…9a249`. Its allocation CSV is byte-identical to attempt03: no force,
case, receiver, method or accounting value changed. No mechanical solve ran.
