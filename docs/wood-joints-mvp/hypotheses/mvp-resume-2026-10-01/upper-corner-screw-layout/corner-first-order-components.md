# Both-corner first-order component replay

**Parent execution complete: all forty-eight same-state component records
returned.** This packet applies the existing single-shear,
finished wood-path, supported washer-annulus mean and conditional smooth-bolt
references to the parent's corrected first-order local forces for both actual
upper corners. It changes no geometry, hardware, source frame or authority.

## Frozen force input and scope

The parent completed `rawlocal/corner-first-order/attempt01/checks.json`,
SHA256 `b15b57d3879fdca2dac607d11a2ad127acd1008f6c2a6f546333a1b26c754cfe`.
Its status is `COMPLETE_FIRST_ORDER_LOCAL_FORCES`, with no failure. Twelve
block states retain both corners in each of the six nominal-clearance cases,
twenty-four host-pair models and forty-eight bolt responses. The corrected
first-order calculation omits geometric shortening and prestress stiffness
consistently and adds no balancing free couples. Independently recovered
physical host and cleat tractions now balance under that stated model.

The six cases remain A12 rear, A12 forward, A12 left, K12 right, K12 rear
and A1 rear. Every corner has two rail bolts and two side bolts, with its
actual station names, hosts, grain axes and saved geometry. Left and right
loads are consumed separately; no symmetry acceptance is inferred.

The integrated frame remains the original 100 mm force-lever source at
`frame-250-attempt02/`, comparison
`bea6cbc330af3cdb20499d774a8f6bb24481d687c3150adb01ede18e4c1d50ca` and response
`0625196497b0dbc7b297724d7b9947f7c7c61bb282cd4d9681705629302c76c7`.
Local first-order redistribution does not feed back into that frame. This
replay neither repeats a mechanics solve nor selects another lever case.

## Same-state reference calculation

The producer reuses the pinned [earlier component replay](upper-left-block-components.py)'s
exported `corner_checks.lateral_reference` function. It does not call the old
replay entry point or borrow its individual force allocations. Geometry and
wood references come from
`bolted-replay-results/corner-attempt01/component-results.json`, SHA256
`401b8876dc3a96b553c847f1029a5a9200ba3f45af5493f64edd61fdc6bc42b6`.

For each changed bolt response, the four references use the following
simultaneous inputs:

| Reference | Same-state input and retained basis |
| --- | --- |
| Single-shear lateral | Negative host bore-force vector gives the signed lateral force on the cleat. Its magnitude and actual two grain angles enter the existing function with 6.35 mm rail or 7.9375 mm side diameter, actual receiver lengths and conditional 92 ksi `Fyb`. Existing rail `Cg*Cdelta` modifiers remain unchanged. |
| Finished bore-tangent path | The signed force component along that cleat's grain selects its own positive or negative finished path. Its magnitude is divided by 1.241056313 MPa times the frozen minimum one-plane finished area, preserving the earlier formula and scope. |
| Washer-seat mean pressure | That bolt's compatible positive tension is divided by its frozen minimum supported cleat annulus and conditional `Fc_perpendicular = 4.309223308 MPa`. Rail grip is 38.1/139.7 mm; side grip is 88.9/88.9 mm. |
| Smooth-bolt steel diagnostic | The same bolt state's recovered beam sectional von Mises proxy and its ratio to the hypothetical 92 ksi comparison are copied together. Local beam bending remains included; no thread-root or delivered-steel resistance is invented. |

All forty-eight records retain corner, case, axis, signed force, tension,
grain-angle reference, selected path, washer area and beam-stress diagnostic.
Global and per-corner peak witnesses each retain the entire governing record;
independent force maxima are not combined into a fictitious state.

The new receipt also retains the source's independently recovered physical
host/whole-cleat balance residuals and exact mapped weight once per cleat.
It checks their existing numerical tolerances without recomputing tractions
or adding another equilibrium model. Original complete-host splitting
records remain geometry/scope history. They are not redistributed cut
demands or an adopted design splitting resistance.

Mean-annulus pressure is separate from sampled contact-spring point pressure.
Combined oblique-group/splitting, elastic timber/cleat response, washer metal,
delivered hardware and physical acceptance remain outside this component
replay. Completed arithmetic alone does not close joint HOLD.

## Completed component references

The parent ran the frozen producer successfully. Its status is
`COMPLETE_SAME_STATE_COMPONENT_REFERENCES`: twelve block states,
twenty-four host models and forty-eight bolt states, with twenty-four bolt
records on each side. These maxima are taken from the fresh first-order
records, retaining each governing case/axis and its simultaneous inputs.

