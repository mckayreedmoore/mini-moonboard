import {meshGeometry, sha256, decodeTypedArray} from './wood-joints-overlay.mjs';
import {loadExtendedCleatBaseScene, loadExtendedCleat2026Scene} from './eoere-cleat-extension-overlay.mjs';

const REVISION = 'eoere-uniform-small-service-channels-v1';
const SHA = /^[0-9a-f]{64}$/;
const PARENT = Object.freeze({url: 'eoere-cleat-extension-scene.json.gz',
  sha256: 'ae6315463f0482597075a769ad3ee55630b4c8b430c2ae93137c5232cc6dbb54',
  decoded_sha256: '6c39b4a240f8033491bbd43c437d60dc888c524e90b350e53351eaf28ddc5db6',
  layout_sha256: '01ba30abe20c2efec136374b8d9a74a098a19929be3cc784b5ebcf7608e62a2d'});
const F_LINKS = Array.from({length: 11}, (_, i) => `wire_${String(61 + i).padStart(3, '0')}_F${12 - i}_F${11 - i}`);
const WOOD = ['base_header', 'base_principal_center_left', 'base_principal_center_right',
  ...['bottom', 'service_lower', 'service_upper'].flatMap(row => ['left', 'right'].map(side => `base_rail_${row}_${side}`))];
function require(ok, message) {if (!ok) throw new Error(`Uniform cable channels: ${message}`);}

export function validateUniformChannels(data, layoutSha256) {
  require(data?.schema === 'eoere_uniform_service_channels_patch/v1' && data.revision === REVISION &&
    data.candidate === 'compact-floor-flush-eoere-bolted-development' && data.status === 'REVISE_UNEVALUATED_GEOMETRY', 'geometry identity differs');
  require(SHA.test(layoutSha256 || '') && data.layout_report?.sha256 === layoutSha256 &&
    data.layout_report.path === 'docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/occupied-uniform-channels-v1.json', 'geometry binding required');
  require(Object.entries(PARENT).every(([key, value]) => data.parent_scene?.[key] === value), 'frozen parent differs');
  require(data.base_geometry_unchanged === false && data.optional_grid_unofficial === true &&
    data.mechanics_ready === false && data.analysis_pass_transferred === false &&
    data.release && Object.keys(data.release).length >= 6 && Object.values(data.release).every(value => value === false), 'revision and release boundaries required');
  const profile = data.smaller_profile;
  require(profile?.wire_clearance_radius_mm === 6.35 && profile.channel_center_N_mm === 8 &&
    Math.abs(profile.front_width_mm - 2 * Math.hypot(8, 6.35)) < 1e-9 && profile.rear_depth_mm === 14.35 &&
    profile.revised_vertical_cable_N_mm === 8 && profile.original_horizontal_cable_N_mm === 8 &&
    profile.extra_horizontal_cable_N_mm === 12.2 && profile.modeled_cable_diameter_mm === 4 &&
    profile.machining_tolerance_or_bit_selected === false, 'smaller common profile required');
  for (const [variant, total, lights, nuts, wires] of [['base', 1021, 132, 142, 131], ['extra', 1380, 252, 262, 250]]) {
    const counts = data.counts?.[variant];
    require(counts?.total_visible_parts === total && counts.timber === 22 && counts.panel === 6 &&
      counts.bracket === 22 && counts.bolt === 500 && counts.physical_bolt_axes === 100 && counts.screw === 66 &&
      counts.lights === lights && counts.tnuts === nuts && counts.wire === wires, `${variant} census differs`);
  }
  function validRows(rows, count) {
    require(Array.isArray(rows) && rows.length === count && new Set(rows.map(row => row.name)).size === count &&
      rows.every(row => row.id === row.name && row.mesh && !row.transform && !row.template_id &&
        SHA.test(row.source_brep_sha256 || '') && row.fabrication?.uniform_channel_revision === REVISION), 'replacement inventory differs');
  }
  validRows(data.common_replacements, 11); validRows(data.base_replacements, 1); validRows(data.extra_replacements, 138);
  require(data.common_replacements.every(row => F_LINKS.includes(row.name) && row.fabrication.kind === 'wire'), 'F-column links differ');
  require(data.base_replacements[0].name === 'base_principal_center_right' &&
    data.base_replacements[0].fabrication.kind === 'timber', 'restored principal required');
  require(data.extra_replacements.filter(row => row.fabrication.kind === 'timber').length === 9 &&
    WOOD.every(name => data.extra_replacements.some(row => row.name === name && row.fabrication.kind === 'timber')) &&
    data.extra_replacements.filter(row => row.fabrication.kind === 'wire' && row.name.startsWith('wire_2026_')).length === 119 &&
    data.extra_replacements.filter(row => row.fabrication.kind === 'wire' && !row.name.startsWith('wire_2026_')).length === 10 &&
    data.extra_replacements.every(row => !F_LINKS.includes(row.name)), 'extra-grid replacement families differ');
  return data;
}

