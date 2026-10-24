import {meshGeometry, sha256, decodeTypedArray} from './wood-joints-overlay.mjs';
import {loadInwardBoltScene} from './eoere-inward-bolts-overlay.mjs';

const require = (ok, message) => {if (!ok) throw new Error('Inset angles: '+message);};
const same = (a, b) => JSON.stringify(a) === JSON.stringify(b);
const TIMBERS = ['base_header', 'base_side_left', 'base_side_right', 'base_principal_center_left',
  'base_principal_center_right', 'base_post_outer_left', 'base_post_outer_right', 'base_post_center_left',
  'base_post_center_right', 'eoere_cleat_left', 'eoere_cleat_right', 'eoere_cleat_left_outer', 'eoere_cleat_right_outer'];
const ANGLES = ['eoere_clip_angle_base_left', 'eoere_clip_angle_base_right', 'eoere_clip_split_base_center_left',
  'eoere_clip_split_base_center_right', 'eoere_clip_header_outer_under_left', 'eoere_clip_header_outer_under_right',
  'eoere_clip_split_header_center_left', 'eoere_clip_split_header_center_right'];
const AXES = Array.from({length: 20}, (_, i) => 'eoere_bolt_'+String(i+65).padStart(3, '0'));
for (const side of ['left', 'right']) for (const n of [1, 2]) AXES.push('cleat_post_bolt_'+side+'_'+n);

export function validateInwardAngles(data, layoutSha256) {
  require(data?.schema === 'eoere_inward_angles_patch/v1' && data.revision === 'eoere-inward-bolts-and-angles-v8' &&
    data.key === 'eoere-current-frame-development', 'revision differs');
  require(/^[a-f0-9]{64}$/.test(layoutSha256 || '') && data.layout_report?.sha256 === layoutSha256, 'receipt differs');
  require(data.parent_scene?.sha256 === 'e95358fdf897ae1cdeb73370b13418d97339259f709a0c9dbe0bafa17656c9a8' &&
    data.parent_layout?.sha256 === 'ad1dd8f59afc0ec70eaa48d25cd4a59f771f40ca1ceea55c2eadf5868b3ca23e', 'inward-bolt parent differs');
  require(data.part_count === 1037 && data.counts?.bolt_stacks === 96 && data.counts.Hillman_axes === 66 &&
    data.counts.angles === 24 && data.counts.spacer_pieces === 32, 'inventory differs');
  for (const flag of ['current_response_computed', 'historical_capacity_transferred',
    'complete_conditional_frame_evaluation', 'fabrication_released', 'climbing_released'])
    require(data[flag] === false, 'review boundary differs: '+flag);
  require(data.panel_Hillman_resolution_deferred === true && data.removals?.length === 0, 'scope differs');
  require(data.replacements?.length === 13 && same(data.replacements.map(r => r.name).sort(), [...TIMBERS].sort()),
    'all thirteen receivers required');
  for (const row of data.replacements)
    require(row.id === row.name && row.fabrication.kind === 'timber' && row.mesh, 'receiver identity or mesh differs');
  require(data.translations?.length === 160 && new Set(data.translations.map(r => r.name)).size === 160,
    'all translated hardware and fittings required');
  require(same(data.translations.filter(r => r.kind === 'angle').map(r => r.name).sort(), [...ANGLES].sort()),
    'eight connected angles required');
  const stacks = new Map();
  for (const row of data.translations) {
    require(same(row.translation_xyz_mm, [0, 6, 0]), 'only six millimetres inward required');
    if (row.kind === 'angle') continue;
    require(row.kind === 'bolt' && AXES.includes(row.axis_id) && row.name.startsWith(row.axis_id+'_'), 'foreign hardware');
    if (!stacks.has(row.axis_id)) stacks.set(row.axis_id, []);
    stacks.get(row.axis_id).push(row.name.slice(row.axis_id.length+1));
  }
  require(same([...stacks.keys()].sort(), [...AXES].sort()), 'twenty-four shared stacks required');
  for (const [axis, roles] of stacks) {
    const spaced = axis.startsWith('cleat_post_bolt_') || ['eoere_bolt_067', 'eoere_bolt_070', 'eoere_bolt_071', 'eoere_bolt_074'].includes(axis);
    const singleSpacer = [65, 66, 79, 80, 81, 82, 83, 84].some(n => axis === 'eoere_bolt_'+String(n).padStart(3, '0'));
    require(same(roles.sort(), ['shaft', 'head', 'head_washer', 'nut_washer', 'nut',
      ...(spaced ? ['spacer', 'spacer_2', 'spacer_3'] : singleSpacer ? ['spacer'] : [])].sort()),
      'all washers, spacers and nut must move together: '+axis);
  }
  return data;
}