| Corner | Reference screen | Maximum index | Governing case | Bolt |
| --- | --- | ---: | --- | --- |
| Left | Single-shear lateral / adjusted reference | 0.722296 | A12-left | `side_2` |
| Left | Parallel force / finished tangent path | 0.142295 | A12-left | `side_2` |
| Left | Full-annulus mean washer pressure / `Fc_perp` | 0.666554 | A12-left | `rail_1` |
| Left | Smooth-bolt beam VM / conditional 92 ksi | 0.279901 | A12-left | `side_2` |
| Right | Single-shear lateral / adjusted reference | 0.813949 | K12-rear | `side_2` |
| Right | Parallel force / finished tangent path | 0.160367 | K12-rear | `side_2` |
| Right | Full-annulus mean washer pressure / `Fc_perp` | 0.768962 | K12-right | `rail_1` |
| Right | Smooth-bolt beam VM / conditional 92 ksi | 0.318740 | K12-right | `side_2` |

Left axis names are under `top_outer/clip_single_top_left_1/`; right names
are under `top_outer/clip_single_top_right_2/`. The left steel witness is
177.546233 MPa, with the same A12-left `side_2` tension 469.059102 N and
bore lateral resultant 975.110965 N. The right steel witness is
202.182515 MPa, with the same K12-right `side_2` tension 508.930770 N and
resultant 1097.575809 N. The right governing lateral/path record instead
belongs to K12-rear `side_2`, T=505.698235 N and V=1098.756946 N; those
different cases are not combined.

The left governing mean-seat record is A12-left `rail_1`, T=613.610019 N;
the right is K12-right `rail_1`, T=707.883638 N. Their sampled end wood-seat
point pressures are 6.578867 and 7.403196 MPa respectively. The tabulated
mean indices use supported annulus areas and the unchanged mean-bearing
reference; they do not treat those point pressures as a qualified local
contact capacity.

The source's maximum absolute independently recovered whole-cleat balance
residuals, retained in this receipt, are 1.513183e-5 N / 9.814427e-4 N mm
on the left and 9.911834e-5 N / 0.004499566 N mm on the right. Both remain
within the source's existing numerical tolerances. This is a source
physical-traction receipt, not a new mechanics or timber stress calculation.

All reported component maxima are below their declared reference value.
They remain conditional individual component screens. No combined
oblique-group/splitting, washer-metal, delivered-hardware or complete-joint
pass is inferred. `complete_joint_acceptance` and `physical_release` remain
false.

## Parent execution and receipts

Producer: [corner-first-order-components.py](corner-first-order-components.py),
SHA256 `64927dce0058a2be67e3c55f82fc5a5649f91a908f6aa3ba6bdbc8dcfb39ec92`.
API: `build(Path(fresh_output))`. The fixed source is the first-order receipt
above. The parent executed the following from the repository root:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 \
uv run --no-sync python \
  docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/corner-first-order-components.py \
  --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/corner-first-order-components/attempt01
```

Use a new output child for another execution; the completed `attempt01/`
is preserved. The producer binds the first-order result's
complete source closure, the frozen geometry/reference packet and arithmetic
dependencies before computation and again before its final receipt. It
writes `checks.json`, `receipt.json` and a byte-exact producer snapshot under
the ignored child. The receipt binds all forty-eight component states,
global/per-corner peaks and source/output hashes.

All twenty-five source bindings and both output bindings in the parent's
receipt were authenticated after the run. The executing producer, maintained
source and raw snapshot remain byte-exact. Completed raw files are under
`rawlocal/corner-first-order-components/attempt01/`.

| Artifact | SHA256 |
| --- | --- |
| `checks.json` | `f220673994b6a6c5b6bc0afd104becd61b5bb68f5e22bc700ed07b901b94525c` |
| `receipt.json` | `c4f3e6a98ca6883cd9255a87e3fb8b66ef0753cffd5d1079cf8fd33e36d9a238` |
| `producer.py.snapshot` | `64927dce0058a2be67e3c55f82fc5a5649f91a908f6aa3ba6bdbc8dcfb39ec92` |
| First-order force source | `b15b57d3879fdca2dac607d11a2ad127acd1008f6c2a6f546333a1b26c754cfe` |
| Frozen component geometry/references | `401b8876dc3a96b553c847f1029a5a9200ba3f45af5493f64edd61fdc6bc42b6` |
| Frozen previous component arithmetic | `893a96221e13dab832d949271b7d9f0c022a1ec71e522a576f603458f93a25e3` |

Targeted Ruff passes. The worker prepared only these two leaves, read saved
source/output records and ran lightweight lint. It has not executed this
producer, geometry/support/CAD/native/frame/mechanics operations, software
tests, a review loop, staging or a commit. No second producer execution was
performed after the parent receipt. Both leaves are frozen at handoff;
parent owns shared staging, integration and publication.
