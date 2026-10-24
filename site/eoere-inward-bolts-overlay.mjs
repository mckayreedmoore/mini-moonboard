import {sha256} from './wood-joints-overlay.mjs';
import {loadPrincipalPairScene} from './eoere-principal-pair-overlay.mjs';

const require = (ok, message) => {if (!ok) throw new Error('Inward bolts: '+message);};
const ROLES = ['shaft', 'head', 'head_washer', 'nut_washer', 'nut'];
const TOP = [1, 5, 17, 18, 22, 23, 24, 28].map(n => 'eoere_bolt_'+String(n).padStart(3, '0'));
const SIDE = [6, 9, 10, 13, 32, 35, 36, 39, 43, 46, 47, 50, 51, 54, 55, 58, 67, 70, 71, 74]
  .map(n => 'eoere_bolt_'+String(n).padStart(3, '0'));
for (const side of ['left', 'right']) SIDE.push(...[
  'cleat_post_bolt_'+side+'_1', 'cleat_post_bolt_'+side+'_2', 'lumber_leg_bolt_'+side+'_1',
  'rail_front_bolt_'+side+'_1', 'rail_front_bolt_'+side+'_2', 'rail_rear_bolt_'+side+'_1']);
const finiteVector = (value, length) => Array.isArray(value) && value.length === length && value.every(Number.isFinite);
const same = (a, b) => JSON.stringify(a) === JSON.stringify(b);

export function validateInwardBolts(data, layoutSha256) {
  require(data?.schema === 'eoere_inward_bolts_patch/v1' && data.revision === 'eoere-inward-exterior-bolts-v7' &&
    data.key === 'eoere-current-frame-development', 'revision differs');
  require(/^[a-f0-9]{64}$/.test(layoutSha256 || '') && data.layout_report?.sha256 === layoutSha256,
    'receipt differs');
  require(data.parent_scene?.sha256 === '4c3d0d18892cab07dc7d7f485732045f57d22368deb77360dff9eb0d5c2a8917' &&
    data.parent_layout?.sha256 === 'd2849e0bb7e3751396854556fa0bb411d83f3cf94dec55ec157a582f4f5b6e80', 'parent differs');
  require(data.part_count === 1037 && data.counts?.bolt_stacks === 96 && data.counts.spacer_pieces === 32 &&
    data.counts.Hillman_axes === 66 && data.counts.angles === 24, 'inventory differs');
  for (const flag of ['historical_capacity_transferred', 'current_response_computed',
    'complete_conditional_frame_evaluation', 'thread_windows_washer_seats_and_tool_access_requalified',
    'fabrication_released', 'climbing_released']) require(data[flag] === false, 'review boundary differs: '+flag);
  require(data.panel_Hillman_resolution_deferred === true, 'panel deferral differs');
  require(data.transforms?.length === 40 && same(data.transforms.map(r => r.axis_id).sort(), [...TOP, ...SIDE].sort()),
    'all 40 exterior stacks required');
  let pieces = 0;
  for (const row of data.transforms) {
    const top = TOP.includes(row.axis_id), expectedRotation = top ? [[1, 0, 0], [0, -1, 0], [0, 0, -1]] :
      [[-1, 0, 0], [0, -1, 0], [0, 0, 1]];
    require(same(row.rotation_matrix_row_major, expectedRotation) &&
      same(row.rotation_axis_xyz, top ? [1, 0, 0] : [0, 0, 1]), 'complete half-turn required');
    require(finiteVector(row.rotation_center_xyz_mm, 3) && finiteVector(row.translation_xyz_mm, 3),
      'finite rigid transform required');
    for (let i = 0; i < 3; i++)
      require(Math.abs(row.translation_xyz_mm[i] - row.rotation_center_xyz_mm[i] * (1 - expectedRotation[i][i])) < 1e-6,
        'rotation center and translation differ');
    require(row.exterior_face === (top ? 'top' : row.rotation_center_xyz_mm[0] < 0 ? 'left' : 'right'),
      'exterior face differs');
    const spaced = row.axis_id.startsWith('cleat_post_bolt_') ||
      ['eoere_bolt_067', 'eoere_bolt_070', 'eoere_bolt_071', 'eoere_bolt_074'].includes(row.axis_id);
    require(same([...row.roles].sort(), [...ROLES, ...(spaced ? ['spacer', 'spacer_2', 'spacer_3'] : [])].sort()),
      'complete stack including all spacers required');
    pieces += row.roles.length;
  }
  require(pieces === 224, 'hardware census differs');
  return data;
}

export async function loadInwardBoltScene(THREE, options) {
  const response = await fetch(options.url); require(response.ok, 'scene request failed');
  const bytes = await response.arrayBuffer(); require(await sha256(bytes) === options.expectedSha256, 'scene bytes differ');
  const data = validateInwardBolts(JSON.parse(new TextDecoder('utf-8', {fatal: true}).decode(bytes)), options.layoutSha256);
  const parent = await loadPrincipalPairScene(THREE, {...options, url: data.parent_scene.path.split('/').pop(),
    expectedSha256: data.parent_scene.sha256, decodedSha256: data.parent_scene.decoded_sha256,
    layoutSha256: data.parent_layout.sha256});
  const old = new Map(parent.parts.map(p => [p.name, p])), changed = new Map();
  try {
    for (const row of data.transforms) {
      const r = row.rotation_matrix_row_major, t = row.translation_xyz_mm;
      const matrix = new THREE.Matrix4().set(...r[0], t[0], ...r[1], t[1], ...r[2], t[2], 0, 0, 0, 1);
      for (const role of row.roles) {
        const name = row.axis_id+'_'+role, previous = old.get(name);
        require(previous?.geometry && previous.fabrication.connection_name === row.axis_id &&
          previous.fabrication.hardware_role === role, 'parent stack differs: '+name);
        const geometry = previous.geometry.clone().applyMatrix4(matrix);
        geometry.computeBoundingBox(); geometry.computeBoundingSphere();
        const part = {...previous, geometry, fabrication: {...previous.fabrication,
          owner_frame_revision: data.revision, installation_orientation: 'Head exterior; nut and spacers interior',
          head_faces: 'exterior', nut_faces: 'interior', delivered_part_verified: false,
          thread_windows_washer_seats_and_tool_access_requalified: false}};
        delete part.path; changed.set(name, part);
      }
    }
    const parts = parent.parts.map(p => changed.get(p.name) || p);
    require(parts.length === 1037 && changed.size === 224, 'composed census differs');
    for (const part of parent.parts) if (changed.has(part.name)) part.geometry.dispose();
    // Keep the preceding full-registry envelope, extending it only if needed.
    const bounds = parent.bounds_mm.map((row, end) => row.map((value, i) =>
      (end ? Math.max : Math.min)(value, data.bounds_mm[end][i])));
    return {...parent, parts, bounds_mm: bounds, design: {...parent.design, key: data.key, qualified_for_design: false},
      meta: {...parent.meta, revision: data.revision, source_sha256: options.expectedSha256,
        layout_sha256: options.layoutSha256, exterior_stacks_reversed: 40, selected_bolt_stacks: 96,
        current_response_computed: false, conditional_frame_evaluation_complete: false,
        analysis_pass_transferred: false, physical_release: false}};
  } catch (error) {
    for (const part of [...parent.parts, ...changed.values()]) part.geometry?.dispose();
    throw error;
  }
}
