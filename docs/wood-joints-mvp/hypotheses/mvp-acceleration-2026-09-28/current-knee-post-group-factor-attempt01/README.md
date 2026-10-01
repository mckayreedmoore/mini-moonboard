# BG001 conditional group-action factor screen

This packet evaluates the reviewed NDS-2024 group-action helper for BG001, the
two current candidate block attachments `knee_outer_left_post_1/2` between
`base_post_outer_left` and `knee_outer_left_spine`. BG001 is a new block
attachment group. The twelve retained baseline frame-bolt arrangements are
separate and are not requalified here.

The result is a conditional method row only. The reviewed helper returns
`Cg = 1.0` for both supported transverse-ring assignments, with
`capacity = null` and criterion disposition `pending`. It does not calculate
resistance, actual bolt-force distribution, demand/capacity, or acceptance.

## Source-bound conditional inputs

The geometry record pins two modeled 6.35 mm shafts whose axes are parallel
global X. Their centers form one straight global-Z row at 42.05 mm pitch. The
pure global-Z input is a 1 lbf direction-normalization vector. It is not a
prescribed BG001 force or an accepted load case.

The current finished member records give both receivers a gross section of
38.1 × 139.7 mm = 8.25 in² normal to global Z. The frame and block material
maps both propose grain along +Z. The only supported longitudinal modulus used
here is the named DF-L No. 2 diagnostic scenario, `E_L = 1.6 × 10^6 psi`,
applied conditionally to both members. Neither delivered stock nor its species,
grade, moisture, modulus, or ring orientation is observed by these records.

| Supported ring scenario | Main `EA` | Side `EA` | `Cg` |
| --- | ---: | ---: | ---: |
| `ring_R_on_X` | 13,200,000 lbf | 13,200,000 lbf | 1.000000 |
| `ring_R_on_T` | 13,200,000 lbf | 13,200,000 lbf | 1.000000 |

The two supported R/T assignments preserve the same +Z longitudinal axis, so
they do not change the `E_L` or gross area used by this lateral row calculation.
The supported cases therefore show zero `Cg` spread. With two fasteners and
matched main/side `EA`, the NDS Eq. 11.3-1 expression reduces algebraically to
`Cg = 1`; there is no group-action reduction in this matched conditional
scenario. The pinned sources do not provide an alternative longitudinal
modulus or gross area for these same members, so no unequal-`EA` perturbation is
invented.

## Limited reference scaling

The prior individual-bolt screen reports a 796.262 N unadjusted global-Z
reference under the explicitly assumed full-body 1/4-inch shaft, `Fe = 5600`
psi, and `Fyb = 45000` psi scenario. That source describes a scenario, not a
delivered fastener. Multiplying only by this screen's `Cg` and the two existing
conditional end-distance branches gives:

| Conditional end-distance branch | `Cg × CΔ × 796.262 N` |
| --- | ---: |
| Opposed parallel-grain tension; post 4D branch controls at `CΔ = 4/7` | 455.007 N |
| Reversed parallel-grain tension; sampled ends exceed 7D, `CΔ = 1` | 796.262 N |

These are `Cg/CΔ`-only scaled individual-bolt references. They are not adjusted
resistance, group capacity, or a pass/fail result. The sign branch cannot be
selected until a signed load case is supplied. Do not multiply either value by
two or infer equal bolt-force sharing from `Cg`.

## Required next inputs and exclusions

The missing signed group action is the BG001 wrench
`[F_x, V_y, V_z, M_x, M_y, M_z]` at the modeled group midpoint
`[-1208.151, -137.6, 192.475] mm` global XYZ, with its load case, cut side,
coordinate/sign convention, and source. The unit +Z vector in the helper input
only identifies a row-aligned direction.

The screen also lacks the delivered fastener dimensions and thread layout,
observed holes/gap/bearing planes/engagement, actual receiver material and
applicable adjustments, complete per-member end/edge/spacing and splitting
checks, washer/head/nut bearing, axial tie/contact qualification, and verified
transfer through downstream members. The bolt axes run along X while the row
and proposed grain run along Z. Axial `F_x` and separation, a possible `M_y`
tie couple, `M_z`, and the other lateral/torsional actions are not established
by this +Z `Cg` row result; the collinear-Z pair alone has no axial lever arm
for `M_z`.

## Reproduction and binding contract

From the repository root, run:

```sh
python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-knee-post-group-factor-attempt01/produce.py --verify
```

`coordinator-inputs.json` supplies the helper's expected source bindings and
static canonical payload digests separately from the payloads. The producer
also checks hashes for the geometry, material maps, full-frame manifest and
finished member STEP files; it checks that the source-derived bindings match
the coordinator manifest, independently hashes each canonical payload, and
compares that hash to the helper's canonical digest before invoking the
reviewed helper. `--print-input-digests` prints payload digests for inspection;
`--write-results` writes only `conditional-group-factor.json`.

The binding labelled `fastener_product` points to the prior named full-body
quarter-inch scenario source and explicitly says it is not a delivered
product. The coordinator hashes establish reproducibility only; they do not
verify source authority or provide independent engineering review. No source
geometry, reviewed helper, native model, or candidate member was changed.
