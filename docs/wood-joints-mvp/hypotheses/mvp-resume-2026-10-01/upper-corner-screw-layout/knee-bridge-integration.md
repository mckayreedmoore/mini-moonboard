# Knee-bridge integration manifest

**Parent data join complete: 50 bodies, 108 proposed axes, 624 existing force records and 24 internal T records / 48 ends. The proposal is unadopted.**
The [producer](knee-bridge-integration.py) exposes `build(output)` and has no
import-time work. Producer SHA-256:
`46b6966fe215408540acf636afa7e7638c2679d825f687c23eedac47c706ac46`.

The parent calls the API or the following command with a fresh immediate child
of `rawlocal/knee-bridge-integration/`:

```sh
.venv/bin/python -B docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/knee-bridge-integration.py \
  --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/knee-bridge-integration/attempt02
```

The implementation pins the supplied normal, geometry, fit, order and register
packets and receipts, and the current operator model. It preserves the saved
scene's four existing top STEP corrections and overlays only the two modified
spine STEP files. Their hashes are
`534ec2db81bbedfddba6cdf92c8703112231e970eff9b10e6a11fd11ce134645` (left) and
`847e644efdb36156a74dee1641e52a18cf17d301f03f59d2fa0bb68cd7d2b273` (right).
It maps canonical `proposed_v_bridge_1/2` IDs to the fitter's `bridge_g100/g250`
IDs by body and `(grain,u)`, then checks global centers, end seats and direction.
Both source names remain in the manifest and internal allocation export.

Completed output: one manifest joining 50 body references, 104 existing bolt
axes, two STEP overrides and four internal bolt axes; separate exports of
624 existing receiver force records and 24 proposed case/bolt T records with
48 ends. The proposed census and summed planning order are 108 bolts, 108 nuts,
216 washers and unchanged 66 Hillman screws. Existing saved allocations and
their original integrated comparisons retain their distinct provenance.

For each of the six cases, the producer reads the declared 1.25-margin T and
uses rational arithmetic on the canonical JSON coordinates and axis direction
to prove exact zero force and moment for each axial end pair on its single
whole body. This is the sole new mechanics arithmetic. It supplies no receiver
interface, floor restraint, lateral capacity or displacement solution. Original
H/D/e/W, force bytes and 250 lb × 2 / signed 300 N / 100 mm loads are retained;
their acceptance is not transferred to changed geometry or elastic operators.
The planning mass delta `+0.24795882906138145 kg` is not fed into global loads.
Compatibility remains unsolved, 47 criteria remain pending, eight release flags
remain false, and physical release remains false.

Fresh children contain `inputs.json`, `manifest.json`, the two force JSONL
exports, a producer snapshot and `receipt.json` with input/output hashes.
Consumed sources, geometry and authority bytes are authenticated before and
after the join; inherited source maps are preserved as provenance. No source
file is rewritten. The parent authenticated all 73 consumed source pins and
six receipt artifacts. All four aliases match their explicit body/station,
global center, direction and end seats. All 24 end pairs cancel exactly.
One lint-only set-comprehension correction followed the completed attempt01;
that packet is preserved, and both force exports are unchanged in attempt02.
Ruff passes. No software tests, review loop, native/CAD or frame solve ran.
Existing studies stay active; generated output belongs in the ignored child.

| Artifact under `rawlocal/knee-bridge-integration/attempt02/` | SHA-256 |
| --- | --- |
| `manifest.json` | `1744bb616354159c06694e99fb239251578dba3a6e860da5391dae19b5d7026c` |
| `receipt.json` | `8a2813419289bee46e2e0985ab702a602a8ff3a0d3aacdd43d1aad841c92c8df` |

The [shop delta](../assembly-package/knee-bridge-shop.md) and
[order delta](../assembly-package/knee-bridge-order.md) remain conditional
proposal records. Manifest status `UNADOPTED_INTEGRATION_PREPARED` means the
data recipe is ready; it does not assert an updated global response.
