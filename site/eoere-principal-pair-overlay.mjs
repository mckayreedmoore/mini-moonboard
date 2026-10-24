import {meshGeometry, sha256, decodeTypedArray} from './wood-joints-overlay.mjs';
import {loadReferenceCleatScene} from './eoere-reference-cleat-overlay.mjs';

const require = (ok, message) => {if (!ok) throw new Error('Principal pairs: '+message);};
const ROLES = ['shaft', 'head', 'head_washer', 'nut_washer', 'nut'];
export function validatePrincipalPairs(data, layoutSha256) {
  require(data?.schema === 'eoere_principal_pair_patch/v1' &&
    data.revision === 'eoere-flat-cleats-principal-upper-pairs-v6' &&
    data.key === 'eoere-current-frame-development', 'revision differs');
  require(/^[a-f0-9]{64}$/.test(layoutSha256 || '') && data.layout_report?.sha256 === layoutSha256, 'receipt differs');
  require(data.parent_layout?.sha256 === 'd48d48a6b2c9b0d11e535f78ffd66102dc3ec1f0b67476de5e17c27252379898' &&
    data.parent_scene?.sha256 === 'f3ee9ff3f8f0ef63a2ebe9dc1999ba85526cac6775bc0f8b1e06768cd18b731e', 'parent differs');
  for (const key of ['historical_capacity_transferred', 'current_response_computed',
    'complete_conditional_frame_evaluation', 'upper_pair_eligible', 'fabrication_released', 'climbing_released'])
    require(data[key] === false, 'review boundary differs: '+key);
  require(data.panel_Hillman_resolution_deferred === true && data.part_count === 1037 &&
    data.counts?.bolt_stacks === 96 && data.counts.Hillman_axes === 66 && data.counts.angles === 24,
    'inventory differs');
  const expected = ['base_principal_center_left', 'base_principal_center_right',
    ...['eoere_bolt_068', 'eoere_bolt_069'].flatMap(axis => ROLES.map(role => axis+'_'+role))];
  require(data.replacements?.length === 12 && new Set(data.replacements.map(r => r.name)).size === 12 &&
    JSON.stringify(data.replacements.map(r => r.name).sort()) === JSON.stringify(expected.sort()),
    'two receivers and complete center stacks required');
  require(data.removals?.length === 0 && data.flat_cleat_outline_yz_mm?.length === 4,
    'straight four-sided cleats required');
  for (const row of data.replacements) {
    require(row.id === row.name && row.mesh, 'part identity or mesh missing');
    if (row.name.startsWith('eoere_bolt_')) {
      const axis = row.name.startsWith('eoere_bolt_068_') ? 'eoere_bolt_068' : 'eoere_bolt_069';
      require(row.fabrication.kind === 'bolt' && row.fabrication.connection_name === axis &&
        row.fabrication.hardware_role === row.name.slice(axis.length+1) &&
        JSON.stringify(row.fabrication.stack_roles) === JSON.stringify(ROLES) && row.copy_metadata_from,
        'center stack metadata differs');
    } else require(row.fabrication.kind === 'timber', 'receiver kind differs');
  }
  return data;
}

export async function loadPrincipalPairScene(THREE, options) {
  const response = await fetch(options.url); require(response.ok, 'scene request failed');
  const compressed = await response.arrayBuffer(); require(await sha256(compressed) === options.expectedSha256, 'compressed bytes differ');
  const decoded = await new Response(new Blob([compressed]).stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer();
  require(await sha256(decoded) === options.decodedSha256, 'decoded bytes differ');
  const data = validatePrincipalPairs(JSON.parse(new TextDecoder('utf-8', {fatal: true}).decode(decoded)), options.layoutSha256);
  const topologies = new Map();
  for (const [digest, row] of Object.entries(data.triangle_topologies)) {
    const indices = decodeTypedArray(row.triangle_indices_base64, row.triangle_component_type, row.index_count);
    require(await sha256(indices.bytes) === digest, 'triangle bytes differ');
    topologies.set(digest, {...row, indices: indices.values});
  }
  const parent = await loadReferenceCleatScene(THREE, {...options, url: data.parent_scene.path.split('/').pop(),
    expectedSha256: data.parent_scene.sha256, decodedSha256: data.parent_scene.decoded_sha256,
    layoutSha256: data.parent_layout.sha256});
  const old = new Map(parent.parts.map(p => [p.name, p])), changed = new Map();
  try {
    for (const row of data.replacements) {
      const previous = old.get(row.name) || old.get(row.copy_metadata_from);
      require(previous?.fabrication.kind === row.fabrication.kind, 'parent part differs');
      const geometry = meshGeometry(THREE, row.mesh, topologies); geometry.computeBoundingBox();
      const part = {...previous, name: row.name, geometry, fabrication: {...previous.fabrication, ...row.fabrication}};
      delete part.path; changed.set(row.name, part);
    }
    const parts = parent.parts.map(p => changed.get(p.name) || p);
    for (const [name, part] of changed) if (!old.has(name)) parts.push(part);
    require(parts.length === 1037 && new Set(parts.map(p => p.name)).size === 1037, 'composed census differs');
    for (const part of parent.parts) if (changed.has(part.name)) part.geometry?.dispose();
    return {...parent, parts, design: {...parent.design, key: data.key, qualified_for_design: false},
      meta: {...parent.meta, revision: data.revision, source_sha256: options.expectedSha256,
        decoded_sha256: options.decodedSha256, layout_sha256: options.layoutSha256,
        selected_bolt_stacks: 96, principal_header_upper_bolts_per_side: 2,
        flat_cleat_sides: true, current_response_computed: false, upper_pair_eligible: false}};
  } catch (error) {
    for (const part of [...parent.parts, ...changed.values()]) part.geometry?.dispose();
    throw error;
  }
}