export function loadUniformChannelBaseScene(THREE, options) {return loadScene(THREE, options, 'base');}
export function loadUniformChannel2026Scene(THREE, options) {return loadScene(THREE, options, 'extra');}

async function loadScene(THREE, options, variant) {
  require(SHA.test(options.expectedSha256 || '') && SHA.test(options.decodedSha256 || ''), 'scene hashes required');
  const response = await fetch(options.url); require(response.ok, `scene request failed (${response.status})`);
  const encoded = await response.arrayBuffer(); require(await sha256(encoded) === options.expectedSha256, 'compressed bytes differ');
  const decoded = await new Response(new Blob([encoded]).stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer();
  require(await sha256(decoded) === options.decodedSha256, 'decoded bytes differ');
  const data = validateUniformChannels(JSON.parse(new TextDecoder('utf-8', {fatal: true}).decode(decoded)), options.layoutSha256);
  const topologies = new Map();
  for (const [digest, row] of Object.entries(data.triangle_topologies)) {
    require(SHA.test(digest) && ['uint16', 'uint32'].includes(row.triangle_component_type) &&
      Number.isInteger(row.triangle_count) && row.triangle_count > 0 && row.index_count === row.triangle_count * 3, 'invalid triangle topology');
    const indices = decodeTypedArray(row.triangle_indices_base64, row.triangle_component_type, row.index_count);
    require(await sha256(indices.bytes) === digest, 'triangle bytes differ');
    topologies.set(digest, {...row, indices: indices.values});
  }
  const parent = await (variant === 'base' ? loadExtendedCleatBaseScene : loadExtendedCleat2026Scene)(THREE,
    {...options, url: PARENT.url, expectedSha256: PARENT.sha256, decodedSha256: PARENT.decoded_sha256, layoutSha256: PARENT.layout_sha256});
  const allocated = new Set();
  try {
    const old = new Map(parent.parts.map(part => [part.name, part]));
    const replacements = new Map();
    for (const row of [...data.common_replacements, ...data[`${variant}_replacements`]]) {
      require(old.get(row.name)?.fabrication.kind === row.fabrication.kind, `parent part missing: ${row.name}`);
      const geometry = meshGeometry(THREE, row.mesh, topologies); allocated.add(geometry); geometry.computeBoundingBox();
      const dimensions = ['x', 'y', 'z'].map(axis => geometry.boundingBox.max[axis] - geometry.boundingBox.min[axis]);
      require(dimensions.every(value => Number.isFinite(value) && value > 0), 'finite replacement extent required');
      const part = {...old.get(row.name), geometry, fabrication: {...old.get(row.name).fabrication, ...row.fabrication,
        dimensions_mm: dimensions, layer: 'eoere_uniform_channels', display_class: 'eoere_uniform_channels'}};
      delete part.path; replacements.set(row.name, part);
    }
    const parts = parent.parts.map(part => replacements.get(part.name) || part);
    require(parts.length === data.counts[variant].total_visible_parts && new Set(parts.map(part => part.name)).size === parts.length, 'visible census differs');
    for (const name of replacements.keys()) old.get(name).geometry?.dispose();
    return {...parent, parts, design: {...parent.design,
      key: variant === 'base' ? 'eoere-uniform-channels-frame-development' : 'eoere-uniform-channels-2026-development', qualified_for_design: false},
      meta: {...parent.meta, revision: REVISION, source_sha256: options.expectedSha256, decoded_sha256: options.decodedSha256,
        layout_sha256: options.layoutSha256, uniform_channel_variant: variant, changed_visible_parts: replacements.size,
        analysis_pass_transferred: false, complete_joint_acceptance: false, physical_release: false, planning_mass_kg: null}};
  } catch (error) {
    for (const geometry of allocated) geometry.dispose();
    for (const part of parent.parts) part.geometry?.dispose();
    throw error;
  }
}
