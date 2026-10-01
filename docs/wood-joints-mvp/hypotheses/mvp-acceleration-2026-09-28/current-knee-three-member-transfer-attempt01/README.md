# BG003 left knee three-member transfer — attempt01

**Status:** source-bound geometry and conditional NDS double-shear references
only. BG003 has no current signed bolt demand, adjusted capacity, pass, or
acceptance. This is the left outer-corner dependency slice; it is not a
full-frame result.

## Modeled stack and NDS bearing-length route

The source group inventory preserves `BG003` as one three-member stack with
axes `knee_outer_left_side_1/2`. The attempt04 interval order is
`knee_outer_left_spine` → `base_side_left` →
`knee_outer_left_inner_frame_block`; both axes agree and the member intervals
are contiguous in the modeled underhead coordinate. The raw modeled receiver
lengths along the +X bolt axis are 38.1, 88.9, and 88.9 mm, respectively
(1.5, 3.5, and 3.5 in). The member-section descriptors independently give
38.1 mm width for the spine and 88.9 mm width for the other two receivers.
These are model dimensions, not measured physical bearing lengths or proof of
delivered head-to-nut order.

NDS-2024 §12.3.5.1 measures dowel bearing length perpendicular to the applied
lateral load. For the modeled +X bolt and the conditional lateral directions
in the Y–Z plane, that bearing length is the receiver thickness along X.
Section 12.3.5.4 directly covers this unequal-side case: use the smaller side
member bearing length for both sides. Thus the NDS input route uses
`ℓm = 88.9 mm (3.5 in)` for middle `base_side_left` and `ℓs = 38.1 mm
(1.5 in)` for **each** outer side. This equalized `ℓs` is a code-prescribed
calculation input, not a change to either member and not an independent
pairwise-capacity construction.

The source-proposed grain vectors are `+Z` for both outer blocks and
`[0, 0.64278761, 0.76604444]` for the middle `base_side_left` (40° from +Z).
The modeled bolt axis is +X, perpendicular to all three proposed grains.
These are not delivered-stock observations. The lateral load-to-grain angle
`θ` in NDS is the angle between each member's action and its grain; the
bolt-axis-to-grain angle of 90° does not establish `θ`. Under a common lateral
direction, the two proposed outer grain directions match, but neither their
equal signed actions nor the actual direction is available. The current
material maps retain DF-L No. 2 only as a scenario; actual species, grade, and
grain are unresolved.

The order packet reports zero modeled interval gaps. The contact map also
records opposed nominal face patches of about 15,653.6 mm² at both adjacent
interfaces. Those geometric facts do not establish installed face contact,
active bearing, or a load-transfer law, all of which remain prerequisites for
applying §12.3.1 to the actual joint.

## Conditional numerical references

[`calculation.json`](calculation.json) records three directional scenarios
run through the existing symmetric wood/wood/wood double-shear helper. Each
uses model-based `ℓm = 3.5 in`, raw side lengths 1.5 and 3.5 in so the helper
applies `min(ℓs) = 1.5 in`, DF-L `G = 0.50`, `D = 0.25 in`, `Fyb = 45 ksi`,
zero thread bearing, zero modeled gap, and an ideal one-bolt signed action
pattern `(+1, −2, +1) lbf` for `(spine, base_side_left, inner block)` in the
listed lateral direction. `G = 0.50` is the NDS assigned DF-L input;
`Fyb = 45 ksi` is the published NDS Table 12F benchmark input, not a selected
bolt property; the 1/4-in full-body, no-thread case is also an assumption.
The artificial unit action only declares the symmetric scenario and is not a
joint demand.

| Conditional lateral direction | `θmain / θside` | Governing mode | One-bolt three-member `Z` reference |
| --- | ---: | --- | ---: |
| Global +Z, parallel to proposed outer grain | 40° / 0° | IV | 313.941 lbf |
| 20° between the proposed grain directions | 20° / 20° | IV | 334.158 lbf |
| Global +Y, perpendicular to proposed outer grain | 50° / 90° | IV | 260.909 lbf |

These are direction-specific *reference scenarios*, not an exhaustive
direction envelope, actual connection capacities, or demands. They each
represent **one bolt through one three-member double-shear stack**. The two
shear planes are handled together by the NDS double-shear modes; do not add
two separate single-shear capacities. Do not multiply this per-bolt reference
by BG003's two modeled bolts: group distribution and applicable group effects
are separate and unbound.

