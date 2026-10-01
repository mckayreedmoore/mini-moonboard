# Current plywood material scenario evidence — attempt01

**Disposition: B — source-bounded identity record, no material assignment.**
`material_assignment_complete` is explicitly `false`. The owner’s existing
purchase record is retained as the chosen retail product record; this attempt
does not select another SKU or vendor. That record and the current primary
manufacturer/APA sources do not support a defensible layup and orthotropic
property interval for the six modeled panels. No solver card or native model
input is produced.

## What the existing record identifies

[`docs/purchased-materials.md`](../../../../purchased-materials.md),
SHA-256 `3a1e09c02e223cdec91ad96e258046e73322a23c6417252453f818624c3b8bad`,
records the owner-designated face-panel purchase as Roseburg at Lowe’s, item
12235 / model 119055, and records the owner’s September 11 reconfirmation of
“AC fir plywood” and that same product link. Preserve this procurement identity.
It is an owner-provided retail identity, not a received-sheet, lot, APA-mark,
or material-properties record.

The current Roseburg [Exterior Core page](https://www.roseburg.com/softwood-plywood/exterior-core/)
describes an AC Sanded Plywood option at 23/32 inch, **5 ply (O.C. 24)**, with
a fully sanded face and touch-sanded back. Roseburg’s current [sanded-plywood
brochure](https://www.roseburg.com/wp-content/uploads/2026/03/SandedPlywood_Brochure.pdf)
lists 23/32-inch AC exterior-core plywood as **5 or 7 ply** and describes a
western-wood core/back. These are family/option statements; neither
cross-references Lowe’s model 119055 or specifies the exact veneer sequence
for the owner’s item or sheets. The primary-source records therefore do not
resolve which published Roseburg option is this retail model. They also give
no exact received-panel strength/stiffness constants. A bounded search of
Roseburg’s current primary domain for `119055` and `12235` returned no product
cross-reference. The word “fir” in the owner’s retail record does not establish
an all-Douglas-fir veneer layup or species group.

APA’s current [plywood design page](https://www.apawood.org/engineered-wood-products/plywood-osb/plywood/)
states that structural properties vary with thickness, span rating, and load
direction relative to the strength axis. It directs design users to [Panel
Design Specification D510](https://www.apawood.org/guides-tools-training/technical-document-library/technical-guides/panel-design-specification/),
which provides tabulated design capacities and methods for PS 1/PS 2/PRP-108
panels. These design capacities are not a complete raw 3-D orthotropic elastic
tensor for a solid-element material card. APA describes the strength axis as
the long panel dimension unless otherwise marked, but no actual sheet mark or
mark orientation is in the record. No Structural I designation is assigned or
assumed.

## Exact current geometry bindings

The six rows below bind material status to the exact panel STEP files in
full-frame manifest attempt04 (manifest JSON SHA-256
`9e682e28c3d4c3c0594863f82c6b74d19dee2700f3856d34e1a26f69082e4f11`). They
identify modeled geometry only. They do not establish which physical sheet
became which body, veneer directions, layup, or properties.

| Current panel body | STEP SHA-256 | Scenario status |
| --- | --- | --- |
| `main_lower_left` | `78e2bd7b3a3f4cb6f70a1a2156ae3143cb936b29e5560dd6fd0cf6142aac6270` | Layup, material axes, and elastic properties unset |
| `main_lower_right` | `408d8ed97edf27954fa63221096af25da56a5aab02d53f77ecccbcfafb5b5d90` | Layup, material axes, and elastic properties unset |
| `main_upper_left` | `4be26c61e59ca3c74f370989097f4bff9edf337fa4de1a30d7e5de9eb7ef52f7` | Layup, material axes, and elastic properties unset |
| `main_upper_right` | `2791dca8f42b86a49b9e685f0f85d896642cbe9975a89bf1524bed89eddfea8f` | Layup, material axes, and elastic properties unset |
| `kicker_left` | `4740a18f46b8e8ecc2c01c80f7966228c498e35a09f10d7ccb32b08ea3cd8691` | Layup, material axes, and elastic properties unset |
| `kicker_right` | `d70c1fedf1c18304818a0f3adefdef0f64204f055a18d941ecd2b91a8dfe32b5` | Layup, material axes, and elastic properties unset |

The current [assembly guide](../../../../floor-flush-assembly-guide.md) gives
the four main panels as 1219.2 mm square, so their outlines do not distinguish
the two in-plane principal directions. The kicker outline has a geometric
long direction, but the exact sheet-to-body placement and strength-axis mark
are not bound. Therefore this attempt records no per-body principal-axis
vector. The geometry does not support a layup or property inference.

## Safely bounded fields

| Field | Disposition |
| --- | --- |
| Owner-designated retail item | Retained as Roseburg / Lowe’s item 12235 / model 119055; not independently cross-walked to a Roseburg technical product code |
| Received sheet IDs, mill/plant and lot | Unset; no receiving claim made |
| APA trademark, grade, span rating, standard edition, exposure and axis mark | Unset for the six sheets; retail description alone is not a sheet-mark transcription |
| Veneer species group, face/back grades, ply count and veneer sequence | Unset; current Roseburg AC 23/32 family literature allows 5- and 7-ply construction and gives no model-specific schedule |
| Principal material axes for each exact STEP body | Unset; no physical mark-to-body orientation binding |
| Orthotropic `E1`, `E2`, `E3`, `G12`, `G13`, `G23`, and Poisson ratios | Unset; no source-backed product-specific tensor or justified interval found |
| Density/material-card assignment | Unset by this artifact; the separate mass ledger is not a plywood elastic-property source |
| Structural I designation | Not assumed; no supporting panel mark or model-specific source |
| Solver material/body/element assignment | Not created |

The only current product-family construction envelope reported here is the
manufacturer’s 23/32 AC option as 5 or 7 plies, with C-grade-or-better
western-wood core/back. It is a literature envelope for Roseburg’s AC product
family, **not** an assignment or property bound for Lowe’s model 119055 or the
six physical sheets. No numerical elastic lower or upper bound is supported.

## Missing evidence needed to reopen assignment

The unresolved bridge is a source that cross-references the owner-designated
Lowe’s model to a Roseburg technical product/grade and to the actual APA
trademark on the delivered sheets. For each physical sheet, a future record
would need its unique sheet ID and full mark (manufacturer/mill, product
standard and edition, panel grade, category/thickness, span rating or species
group where marked, exposure/bond, and any strength-axis marking), plus the
layup/veneer schedule or a manufacturer property source that explicitly
covers that identified product. A sheet-to-panel-body map is also needed to
orient all six exact STEP bodies. Even then, D510 design capacities alone do
not supply every elastic constant required by a 3-D orthotropic solid material
card; an appropriate source for those constants or a different validated
material representation would still be required.

This record authorizes no receiving, test, model change, material card, solver
run, or acceptance change. Reproduce source-hash checks from the repository
root with:

```sh
sha256sum -c docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-plywood-material-scenarios-attempt01/source-pins.sha256
```

Online source snapshots are kept in [`sources/`](sources/) with retrieval URLs
and SHA-256 pins in `source-pins.sha256`. They were retrieved on 2026-09-27.
