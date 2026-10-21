import {meshGeometry, sha256, decodeTypedArray} from './wood-joints-overlay.mjs';
import {loadEnclosedPassagesScene} from './eoere-enclosed-passages-overlay.mjs';

const require = (ok, message) => {if (!ok) throw new Error('Leg/header revision: '+message);};
export function validateLegHeader(data, layoutSha256) {
  require(data?.schema === 'eoere_leg_header_patch/v3' &&
    data.revision === 'eoere-single-leg-bolts-header-angles-v3', 'revision differs');
  require(data.layout_report?.sha256 === layoutSha256 && /^[a-f0-9]{64}$/.test(layoutSha256 || ''), 'receipt differs');
  require(data.key === 'eoere-leg-header-frame-development' && data.part_count === 1027, 'model census differs');
  require(data.parent_layout?.sha256 === '712416189f209322c10acf4af3b16ac97f91b8ca4f2da415972a0033e4ce1e7d', 'parent differs');
  require(data.historical_capacity_transferred === false && Object.keys(data.release || {}).length >= 6 &&
    Object.values(data.release).every(v => v === false), 'acceptance boundary differs');
  require(data.replacements?.length === 92 && new Set(data.replacements.map(r => r.name)).size === 92 &&
    data.replacements.filter(r => r.fabrication.kind === 'timber').length === 10 &&
    data.replacements.filter(r => r.fabrication.kind === 'bracket').length === 2 &&
    data.replacements.filter(r => r.fabrication.kind === 'bolt').length === 80 &&
    data.replacements.every(r => r.id === r.name && r.mesh && !r.transform && !r.template_id), 'changed geometry census differs');
  require(data.replacements.every(r => r.fabrication.dimensions_mm?.length === 3 &&
    r.fabrication.dimensions_mm.every(v => Number.isFinite(v) && v > 0)), 'inspection dimensions required');
  require(data.replacements.filter(r => r.fabrication.kind === 'bolt').every(r =>
    r.fabrication.connection_name && r.fabrication.stack_roles?.includes(r.fabrication.hardware_role)), 'complete bolt inspection metadata required');
  const axes = ['lumber_leg_bolt_left_2', 'lumber_leg_bolt_right_2', 'rail_rear_bolt_left_2', 'rail_rear_bolt_right_2'];
  const expected = axes.flatMap(a => ['shaft', 'head', 'head_washer', 'nut_washer', 'nut'].map(role => a+'_'+role));
  require(data.removals?.length === 20 && expected.every(name => data.removals.includes(name)) &&
    !data.replacements.some(r => data.removals.includes(r.name)), 'four removed leg stacks required');
  return data;
}

export async function loadLegHeaderScene(THREE, options) {
  const response = await fetch(options.url); require(response.ok, 'scene request failed');
  const compressed = await response.arrayBuffer(); require(await sha256(compressed) === options.expectedSha256, 'compressed bytes differ');
  const decoded = await new Response(new Blob([compressed]).stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer();
  require(await sha256(decoded) === options.decodedSha256, 'decoded bytes differ');
  const data = validateLegHeader(JSON.parse(new TextDecoder('utf-8', {fatal: true}).decode(decoded)), options.layoutSha256);
  const topologies = new Map();
  for (const [digest, row] of Object.entries(data.triangle_topologies)) {
    const indices = decodeTypedArray(row.triangle_indices_base64, row.triangle_component_type, row.index_count);
    require(await sha256(indices.bytes) === digest, 'triangle bytes differ');
    topologies.set(digest, {...row, indices: indices.values});
  }
  const parent = await loadEnclosedPassagesScene(THREE, {...options,
    url: data.parent_scene.path.split('/').pop(), expectedSha256: data.parent_scene.sha256,
    decodedSha256: data.parent_scene.decoded_sha256, layoutSha256: data.parent_layout.sha256});
  const old = new Map(parent.parts.map(p => [p.name, p]));
  const changed = new Map();
  try {
    for (const row of data.replacements) {
      const previous = old.get(row.name);
      require(!previous || previous.fabrication.kind === row.fabrication.kind, 'parent part kind differs');
      const geometry = meshGeometry(THREE, row.mesh, topologies); geometry.computeBoundingBox();
      const part = {...previous, name: row.name, geometry, fabrication: {...previous?.fabrication, ...row.fabrication}};
      delete part.path;
      changed.set(row.name, part);
    }
    require(data.removals.every(name => old.has(name)), 'removed parent stack missing');
    const parts = [...parent.parts.filter(p => !data.removals.includes(p.name)).map(p => changed.get(p.name) || p),
      ...[...changed.values()].filter(p => !old.has(p.name))];
    require(parts.length === 1027 && new Set(parts.map(p => p.name)).size === 1027 &&
      parts.filter(p => p.fabrication.kind === 'bracket').length === 24 &&
      parts.filter(p => p.fabrication.kind === 'bolt').length === 504, 'composed part census differs');
    const bounds = parent.bounds_mm.map(point => [...point]);
    for (const part of changed.values()) for (const [i, axis] of ['x', 'y', 'z'].entries()) {
      bounds[0][i] = Math.min(bounds[0][i], part.geometry.boundingBox.min[axis]);
      bounds[1][i] = Math.max(bounds[1][i], part.geometry.boundingBox.max[axis]);
    }
    for (const part of parent.parts) if (changed.has(part.name) || data.removals.includes(part.name)) part.geometry?.dispose();
    return {...parent, parts, bounds_mm: bounds, design: {...parent.design, key: data.key, qualified_for_design: false},
      meta: {...parent.meta, revision: data.revision, source_sha256: options.expectedSha256,
        decoded_sha256: options.decodedSha256, layout_sha256: options.layoutSha256,
        selected_bolt_stacks: 96, plywood_cleats: 2, angle_count: 24, Hillman_axes: 66,
        planning_mass_kg: null, analysis_pass_transferred: false, physical_release: false}};
  } catch (error) {
    for (const part of [...parent.parts, ...changed.values()]) part.geometry?.dispose();
    throw error;
  }
}
