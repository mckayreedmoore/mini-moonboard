import assert from 'node:assert/strict';
import {validateOwnerCornerScene} from '../site/owner-corner-overlay.mjs';

const hidden = Array.from({length: 170}, (_, index) => `item_${index}`);
const scene = {
  schema: 'owner_corner_layout_scene/v1',
  status: 'complete_layout_concept_not_qualified',
  baseline: 'compact-floor-flush-kerf-right',
  layout_clearance_approved: false,
  drilling_released: false,
  fabrication_released: false,
  structural_released: false,
  inventory: {
    replaced_angle_duties: 24,
    removed_structural_sds: 144,
    corner_blocks: 24,
    moved_center_posts: 2,
    kicker_screw_backers: 2,
    new_diagnostic_bolt_axes: 92,
    fixed_panel_kicker_screw_axes: 66,
    retained_frame_bolt_axes: 12,
  },
  solids: Array(28).fill({}),
  diagnostic_bolt_axes: Array(92).fill({}),
  hidden_baseline_visual_names: hidden,
};

assert.equal(validateOwnerCornerScene(scene, hidden), scene);
assert.throws(
  () => validateOwnerCornerScene({...scene, structural_released: true}, hidden),
  /inventory or release boundary/,
);
assert.throws(
  () => validateOwnerCornerScene(scene, [...hidden].reverse()),
  /inventory or release boundary/,
);