export async function loadInwardAngleScene(THREE, options) {
  const response = await fetch(options.url); require(response.ok, 'scene request failed');
  const compressed = await response.arrayBuffer(); require(await sha256(compressed) === options.expectedSha256, 'compressed bytes differ');
  const decoded = await new Response(new Blob([compressed]).stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer();
  require(await sha256(decoded) === options.decodedSha256, 'decoded bytes differ');
  const data = validateInwardAngles(JSON.parse(new TextDecoder('utf-8', {fatal: true}).decode(decoded)), options.layoutSha256);
  const topologies = new Map();
  for (const [digest, row] of Object.entries(data.triangle_topologies)) {
    const indices = decodeTypedArray(row.triangle_indices_base64, row.triangle_component_type, row.index_count);
    require(await sha256(indices.bytes) === digest, 'triangle bytes differ');
    topologies.set(digest, {...row, indices: indices.values});
  }
  const parent = await loadInwardBoltScene(THREE, {...options, url: data.parent_scene.path.split('/').pop(),
    expectedSha256: data.parent_scene.sha256, layoutSha256: data.parent_layout.sha256});
  const old = new Map(parent.parts.map(p => [p.name, p])), changed = new Map();
  try {
    for (const row of data.replacements) {
      const previous = old.get(row.name);require(previous?.fabrication.kind === 'timber', 'parent receiver differs');
      const geometry = meshGeometry(THREE, row.mesh, topologies); geometry.computeBoundingBox();
      const part = {...previous, geometry, fabrication: {...previous.fabrication, ...row.fabrication}};
      delete part.path;changed.set(row.name, part);
    }
    for (const row of data.translations) {
      const previous = old.get(row.name);
      const kind = row.kind === 'angle' ? 'bracket' : row.kind;
      require(previous?.geometry && previous.fabrication.kind === kind, 'parent hardware differs: '+row.name);
      const geometry = previous.geometry.clone().translate(...row.translation_xyz_mm);geometry.computeBoundingBox();geometry.computeBoundingSphere();
      const part = {...previous, geometry, fabrication: {...previous.fabrication, owner_frame_revision: data.revision,
        inset_angle_translation_xyz_mm: row.translation_xyz_mm, delivered_part_verified: false}};
      delete part.path;changed.set(row.name, part);
    }
    const parts = parent.parts.map(p => changed.get(p.name) || p);
    require(parts.length === 1037 && changed.size === 173, 'composed census differs');
    for (const part of parent.parts) if (changed.has(part.name)) part.geometry.dispose();
    return {...parent, parts, design: {...parent.design, key: data.key, qualified_for_design: false},
      meta: {...parent.meta, revision: data.revision, source_sha256: options.expectedSha256,
        decoded_sha256: options.decodedSha256, layout_sha256: options.layoutSha256,
        retained_inward_exterior_stacks: 40, inset_angles: 8, moved_shared_axes: 24,
        current_response_computed: false, analysis_pass_transferred: false, physical_release: false}};
  } catch (error) {
    for (const part of [...parent.parts, ...changed.values()]) part.geometry?.dispose();
    throw error;
  }
}
