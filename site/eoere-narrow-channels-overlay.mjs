import {meshGeometry, sha256, decodeTypedArray} from './wood-joints-overlay.mjs';
import {loadFrontPostsBaseScene, loadFrontPostsGridScene} from './eoere-front-posts-4x6-overlay.mjs';

const REVISION = 'eoere-narrow-channel-openings-v1';
const NAMES = ['base_principal_center_left', 'base_principal_center_right',
  ...['bottom', 'service_lower', 'service_upper'].flatMap(row => ['left', 'right'].map(side => `base_rail_${row}_${side}`))];
const SHA = /^[a-f0-9]{64}$/;
const require = (ok, message) => {if (!ok) throw new Error('Narrow channels: '+message);};

export function validateNarrowChannels(data, layoutSha256) {
  require(data?.schema === 'eoere_narrow_channels_patch/v1' && data.revision === REVISION, 'revision differs');
  require(SHA.test(layoutSha256 || '') && data.layout_report?.sha256 === layoutSha256 &&
    data.layout_report.path.endsWith('/occupied-narrow-channels-v1.json'), 'receipt differs');
  require(data.parent_scene?.sha256 === '54e081aa13170f32badd4b0142a34f8851dc584268b09c9ea25e01bc89c68b17' &&
    data.parent_layout?.sha256 === '96bb5105b4a193bab5f802d659b1fd057179cdfa90c320489e283414a2331c61', 'post parent differs');
  require(data.profile?.front_width_mm === 14 && data.profile.rear_depth_mm === 14.35 &&
    data.profile.maximum_recorded_harness_diameter_mm === 12.7 && data.profile.actual_fit_or_tolerance_verified === false,
    'measured envelope and unchanged depth required');
  require(data.analysis_pass_transferred === false && Object.keys(data.release || {}).length >= 6 &&
    Object.values(data.release).every(v => v === false), 'unresolved acceptance required');
  for (const [variant, count] of [['base', 1033], ['extra', 1428]]) {
    require(data.counts?.[variant] === count, 'part census differs');
    const rows = data.replacements?.[variant];
    require(Array.isArray(rows) && rows.length === 8 && new Set(rows.map(r => r.name)).size === 8 &&
      rows.every(r => NAMES.includes(r.name) && r.id === r.name && r.mesh && !r.transform && !r.template_id &&
        r.fabrication?.kind === 'timber' && r.fabrication.narrow_channel_revision === REVISION), 'eight timbers required');
  }
  require(data.keys?.base === 'eoere-narrow-channels-frame-development' &&
    data.keys.extra === 'eoere-narrow-channels-grid-development', 'model keys differ');
  return data;
}

async function load(THREE, options, variant) {
  require(SHA.test(options.expectedSha256 || '') && SHA.test(options.decodedSha256 || ''), 'hashes required');
  const response = await fetch(options.url); require(response.ok, 'scene request failed');
  const encoded = await response.arrayBuffer(); require(await sha256(encoded) === options.expectedSha256, 'compressed bytes differ');
  const decoded = await new Response(new Blob([encoded]).stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer();
  require(await sha256(decoded) === options.decodedSha256, 'decoded bytes differ');
  const data = validateNarrowChannels(JSON.parse(new TextDecoder('utf-8', {fatal: true}).decode(decoded)), options.layoutSha256);
  const topologies = new Map();
  for (const [digest, row] of Object.entries(data.triangle_topologies)) {
    const indices = decodeTypedArray(row.triangle_indices_base64, row.triangle_component_type, row.index_count);
    require(await sha256(indices.bytes) === digest, 'triangle bytes differ');
    topologies.set(digest, {...row, indices: indices.values});
  }
  const parent = await (variant === 'base' ? loadFrontPostsBaseScene : loadFrontPostsGridScene)(THREE,
    {...options, url: data.parent_scene.path.split('/').pop(), expectedSha256: data.parent_scene.sha256,
      decodedSha256: data.parent_scene.decoded_sha256, layoutSha256: data.parent_layout.sha256});
  const changed = new Map();
  try {
    for (const row of data.replacements[variant]) {
      const geometry = meshGeometry(THREE, row.mesh, topologies); geometry.computeBoundingBox();
      const previous = parent.parts.find(p => p.name === row.name);
      require(previous?.fabrication.kind === 'timber', 'missing parent timber');
      changed.set(row.name, {...previous, geometry, fabrication: {...previous.fabrication, ...row.fabrication}});
    }
    const parts = parent.parts.map(p => changed.get(p.name) || p);
    require(parts.length === data.counts[variant], 'assembled census differs');
    for (const p of parent.parts) if (changed.has(p.name)) p.geometry?.dispose();
    return {...parent, parts, design: {...parent.design, key: data.keys[variant], qualified_for_design: false},
      meta: {...parent.meta, revision: REVISION, source_sha256: options.expectedSha256, decoded_sha256: options.decodedSha256,
        layout_sha256: options.layoutSha256, unchanged_geometries_reused: parts.length-8,
        new_response_computed: false, analysis_pass_transferred: false, physical_release: false}};
  } catch (error) {
    for (const p of [...parent.parts, ...changed.values()]) p.geometry?.dispose();
    throw error;
  }
}

export const loadNarrowChannelsBaseScene = (THREE, options) => load(THREE, options, 'base');
export const loadNarrowChannelsGridScene = (THREE, options) => load(THREE, options, 'extra');
