import {meshGeometry, sha256, decodeTypedArray} from './wood-joints-overlay.mjs';
import {loadPairedFrameScene} from './eoere-paired-frame-overlay.mjs';

const require = (ok, message) => {if (!ok) throw new Error('Retained 2×6 frame: '+message);};

export function validateRetainedFrame(data, layoutSha256) {
  require(data?.schema === 'eoere_retained_2x6_frame_patch/v1' &&
    data.revision === 'eoere-paired-frame-retained-2x6-A574-v2', 'revision differs');
  require(data.key === 'eoere-retained-2x6-frame-development' && data.part_count === 1075, 'model census differs');
  require(data.layout_report?.sha256 === layoutSha256 && /^[a-f0-9]{64}$/.test(layoutSha256 || ''), 'receipt differs');
  require(data.parent_layout?.sha256 === 'a9fe79843ac96aa9e0ad7ddcba5b532105680f7323baed72f9a620e3765cc0dc', 'parent differs');
  require(data.historical_capacity_transferred === false && data.fabrication_released === false &&
    data.climbing_released === false && data.panel_Hillman_resolution_deferred === true, 'claim boundary differs');
  const rows = data.replacements;
  require(rows?.length === 34 && new Set(rows.map(r => r.name)).size === 34, 'replacement census differs');
  for (const [kind, count] of [['timber', 8], ['bolt', 26]])
    require(rows.filter(r => r.fabrication.kind === kind).length === count, `${kind} census differs`);
  require(rows.every(r => r.id === r.name && r.mesh && !r.transform && !r.template_id &&
    r.fabrication.dimensions_mm?.length === 3 && r.fabrication.dimensions_mm.every(v => Number.isFinite(v) && v > 0)), 'inspection geometry missing');
  const omitted = ['eoere_bolt_068', 'eoere_bolt_069', 'outboard_angle_left_eoere_bolt_006', 'outboard_angle_right_eoere_bolt_009'];
  const removals = omitted.flatMap(id => ['shaft', 'head', 'head_washer', 'nut_washer', 'nut',
    ...(id.startsWith('outboard_') ? ['spacer'] : [])].map(role => id+'_'+role));
  require(data.removals?.length === 22 && removals.every(id => data.removals.includes(id)) &&
    !rows.some(r => data.removals.includes(r.name)), 'removed stacks differ');
  return data;
}

export async function loadRetainedFrameScene(THREE, options) {
  const response = await fetch(options.url); require(response.ok, 'scene request failed');
  const compressed = await response.arrayBuffer(); require(await sha256(compressed) === options.expectedSha256, 'compressed bytes differ');
  const decoded = await new Response(new Blob([compressed]).stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer();
  require(await sha256(decoded) === options.decodedSha256, 'decoded bytes differ');
  const data = validateRetainedFrame(JSON.parse(new TextDecoder('utf-8', {fatal: true}).decode(decoded)), options.layoutSha256);
  const topologies = new Map();
  for (const [digest, row] of Object.entries(data.triangle_topologies)) {
    const indices = decodeTypedArray(row.triangle_indices_base64, row.triangle_component_type, row.index_count);
    require(await sha256(indices.bytes) === digest, 'triangle bytes differ');
    topologies.set(digest, {...row, indices: indices.values});
  }
  const parent = await loadPairedFrameScene(THREE, {...options,
    url: data.parent_scene.path.split('/').pop(), expectedSha256: data.parent_scene.sha256,
    decodedSha256: data.parent_scene.decoded_sha256, layoutSha256: data.parent_layout.sha256});
  const old = new Map(parent.parts.map(p => [p.name, p]));
  const changed = new Map();
  try {
    for (const row of data.replacements) {
      const previous = old.get(row.name);
      require(previous?.fabrication.kind === row.fabrication.kind, 'part identity differs');
      const geometry = meshGeometry(THREE, row.mesh, topologies); geometry.computeBoundingBox();
      const part = {...previous, geometry, fabrication: {...previous.fabrication, ...row.fabrication}};
      delete part.path;
      changed.set(row.name, part);
    }
    require(data.removals.every(name => old.has(name)), 'removed parent stack missing');
    const parts = parent.parts.filter(p => !data.removals.includes(p.name)).map(p => changed.get(p.name) || p);
    require(parts.length === 1075 && new Set(parts.map(p => p.name)).size === 1075 &&
      parts.filter(p => p.fabrication.kind === 'bracket').length === 26 &&
      parts.filter(p => p.fabrication.kind === 'bolt').length === 544, 'composed census differs');
    const bounds = parent.bounds_mm.map(p => [...p]);
    for (const part of changed.values()) for (const [i, axis] of ['x', 'y', 'z'].entries()) {
      bounds[0][i] = Math.min(bounds[0][i], part.geometry.boundingBox.min[axis]);
      bounds[1][i] = Math.max(bounds[1][i], part.geometry.boundingBox.max[axis]);
    }
    for (const part of parent.parts) if (changed.has(part.name) || data.removals.includes(part.name)) part.geometry.dispose();
    return {parts, bounds_mm: bounds, design: {...parent.design, key: data.key, qualified_for_design: false},
      meta: {...parent.meta, revision: data.revision, source_sha256: options.expectedSha256,
        decoded_sha256: options.decodedSha256, layout_sha256: options.layoutSha256,
        selected_bolt_stacks: 102, plywood_cleats: 4, angle_count: 26, Hillman_axes: 66,
        planning_mass_kg: null, analysis_pass_transferred: false, physical_release: false}};
  } catch (error) {
    for (const part of [...parent.parts, ...changed.values()]) part.geometry?.dispose();
    throw error;
  }
}