For a three-member connection, use the NDS §12.3.1A symmetric double-shear
route (`Im`, `Is`, `IIIs`, `IV`). Section 12.3.8 is for connections with four
or more members and supplies no multiplier here. Section 12.3.2 requires
applicable table footnotes to turn reference `Z` into adjusted `Z′`; no
adjustment is calculated. The reviewed multi-member helper accepts only
matched side properties, effective bearing length, load-to-grain angle, and
equal-and-opposite side action magnitudes. Its raw-equality check therefore
needs both sides entered at §12.3.5.4's derived 1.5-in `ℓs`, not at the raw
38.1/88.9-mm geometry. The local double-shear helper applies the same minimum
side-length rule and returns reference modes only. The maintained TR12 helper
covers the two-member single-shear equations; it does not authorize adding two
pairwise results for this stack.

## Missing actual corner transfer

The reduced-static assembly map represents BG003's two bolts as four adjacent
lateral spring rows (planes 37–40), one on each interface per bolt. Its
record says loads were not applied, native solve was not executed, and the
model was not ready for six-case response. The receiver/load-path ledger also
records no current solver DOF mapping or mechanical carrier for the corner
chain. Consequently, there is no continuous signed bolt-action map through
both shear planes and no basis for an actual symmetric-double-shear check.

For each load case and each BG003 bolt, the missing local signed lateral
vectors are the actions on `spine`, `base_side_left`, and `inner block`,
resolved in one global frame at the bolt point and reconciled across both
planes. The symmetric scenario requires equal same-direction outer-member
actions and an opposing middle-member action; for an isolated balanced
three-body scenario this is `Vspine = Vinner` and `Vbase = −2Vspine`. The
actual split cannot be inferred from stack order, face area, the two-bolt
pitch, or the external panel wrench. The per-axis distribution between the
two BG003 bolts is also missing. The source profile's ray geometry can inform
later direction-specific edge/end checks, but no signed load direction is
available to select those checks here; its query JSON is pinned at SHA-256
`5c820231ac4434e896ee708c72128672424ff158b3ee4458197cdadc1a4b0854`.

The local result must be compatible with the complete left-corner chain:

- **BG001:** `base_post_outer_left` ↔ `knee_outer_left_spine` (see the
  [post check dependency note](../current-knee-post-check-dependencies.md)).
- **BG003:** `knee_outer_left_spine` ↔ `base_side_left` ↔
  `knee_outer_left_inner_frame_block` (this stack).
- **BG045:** `knee_outer_left_inner_frame_block` ↔ `base_header`. The
  proposed block grain is +Z and the two BG045 axes are modeled parallel to
  it, so its NDS end-grain-axis route is separate and remains unassessed.

The next minimum evidence is a same-case signed force/moment transfer and
compatibility record through those three connections, including each BG003
axis's two-plane force split and the two-axis group distribution; verified
member order/contact and actual species/grade/grain; delivered bolt diameter,
root, thread interval and an ASTM-supported `Fyb`; and direction-specific NDS
§12.5 spacing/end/edge inputs plus applicable §12.3.2 adjustments. The
hardware register currently leaves the BG003 product unselected and delivered
shank, full-thread, and nut engagement intervals null. The nominal BG001 and
BG045 paths are corner dependencies, not blanket qualifications. The 12
retained baseline frame-bolt arrangements and the other introduced axes stay
separate; no baseline check is transferred to this new corner path.

## Source pins

- [BG003 inventory and pitch](../bolt-groups/README.md), structured
  [`bolt-groups.json`](../bolt-groups/bolt-groups.json), SHA-256
  `4a8b8f78db190d2e9841e5ad266356f0f0c5a402072d371938ad0760da0accb4`;
  two-axis spacing CSV SHA-256
  `74bcd73dc7683dc4e5960dc3dd6026cf920434c671121de60d2e6adb4d6cff5b`.
- [Modeled receiver order](../bolt-groups/three-member-stack-order-attempt01/receiver-stack-order.json),
  SHA-256 `e6a6d242ae2a62ecefafc4acbe8f3ea78a916aac4f48f53bdff84ec3c773055e`.
