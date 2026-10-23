import {meshGeometry, sha256, decodeTypedArray} from './wood-joints-overlay.mjs';
import {loadRetainedFrameScene} from './eoere-retained-frame-overlay.mjs';

const require = (ok, message) => {if (!ok) throw new Error('Owner frame: '+message);};
export function validateOwnerFrame(data, layoutSha256) {
  const moved = data?.revision === 'eoere-local-front-bolt-moves-v4';
  require(data?.schema === 'eoere_owner_requested_frame_patch/v1' &&
    (moved || data.revision === 'eoere-retained-frame-trimmed-three-quarter-v3') &&
    data.key === 'eoere-current-frame-development', 'revision differs');
  require(data.layout_report?.sha256 === layoutSha256 && /^[a-f0-9]{64}$/.test(layoutSha256 || ''), 'receipt differs');
  require(data.parent_layout?.sha256 === (moved ?
    '6c71c75af5abd86cf97173e68b93b7e5c86b2dea6fdd092557137dfee200a3fb' :
    '98fb3d6437d629201e9e60cf6a3068a070f2e1f0574a7364c256c0e8a904f379'), 'parent differs');
  require(data.historical_capacity_transferred === false && data.complete_conditional_frame_evaluation === false &&
    data.fabrication_released === false && data.climbing_released === false &&
    data.panel_Hillman_resolution_deferred === true, 'claim boundary differs');
  require(data.part_count === 1011 && data.counts?.bolt_stacks === 92 && data.counts.angles === 24 &&
    data.counts.sawn_members === 20 && data.counts.plywood_cleats === 4 && data.counts.Hillman_axes === 66, 'inventory differs');
  require(data.replacements?.length === (moved ? 14 : 39) &&
    new Set(data.replacements.map(r => r.name)).size === (moved ? 14 : 39) &&
    data.replacements.filter(r => r.fabrication.kind === 'timber').length === (moved ? 4 : 9) &&
    data.replacements.every(r => r.id === r.name && r.mesh), 'replacement inventory differs');
  require(data.removals?.length === (moved ? 0 : 70) &&
    new Set(data.removals).size === (moved ? 0 : 70), 'removal inventory differs');
  if (moved) {
    const expected = ['left', 'right'].flatMap(side => [
      'base_floor_'+side, 'base_post_outer_'+side,
      ...['shaft', 'head', 'head_washer', 'nut_washer', 'nut'].map(role => 'rail_front_bolt_'+side+'_1_'+role),
    ]).sort();
    require(JSON.stringify(data.replacements.map(r => r.name).sort()) === JSON.stringify(expected), 'local move changes unrelated parts');
  } else for (const side of ['left', 'right']) for (const name of ['outboard_knee_', 'outboard_leg_packer_', 'outboard_knee_angle_'])
    require(data.removals.includes(name+side), 'rejected outboard part retained');
  for (const row of data.replacements.filter(r => r.name.startsWith('eoere_cleat_')))
    require(row.fabrication.nominal_independent_leaf_thickness_mm === 19.05 &&
      row.fabrication.no_glue_friction_or_composite_action_credit === true, 'cleat thickness or composite claim differs');
  return data;
}

export async function loadOwnerFrameScene(THREE, options) {
  const response = await fetch(options.url); require(response.ok, 'scene request failed');
  const compressed = await response.arrayBuffer(); require(await sha256(compressed) === options.expectedSha256, 'compressed bytes differ');
  const decoded = await new Response(new Blob([compressed]).stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer();
  require(await sha256(decoded) === options.decodedSha256, 'decoded bytes differ');
  const data = validateOwnerFrame(JSON.parse(new TextDecoder('utf-8', {fatal: true}).decode(decoded)), options.layoutSha256);
  const moved = data.revision === 'eoere-local-front-bolt-moves-v4';
  const topologies = new Map();
  for (const [digest, row] of Object.entries(data.triangle_topologies)) {
    const indices = decodeTypedArray(row.triangle_indices_base64, row.triangle_component_type, row.index_count);
    require(await sha256(indices.bytes) === digest, 'triangle bytes differ');
    topologies.set(digest, {...row, indices: indices.values});
  }
  const loadParent = moved ? loadOwnerFrameScene : loadRetainedFrameScene;
  const parent = await loadParent(THREE, {...options, url: data.parent_scene.path.split('/').pop(),
    expectedSha256: data.parent_scene.sha256, decodedSha256: data.parent_scene.decoded_sha256,
    layoutSha256: data.parent_layout.sha256});
  const old = new Map(parent.parts.map(p => [p.name, p])), changed = new Map();
  try {
    for (const row of data.replacements) {
      const previous = old.get(row.name) || old.get(row.name.replace(/_spacer_3$/, '_spacer_2'));
      require(previous?.fabrication.kind === row.fabrication.kind, 'part identity differs');
      const geometry = meshGeometry(THREE, row.mesh, topologies); geometry.computeBoundingBox();
      const part = {...previous, name: row.name, geometry, fabrication: {...previous.fabrication, ...row.fabrication}};
      if (row.name.startsWith('eoere_cleat_')) Object.assign(part.fabrication, {
        blank_mm: [609.6, 203.2, 19.05],
        proposed_lamination: 'Two aligned layers per corner; perfect-bond study exceeds the row reference',
        proposed_combined_wood_thickness_mm: 38.1, actual_bond_qualified: false,
      });
      delete part.path;
      changed.set(row.name, part);
    }
    require(data.removals.every(n => old.has(n)), 'removed parent part missing');
    let parts = parent.parts.filter(p => !data.removals.includes(p.name)).map(p => changed.get(p.name) || p);
    for (const [name, part] of changed) if (!old.has(name)) parts.push(part);
    const cleatConnections = new Set(data.replacements.filter(r => !moved && r.fabrication.kind === 'bolt')
      .map(r => r.fabrication.connection_name));
    parts = parts.map(part => cleatConnections.has(part.fabrication.connection_name) ? {...part,
      fabrication: {...part.fabrication, stack_roles: ['shaft', 'head', 'head_washer', 'nut_washer',
        'spacer', 'spacer_2', 'spacer_3', 'nut'], nut_side_spacer_mm: 38.1, spacer_piece_count: 3,
      delivered_part_verified: false}} : part);
    require(parts.length === 1011 && new Set(parts.map(p => p.name)).size === 1011, 'composed census differs');
    require(!parts.some(p => p.name.startsWith('outboard_')), 'rejected assembly remains');
    // Some retained services load their STL later. Use the complete current
    // occupied-registry bounds, not the removed return assembly's envelope.
    const bounds = [[-1343.025, -182.7, -3.183231456205249e-12],
      [1339.8500000000001, 1639.9464830416935, 2246.2903761488838]];
    for (const part of parent.parts) if (changed.has(part.name) || data.removals.includes(part.name)) part.geometry?.dispose();
    return {parts, bounds_mm: bounds, design: {...parent.design, key: data.key, qualified_for_design: false},
      meta: {...parent.meta, revision: data.revision, source_sha256: options.expectedSha256,
        decoded_sha256: options.decodedSha256, layout_sha256: options.layoutSha256,
        selected_bolt_stacks: 92, plywood_cleats: 4, angle_count: 24, Hillman_axes: 66,
        planning_mass_kg: null, bounds_scope: 'Complete current occupied-part registry', conditional_frame_evaluation_complete: false,
        analysis_pass_transferred: false, physical_release: false}};
  } catch (error) {
    for (const part of [...parent.parts, ...changed.values()]) part.geometry?.dispose();
    throw error;
  }
}
