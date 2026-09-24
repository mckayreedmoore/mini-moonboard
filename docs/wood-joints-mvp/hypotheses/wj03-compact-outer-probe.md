# WJ-03 compact outer-envelope probe

Status: archived v2 geometry comparison. It does not change the active
candidate, source pins, configuration, or manifest. Acceptance is not assessed;
the three layouts remain hypotheses, with no structural, purchase, drilling,
or fabrication release.

## Reproduction and source binding

Run from the repository root:

```sh
uv run python -m scripts.wood_joint_wj03_compact_outer_probe > /tmp/wj03-compact-outer-v2.json
```

The archived report is byte-identical to the preserved v2 output and has
SHA-256 `3c92c825f4b20b81160bdb96c2d38a0a05b9ca0222532ef6a274d3823b61b985`.
The producer script SHA-256 at archive time is
`1b87fffdb250e7e3021f43913bb26d2e0c6f4a3b3f198d31c6bd8b875320065e`; it
matches the producer in the repository revision that introduces this archive.
For reproduction, use that repository revision, verify this producer hash, and
then run the command above. The report schema is
`wood_joint_wj03_compact_outer_probe_collection/v1`.

Each case records the same selected-source authority pin: source commit
`df7f5eca86ae831b35a8bcf9e6dcd7ae8af852bb`; inventory SHA-256
`07af4c3eb642cf3887595fe4415eb65404cdcf74d66c5c7bb182847ef21c2d78`; fixed
screw-axis SHA-256
`22224a0afc78500cb0f832f3b6c6ea4e0d1dd934813c8570d637c16cb052a4f1`; frame
bolt-axis SHA-256
`524792bb6fe1f966a7725aad7a7ed4290c355bebafcc27d84f9a5e2690ad3e27`; and
uncut-part shape SHA-256
`627cead591c1f0f4e63ede07a871659fba7c1b56a8e468791e5dd8f6d9845f2c`. The
report also records runtime-module hashes, the panel-replacement helper hash,
and the six panel-obstacle IDs. All 66 fixed purchased panel-screw envelopes
and 12 starting frame-bolt axes were included. The `source_commit` identifies
the selected source authority; it is not the implementation revision used to
produce the report. These recorded hashes are partial pins, not the complete
transitive producer closure: the report does not self-record its producer hash
and omits implementation inputs such as `wood_joint_frame` and protected-wire
inputs. The repository revision that introduces this archive preserves those
remaining implementation inputs. No active authority is repinned or modified.

This archive preserves the v2 output only. The original v1 report/source was
not archived or verified for exact reproduction, so this note makes no such
claim.

## Comparison

| Hypothesis | Bridge | Bevel limits | Rear projection vs. 139.7 mm ordinary envelope |
| --- | --- | --- | --- |
| `full_bridge_4x6_spine_bevel_137` | 88.9 mm deep | Spine N = 137 mm | 179.982 mm, 40.282 mm beyond |
| `compact_bridge_4x6_spine_bevel_137_7` | 38.1 mm deep | Spine N = 137.7 mm | 141.067 mm, 1.367 mm beyond |
| `compact_bridge_rear_bevel_4x6_spine_137_7` | 38.1 mm deep | Spine and bridge N = 137.7 mm | 137.7 mm, 2 mm reserve |

For each case, the probe reports no intersections with unintended finished
timber, no installed-stack or cross-stack component intersections, no final
panel intersections, and no protected-envelope hits (all 106 tested envelope
entries are empty). Each case has 20 modeled bolt stacks with all 40 head and
nut washer seats fully supported, and six positive contact patches at each
side node. These are geometric results only.

Bolt lengths are provisional; grade, thread length, washer product, supplier,
and catalog fit are unselected. Structural capacity and actual tool access were
not assessed. The report establishes no load-path acceptance, fabrication
readiness, or build suitability.
