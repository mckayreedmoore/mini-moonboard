import {meshGeometry, sha256, decodeTypedArray} from './wood-joints-overlay.mjs';
import {loadNarrowChannelsBaseScene} from './eoere-narrow-channels-overlay.mjs';

const require = (ok, message) => {if (!ok) throw new Error('Enclosed passages: '+message);};
export function validateEnclosedPassages(data, layoutSha256) {
  require(data?.schema === 'eoere_enclosed_passages_patch/v1' &&
    data.revision === 'eoere-centred-enclosed-passages-v1', 'revision differs');
  require(data.layout_report?.sha256 === layoutSha256 && /^[a-f0-9]{64}$/.test(layoutSha256 || ''), 'receipt differs');
  require(data.key === 'eoere-enclosed-passages-frame-development' && data.part_count === 1033, 'model census differs');
  require(data.parent_layout?.sha256 === '871836782314f30ef4ed7c48dcf6d154927db19a371eea4a0e2bb01264a73932', 'parent differs');
  require(data.new_response_computed === false && data.historical_capacity_transferred === false &&
    Object.keys(data.release || {}).length >= 6 && Object.values(data.release).every(v => v === false), 'acceptance boundary differs');
  require(data.replacements?.length === 40 && new Set(data.replacements.map(r => r.name)).size === 40 &&
    data.replacements.filter(r => r.fabrication.kind === 'timber').length === 8 &&
    data.replacements.filter(r => r.fabrication.kind === 'wire').length === 32 &&
    data.replacements.every(r => r.id === r.name && r.mesh && !r.transform && !r.template_id), 'eight timbers and 32 cables required');
  return data;
}

export async function loadEnclosedPassagesScene(THREE, options) {
  const response = await fetch(options.url); require(response.ok, 'scene request failed');
  const compressed = await response.arrayBuffer(); require(await sha256(compressed) === options.expectedSha256, 'compressed bytes differ');
  const decoded = await new Response(new Blob([compressed]).stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer();
  require(await sha256(decoded) === options.decodedSha256, 'decoded bytes differ');
  const data = validateEnclosedPassages(JSON.parse(new TextDecoder('utf-8', {fatal: true}).decode(decoded)), options.layoutSha256);
  const topologies = new Map();
  for (const [digest, row] of Object.entries(data.triangle_topologies)) {
    const indices = decodeTypedArray(row.triangle_indices_base64, row.triangle_component_type, row.index_count);
    require(await sha256(indices.bytes) === digest, 'triangle bytes differ');
    topologies.set(digest, {...row, indices: indices.values});
  }
  const parent = await loadNarrowChannelsBaseScene(THREE, {...options,
    url: data.parent_scene.path.split('/').pop(), expectedSha256: data.parent_scene.sha256,
    decodedSha256: data.parent_scene.decoded_sha256, layoutSha256: data.parent_layout.sha256});
  const changed = new Map();
  try {
    for (const row of data.replacements) {
      const previous = parent.parts.find(p => p.name === row.name);
      require(previous?.fabrication.kind === row.fabrication.kind, 'missing parent part');
      const geometry = meshGeometry(THREE, row.mesh, topologies); geometry.computeBoundingBox();
      changed.set(row.name, {...previous, geometry, fabrication: {...previous.fabrication, ...row.fabrication}});
    }
    const parts = parent.parts.map(p => changed.get(p.name) || p);
    for (const p of parent.parts) if (changed.has(p.name)) p.geometry?.dispose();
    return {...parent, parts, design: {...parent.design, key: data.key, qualified_for_design: false},
      meta: {...parent.meta, revision: data.revision, source_sha256: options.expectedSha256,
        decoded_sha256: options.decodedSha256, layout_sha256: options.layoutSha256,
        unchanged_geometries_reused: parts.length-40, new_response_computed: false,
        planning_mass_kg: null, analysis_pass_transferred: false, physical_release: false}};
  } catch (error) {
    for (const p of [...parent.parts, ...changed.values()]) p.geometry?.dispose();
    throw error;
  }
}