- [Member geometry](../reduced-static-attempt01/member-geometry.json), SHA-256
  `121f1940d0180367f953a1f92443964ded901ca775536750a9b028e37d6c8187`;
  [contact geometry](../reduced-static-attempt01/contact-geometry.json), SHA-256
  `034067430fff5207cdb40819fa8118a367edeb29a8d83926928cc96a0e87d151`;
  [assembly check](../reduced-static-attempt01/connection-assembly-check.json),
  SHA-256 `b474c686355b6fa74dfe158344340ebcb817f128a3c29f32bdb042649e93e02e`.
- [72-ray current-knee profile query](../current-knee-three-member-profile-attempt01/query.json),
  SHA-256 `5c820231ac4434e896ee708c72128672424ff158b3ee4458197cdadc1a4b0854`.
- [Frame grain map](../../evaluation-resume-2026-09-24/current-frame-timber-material-frame-map-attempt01/current-frame-timber-material-frame-map.json),
  SHA-256 `f867b4926ed23c9f356005c134778e138c8b1230547f0b69be7c3f9bc2a42409`;
  [block grain map](../../evaluation-resume-2026-09-24/current-block-material-frame-map-attempt02/material-frame-map.json),
  SHA-256 `8705b8f100a2d3355c236fc19e6798bb7ad4862ba2d51826cf63a88db1285480`.
- [Hardware axis register](../../evaluation-resume-2026-09-24/current-hardware-material-cost-closeout-attempt01/fastener-axis-register.json),
  SHA-256 `c1e53e9a08599d13a992fc11a493853c1695f697f3fe99b45af20795c430240a`.
- ANSI/AWC NDS-2024 Chapter 12, local review PDF SHA-256
  `5fc837523ff10acc097a162718700a9b4ba64e627d2b0023439146d42fe4ee2a`,
  especially §§12.3.1, 12.3.2, 12.3.5.1/12.3.5.4, 12.3.6.2, 12.3.7.2,
  12.3.8, and 12.5.
- The maintained
  [`nds_2024_multi_member_bolt_yield.py`](../../../../../mini_moonboard/nds_2024_multi_member_bolt_yield.py)
  SHA-256 `575d7de88d5f138412fef633ef946bccba884c1953b67e8d9211fc028d74ab89`
  has a parent-reviewed symmetric three-member route and NDS Table 12F known
  answer; see the [review record](../../evaluation-resume-2026-09-24/current-lateral-bolt-method-attempt02/parent-review.json)
  and [known-answer record](../../evaluation-resume-2026-09-24/current-lateral-bolt-method-attempt01/known-answer-validation.json).
  The numeric scenarios use the existing
  [`bolted_wood_wood_double_shear.py`](../../../../../mini_moonboard/bolted_wood_wood_double_shear.py)
  helper (SHA-256 `46a7be4202f32bdcb4631c6137574204f64aa44365b582ebe2369319052afcbd`)
  and DF-L dowel-bearing input in
  [`bolted_timber_checks.py`](../../../../../mini_moonboard/bolted_timber_checks.py)
  (SHA-256 `a1414547d9eaa3d60e81482b4a2cac2d49e88f31aafa341dca5be9ec8ef4aa13`).
  The separate TR12 generalized single-shear helper is
  [`fea/dowel_yield.py`](../../../../../fea/dowel_yield.py), SHA-256
  `d6c318e75c1a720d0b91f810a892e8309ef89735f66f48820ee853b753f8fe45`.
- [Receiver/load-path ledger](../receiver-load-path-ledger-2026-09-29.md),
  SHA-256 `c32a84b1045bcbaca1966e33254543d1ab04515799043793b2ee09ed39891466`.

## Parent numerical reproduction

The parent reproduced all four mode values for each scenario with the existing
helper and independently checked the double-shear mode-IV expression. Mode IV
governs all three; the references are 1,396.479 N (+Z), 1,486.407 N (grain
bisector), and 1,160.581 N (+Y). The unit action declaration establishes force
balance only, not the physical moment compatibility or actual side-load split.
The source-bound verifier checks five essential source pins and all scenarios:

```sh
uv run --no-sync python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-knee-three-member-transfer-attempt01/verify_calculation.py
```
