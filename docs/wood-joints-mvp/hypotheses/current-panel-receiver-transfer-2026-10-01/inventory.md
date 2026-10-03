# Current panel receiver inventory

`inventory.py` joins the saved 66 Hillman 42605 panel and kicker axes to their
current receiver members, one matched finished-timber bore-like patch, the
panel/receiver contact record, and current receiver-to-timber graph edges. It
uses only saved JSON and SHA-256 byte checks; it does not import CadQuery or
regenerate or replay CAD.

`build_report(root=ROOT)` returns `(report, pins)`. `report["axes"]` is sorted by
`axis_id` and uses `axis_id`, `panel_member`, `receiver_member`,
`origin_global_xyz_mm`, and `axis_global_xyz` as its stable join fields. It
retains `previous_receiver_member`, move status and translation, source
inventory provenance, feature and STEP binding, nominal overlap geometry,
panel/receiver contact, timber-neighbor contact edges, and per-axis limits.
`pins["sources"]` lists every direct input and verified transitive source byte
binding as repository-relative path, SHA-256, and size.

The saved joins agree on 66 axis IDs: 58 `source_station_retained` and 8
`moved`. The 22 current panel/receiver pairs contain a finite planar face
contact record. Every axis has one current matched cylindrical patch and one
contact-graph association. The receiver screen’s full-section-equivalent
receiver overlap and the matched patch interval are nominally 45.24375 mm
within a 63.5 mm modeled axis envelope. The source inventory’s 50.8 mm
occupied-length value is retained separately as historical SPAX analysis
provenance. These values describe saved geometry; the output deliberately
labels them as a modeled nominal envelope, not installed screw embedment or
thread engagement.

The four moved center-kicker screws enter `base_post_center_left` or
`base_post_center_right` in the current attempt04 manifest, receiver screen,
feature report, and graph association. Their previous receiver field retains
the `inner_kicker_backer_left/right` names. The source inventory’s
`candidate_finished_receiver_member` field and the older [WJ24 fixed-screw
receiver audit](../../wj24-fixed-screw-receiver-audit.md) retain that historical
backer mapping. The attempt04 center check says no previous backer shapes are
present in the current composition. The inventory uses the current manifest
and matched feature identity for `receiver_member`; it does not use those old
backer fields as current receivers.

Each receiver row also carries direct timber-neighbor edges from the current
contact graph. These are finite geometric contact classifications, not a
supported edge or verified load path. The source inventory records
`receiver_to_frame_path_complete: false`; the graph does not provide force
allocation or acceptance. The current center-post margins and kicker seam
contact likewise do not establish continuous seam support, panel bending
response, or capacity.

## Saved sources

The join reads and checks these direct artifacts and their pin closures:

- [`source-inventory.json`](../../source-inventory.json),
  `wood_joint_source_inventory/v1`: the 66 source screw IDs, source station,
  historical receiver names, 50.8 mm occupied-length proxy, and incomplete
  receiver-to-frame path status.
- [Attempt03 full-frame manifest](../evaluation-resume-2026-09-24/current-full-frame-input-manifest-attempt03/current-full-frame-input-manifest.json),
  `wood_joint_current_full_frame_input_manifest/v2`, and [attempt04
  manifest](../evaluation-resume-2026-09-24/current-full-frame-input-manifest-attempt04/current-full-frame-input-manifest.json),
  `wood_joint_current_full_frame_input_manifest/v3`: attempt04’s preserved
  attempt03 byte pin plus the current axis map and finished member STEP
  bindings.
- [Receiver screen](../evaluation-resume-2026-09-24/receiver-screen-attempt04.json),
  `wood_joint_current_receiver_screen/v1`: current nominal axis/receiver
  intersections, pair contacts, receiver counts, and center-kicker check.
- [Complete contact graph](../evaluation-resume-2026-09-24/complete-contact-graph-attempt02.json),
  `wood_joint_current_contact_graph/v1`: panel-screw pair associations and
  current timber-neighbor contact geometry. All 68 paths in its declared
  `geometry_source_inputs_sha256` map are checked and included in the returned
  source pins.
- [Finished axis-feature register](../current-finished-feature-register-2026-10-01/axis-features.json),
  `wood_joint_axis_finished_feature_register/v1`, together with
  [`axis-source-pins.json`](../current-finished-feature-register-2026-10-01/axis-source-pins.json),
  `wood_joint_axis_source_pins/v1`, and
  [`source-pins.json`](../current-finished-feature-register-2026-10-01/source-pins.json),
  `wood_joint_current_finished_feature_register_source_pins/v1`: current
  receiver feature matches and the finished-surface source closure.

`build_report` verifies the recorded JSON schemas, candidate/revision identity,
the axis ID set and movement counts, attempt03/04 station agreement, source
and current receiver provenance, STEP binding correspondence, one-to-one
screen/feature/graph membership, and the byte closures. The current local build
returns 145 distinct source pins, including all 68 contact-graph geometry
inputs. It only hashes saved source bytes; the feature closure includes exact
STEP inputs but no STEP geometry is opened or regenerated here. A public
checkout without these local saved reports and ignored closure inputs cannot
rebuild this report; it fails with a missing-source error. The synthetic tests
use isolated JSON fixtures and do not depend on the local CAD or ignored
geometry set.

## Limits

This inventory does not establish delivered product conformance, installed
engagement, holes or cuts, pilot/countersink occupancy, panel edge support,
continuous support, a receiver-to-frame load path, force sharing, individual
screw action, screw resistance, stiffness, joint acceptance, or a build or
climbing release. The axis geometry and member contact rows are not physical
inspection evidence.

Run the focused source-only tests with:

```bash
uv run pytest docs/wood-joints-mvp/hypotheses/current-panel-receiver-transfer-2026-10-01/test_inventory.py
uv run ruff check docs/wood-joints-mvp/hypotheses/current-panel-receiver-transfer-2026-10-01/inventory.py docs/wood-joints-mvp/hypotheses/current-panel-receiver-transfer-2026-10-01/test_inventory.py
```
