# Original corner transfers under the new knee-bridge gravity frame

**Parent execution complete: all four cleats and six cases balance.**
[The producer](knee-bridge-corner-replay.py) exposes `build(output)` for the
four original top/bottom outer cleats. Importing it performs no source reads or
calculations. The parent executed the local matrix calculations once; no coupon,
software test, native/CAD/frame solve or review loop ran. Fresh component
comparisons remain a separate calculation.

The only fresh case-load sources are the authenticated
`rawlocal/knee-bridge-gravity/attempt01` operators and
`rawlocal/knee-bridge-frame/attempt02/response` nominal raw forces. The six cases
remain `a12-rear`, `a12-forward`, `a12-left`, `k12-right`, `k12-rear`, `a1-rear`,
with 250 lb × 2, 300 N and the original 100 mm live-load placement. Modeled mass
is **225.19791414318078 kg**; dead factor is **1.1110134616260479**. The reported
maximum global row-force change of 1.418 N does not transfer an old local pass.

| Bound source | SHA-256 |
| --- | --- |
| `knee-bridge-corner-replay.py` | `b04289b5e3d2214c053eb5c0dd29f14836fcd84d81c3fd6acec2c5b8d7ab33cc` |
| `rawlocal/knee-bridge-gravity/attempt01/operator-assessment.json` | `ce69ba58e3c6265d31ab0dfdec1ffac4c019b93fc1106c8f9677ed9b5b2c3f95` |
| `rawlocal/knee-bridge-frame/attempt02/response/comparison.json` | `c3a8ff024fb494032d947aedfd6f00cda8698587b8751b2cec66e4b3af243729` |
| `rawlocal/knee-bridge-frame/attempt02/response/response.npz` | `62bd4116cfb577a0846f4de0d43fbeec6bb704bac7feee530ee673ded1820f90` |
| `corner-first-order.py` | `6e3f899ac99d6eef629ac12570b6ea31ea5c3914467c1c7399b7bcdd8d320563` |
| `bottom-corner-transfer.py` | `2b05f8a789ed1098d66a0b482c3c4531379a3b5c5bb538ef80f46adfc5356d77` |
| `cleat-traction.py` | `2834a9a9fd25083da16034b498b3356197a4a6b2b53ffb35663077c5f93f7764` |

The gravity assessment binds its output hashes; the fresh comparison must bind
that same assessment, model, inputs, rows and operators. Source closures are
checked before calculations and after output writes. Original preparations
supply the unchanged geometry, matrices and provenance; every historical case
wrench and weight is discarded before the replay. Original helpers and their
pins remain unchanged.

Each host boundary uses the new `<case>_gap_raw_force_n` vector, current row
ownership and the complete `-D_host.T @ raw` wrench, including rotational terms
converted to N·mm and shifted to the original interface datum. Source point
placements, receiver orders, full moments and any difference between the D
moment and point-force moment are retained. Each cleat's unchanged nodal
self-weight is recovered from fresh F columns, multiplied by the new dead
factor once, and checked independently against fresh W. Gross H/D and live
F/e/W fingerprints must match the original frozen inputs.

The producer calls the original preparation/configuration definitions,
`solve_case`, `physical_actions` and `recover`; it calls no historical
`run`/`build`/`main`, coupon or test entry point. Every geometric matrix is zero,
preserving the original first-order omission of shortening and preload
stiffness. No compensating wood moment is added. Independent host and cleat
interface force/moment errors use **0.001 N / 0.2 N·mm**; whole-cleat closure,
including its weight once, uses **0.002 N / 0.4 N·mm**. Source F/W and whole-cleat
boundary closure retain the original 1e-6 component checks.

From the repository root, the parent runs this once, serialized with other local
calculations, into a fresh immediate child:

```sh
corner_packet=docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 \
  .venv/bin/python "$corner_packet/knee-bridge-corner-replay.py" \
  --output "$corner_packet/rawlocal/knee-bridge-corner-replay/attempt01"
```

`checks.json` can claim `COMPLETE_FRESH_FIRST_ORDER_LOCAL_FORCES` only with
**24 distinct cleat cases, 48 host states and 48 top + 48 bottom bolt states**.
A local failure produces `STOP`, completed states, the partial host states and
the last iteration without relaxing a law or tolerance. Preparation/source
errors stop before local execution. The output child contains ignored
`fresh-transfer-inputs.json`, `checks.json`, `receipt.json` and a producer
snapshot; the receipt binds output bytes and source closure.

This is a fresh transfer API for the parent's component extractor. Existing
component replay entry points bind historical load packets and whole-result
schemas, so they are not called. `states[]` retains each cleat's own weight,
physical actions and both hosts' native local states. Each
`same_state_bolt_actions[]` entry is keyed by `(level, side, case_id, axis_id)`
and contains host/cleat identities, ordered geometry, the full `local_bolt_state`,
all beam fields and independent physical balance receipts. Its native bolt
record retains simultaneous `compatible_T_n`, signed `bore_force_on_host_xyz_n`,
`bore_moment_on_host_at_face_datum_nmm`, end-contact moments/pressures and the
smooth stress witness. Beam records retain signed `EI_curvature_M_components_nmm`
and `EI_third_derivative_shear_components_n`. Inherited `source_original_*`
field names refer to the authenticated **new** raw-force components.

Fresh component-reference comparisons, redistributed timber cuts,
group/splitting resistance and washer/hardware resistance are outside this
transfer packet. Rigid timber, K20 wood/K10000 head contacts, concentric rigid
washers, circular clearance and smooth elastic bolts retain their conditional
scope. Representative poses do not establish stability or motion bounds.
Proposal adoption, criterion/joint acceptance and physical/fabrication release
flags stay false. The goal remains the conditional shop model under its stated
assumptions; no new external sign-off gate is introduced.

## Completed parent result

`rawlocal/knee-bridge-corner-replay/attempt01/` contains **24 cleat states,
48 host states and 96 bolt states: 48 top, 48 bottom**. The parent authenticated
all **94 source pins and four receipt-bound artifacts**. Maximum independent
host, cleat-interface and whole-cleat errors are respectively
**0.000097 N / 0.000990 Nmm**, **0.000100 N / 0.007271 Nmm** and
**0.000100 N / 0.004508 Nmm**, below the retained component tolerances.

The top peak tie is **707.883251 N** at right/K12-right `rail_1`, with concurrent
host bore resultant **523.976992 N**. The bottom peak is **203.597843 N** at
left/A1-rear `side_1`, with **243.435431 N** concurrent bore resultant. These
fresh demands preserve the full moments; they establish no hardware capacity.

| Artifact under the completed child | SHA-256 |
| --- | --- |
| `checks.json` | `e699b5c662992abab1f646236cdd4037feb425c5476458d8629899bcb9948976` |
| `receipt.json` | `50898edc4d0d977c7522c3c30866504235f847ee6d3777345114afb4d86cd52d` |

The separate spine producer uses the modified six-bore solids. Historical corner
sources and runs remain preserved; no historical acceptance transfers.
