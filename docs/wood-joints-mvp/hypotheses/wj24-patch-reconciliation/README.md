# WJ16 representative mesh geometry versus WJ24

Status: source-bound finished-wood comparison completed on 2026-09-24. The
parent's fresh live WJ16 and WJ24 objects each reproduced their archived
composition reports before comparison. The exact producer output is
[comparison.json](comparison.json); its executed source is preserved in
[executed-comparison.py.snapshot](executed-comparison.py.snapshot). The hash
index binds both files and records the composition and durable old-mesh archive
hashes.

The earlier mesh uses five finished WJ16 bodies from the representative WJ04
right-side joint. Four bodies have zero OCC symmetric difference against the
complete WJ24 baseline. The principal has changed, so the five-body WJ16 mesh
does not describe complete WJ24 geometry.

| Representative body | WJ16 volume (mm³) | WJ24 volume (mm³) | Removed WJ16 material (mm³) | Added WJ24 material (mm³) | Result |
| --- | ---: | ---: | ---: | ---: | --- |
| `base_rail_service_lower_right` | 5,300,088.326703 | 5,300,088.326703 | 0 | 0 | Same solid |
| `base_rail_service_upper_right` | 5,300,088.326703 | 5,300,088.326703 | 0 | 0 | Same solid |
| `base_principal_center_right` | 13,064,473.889421 | 13,064,685.127371 | 6,732.825756 | 6,944.063705 | Changed; 4 removed regions and 6 added regions |
| `wj04_lower_full_stock_cleat` | 930,304.310237 | 930,304.310237 | 0 | 0 | Same solid |
| `wj04_upper_g7_crosscut_full_stock_cleat` | 671,079.022237 | 671,079.022237 | 0 | 0 | Same solid |

The principal's net volume increase is 211.237949 mm³, while its two-sided
symmetric difference is 13,676.889461 mm³. This is a useful example of why a
net volume delta cannot stand in for a solid-to-solid comparison. The full
coordinates and volumes of each removed or added solid are in
[comparison.json](comparison.json).

The principal change follows WJ24's added bottom-right and top-center duties.
Its final machining removes these six former source screw cutters:

- `clip_horizontal_bottom_right_1_upright_1` through `_upright_3`
- `clip_split_top_center_right_upright_1` through `_upright_3`

WJ24 adds four candidate bores through the principal:
`bottom_center/clip_horizontal_bottom_right_1/principal_1` and `_2`, and
`top_center/clip_split_top_center_right/principal_1` and `_2`. The native
source-cut replay remains a separate check: WJ24 replays source-native cutters
from raw stock to confirm the canonical source-finished members, then its
machining pass applies the 144-axis source-cutter removal set and candidate
bores. The unfiltered source-cut maps in the composition report do not by
themselves say which old axes are removed in the finished candidate host.

The two service rails retain the same source-cut sets and four candidate-bore
axes each, which is consistent with their exact geometric matches. Both WJ04
cleats also remain identical in the WJ24 baseline. The upper cleat retains the
historical 86.9 mm N-direction crosscut and its provisional 2 mm G7 keepout
reserve, as declared by the pinned WJ04 G7 producer.

The WJ24 G7 LED access relief is a separate geometry scenario on
`wj04_lower_full_stock_cleat`. The access-relief producer defines connector-only
variants at 0, 0.5 and 1.0 mm radial clearance and leaves the retained WJ24
composition unchanged. The baseline remains the current WJ24 lower cleat; the
relief variants remain exploratory and require study corrections before they
can become a named mesh input. Those relief shapes are not in this baseline
comparison or its five-body export. If a relief variant is later selected,
replace the lower-cleat solid with that named shape and repeat the STEP
identity and geometry checks. The relief screen does not authorize a cut or
establish a service sequence.

## Mesh reuse boundary

The archived WJ16 mesh remains a mesh-preparation diagnostic for its original
five WJ16 solids. Its four matching body partitions are candidates for
component-mesh reuse after the receiving analysis checks their imported STEP
identity, surface tags and node/element ownership. The five-body deck as a
whole cannot be reused as the WJ24 geometry mesh because its principal still
contains the old cut pattern. No contact identities, material model, loads,
restraints, response or resistance are present in that deck. The historical
mesh worker also pins the old WJ04/WJ16 inventory and exporter, so it rejects a
new WJ24 bundle by design.

The source-bound exporter reads the old mesh report directly from the durable
[attempt-03 evidence archive](../wj04-patch-mesh/attempt-03/complete-mesh-evidence.tar.gz).
It verifies the archive and contents-index hashes, then checks the exact
`mesh.json` member's identity, byte count and SHA-256 against
[bundle-contents.json](../wj04-patch-mesh/attempt-03/bundle-contents.json).
It does not depend on the ignored `fea/generated` copy or extract archive files
to disk.

## Source-bound comparison and export invocation

The prepared helper is preserved as
[prepared-reconciliation-exporter.py.snapshot](prepared-reconciliation-exporter.py.snapshot)
and remains available at
[`scripts/wood_joint_wj24_patch_reconciliation.py`](../../../../scripts/wood_joint_wj24_patch_reconciliation.py).
The parent subsequently ran it once in the serialized WJ16/WJ24 geometry
session. The exact five-body export, execution record, launcher and source/test
snapshots are preserved in [export attempt 01](export-attempt-01/README.md).
Its source-bound reconciliation report has SHA-256
`256af45c2a6b2b48726d86f95e2f4febdd8cad726d690738e9cb1fad87a89711`; the
archive readback verified all seven bundle members and the five STEP
source-to-readback identity checks.

For a reproducible rebuild, in the same serialized Python process that holds
the complete live `g16` and `g24` objects, use:

```python
from scripts import wood_joint_wj24_patch_reconciliation as patch_reconcile

report = patch_reconcile.build_wj24_patch_reconciliation_report(g16, g24)
```

To create a new, non-overwriting five-body STEP bundle for inspection, call
`patch_reconcile.export_wj24_representative_patch(g16, g24, "/tmp/wj24-representative-patch")`.
That helper checks that the live objects match the selected archived WJ16 and
WJ24 reports before it exports. It does not mesh the bodies. The old
`fea.wood_joint_patch_mesh` worker cannot consume the WJ24 export because it
is explicitly pinned to the historical WJ16/WJ04 source bundle.

On a fresh process, WJ12, WJ16 and WJ24 must be rebuilt from one shared right
rail source object before calling the helper. In outline: materialize the
right rail; use that object for WJ12 source-cutter preflight/composition and
left-service materialization; compose WJ16; build top-outer and compose WJ18;
build top-center, bottom-outer (`context_variant="wj18"`) and bottom-center;
then compose WJ24. Do not independently call the WJ12 convenience materializer
and then create left-service geometry: those calls would use different source
objects and fail WJ16's shared-source identity contract. This outline is for
geometry analysis only; it does not authorize physical work or release.

No mesh or native solve was run for this reconciliation/export. It accepts no joint,
access sequence, capacity, fabrication or structural release.
