// Separate unadopted preview; the Z200 parent and its numerical fields stay intact.
import {meshGeometry, sha256, decodeTypedArray} from './wood-joints-overlay.mjs';
import {loadExtendedCleatBaseScene} from './eoere-cleat-extension-overlay.mjs';

const REVISION = 'eoere-lower-cleat-z180-proposal-v1';
const MODEL = 'eoere-lower-cleat-z180-development';
const SHA = /^[0-9a-f]{64}$/;
const HOSTS = ['base_post_outer_left', 'base_post_outer_right', 'eoere_cleat_left', 'eoere_cleat_right'];
const AXES = ['cleat_post_bolt_left_1', 'cleat_post_bolt_left_2', 'cleat_post_bolt_right_1', 'cleat_post_bolt_right_2'];
const ROLES = ['shaft', 'head', 'head_washer', 'nut_washer', 'nut'];
const PARENT = Object.freeze({url: 'eoere-cleat-extension-scene.json.gz',
  sha256: 'ae6315463f0482597075a769ad3ee55630b4c8b430c2ae93137c5232cc6dbb54',
  decoded_sha256: '6c39b4a240f8033491bbd43c437d60dc888c524e90b350e53351eaf28ddc5db6',
  layout_sha256: '01ba30abe20c2efec136374b8d9a74a098a19929be3cc784b5ebcf7608e62a2d'});
const REPORT = 'fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/cleat-remedy-v1/current-source-followup-v1/viewer-revision-v1/runs-v1/export01/layout.json';
function require(ok, message) { if (!ok) throw new Error(`Z180 preview: ${message}`); }

export function validateLowerCleatPreview(data, layoutSha256) {
  require(data?.schema === 'eoere_lower_cleat_z180_display_patch/v1' && data.revision === REVISION &&
    data.candidate === 'compact-floor-flush-eoere-bolted-development' &&
    data.status === 'UNADOPTED_GEOMETRY_PREVIEW', 'separate proposal identity required');
  require(SHA.test(layoutSha256 || '') && data.layout_report?.sha256 === layoutSha256 &&
    data.layout_report.path === REPORT, 'proposal descriptor binding required');
  require(Object.entries(PARENT).every(([key, value]) => data.parent_scene?.[key] === value), 'Z200 parent differs');
  require(data.optional_2026_extra === false && data.saved_response_transferred === false &&
    data.complete_joint_resistance === null && data.release?.geometry_adopted === false &&
    Object.keys(data.release).length === 6 && Object.values(data.release).every(value => value === false),
    'unadopted geometry with no transferred response or release required');
  const counts = data.counts;
  for (const [key, value] of Object.entries({timber: 22, panel: 6, bracket: 22, bolt: 500,
    physical_bolt_axes: 100, screw: 66, lights: 132, tnuts: 142, wire: 131, total_visible_parts: 1021}))
    require(counts?.[key] === value, `${key} census differs`);
  require(Array.isArray(data.replacements) && data.replacements.length === 4 &&
    new Set(data.replacements.map(row => row.name)).size === 4 &&
    data.replacements.every(row => HOSTS.includes(row.name) && row.id === row.name && row.mesh &&
      !row.transform && !row.template_id && SHA.test(row.source_brep_sha256 || '') &&
      row.fabrication?.kind === 'timber' && row.fabrication.lower_cleat_revision === REVISION),
    'four direct saved receiver meshes required');
  require(Array.isArray(data.bolt_translations) && data.bolt_translations.length === 4 &&
    new Set(data.bolt_translations.map(row => row.axis_id)).size === 4 &&
    data.bolt_translations.every(row => AXES.includes(row.axis_id) &&
      JSON.stringify(row.translation_xyz_mm) === '[0,0,-20]'), 'exactly four 20-mm lower bolt moves required');
  return data;
}

export async function loadLowerCleatPreviewScene(THREE, options) {
  require(SHA.test(options.expectedSha256 || '') && SHA.test(options.decodedSha256 || ''), 'scene hashes required');
  const response = await fetch(options.url);
  require(response.ok, `scene request failed (${response.status})`);
  const encoded = await response.arrayBuffer();
  require(await sha256(encoded) === options.expectedSha256, 'compressed bytes differ');
  const decoded = await new Response(new Blob([encoded]).stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer();
  require(await sha256(decoded) === options.decodedSha256, 'decoded bytes differ');
  const data = validateLowerCleatPreview(JSON.parse(new TextDecoder('utf-8', {fatal: true}).decode(decoded)), options.layoutSha256);
  const topologies = new Map();
  for (const [digest, row] of Object.entries(data.triangle_topologies)) {
    require(SHA.test(digest) && ['uint16', 'uint32'].includes(row.triangle_component_type) &&
      Number.isInteger(row.triangle_count) && row.triangle_count > 0 && row.index_count === row.triangle_count * 3,
      'valid triangle topology required');
    const indices = decodeTypedArray(row.triangle_indices_base64, row.triangle_component_type, row.index_count);
    require(await sha256(indices.bytes) === digest, 'triangle bytes differ');
    topologies.set(digest, {...row, indices: indices.values});
  }
  const parent = await loadExtendedCleatBaseScene(THREE, {...options, url: PARENT.url,
    expectedSha256: PARENT.sha256, decodedSha256: PARENT.decoded_sha256, layoutSha256: PARENT.layout_sha256});
  const allocated = new Set();
  try {
    const old = new Map(parent.parts.map(part => [part.name, part]));
    const replacements = new Map();
    for (const row of data.replacements) {
      require(old.get(row.name)?.fabrication.kind === 'timber', 'parent receiver missing');
      const geometry = meshGeometry(THREE, row.mesh, topologies); allocated.add(geometry);
      geometry.computeBoundingBox();
      const dimensions = ['x', 'y', 'z'].map(axis => geometry.boundingBox.max[axis] - geometry.boundingBox.min[axis]);
      require(dimensions.every(value => Number.isFinite(value) && value > 0), 'finite receiver extent required');
      const part = {...old.get(row.name), geometry, fabrication: {...old.get(row.name).fabrication,
        ...row.fabrication, dimensions_mm: dimensions,
        description: 'Z180 proposal receiver; two lower bores moved down 20 mm; other cuts retained.'}};
      delete part.path;
      replacements.set(row.name, part);
    }
    for (const axis of AXES) for (const role of ROLES) {
      const name = `${axis}_${role}`, part = old.get(name);
      require(part?.fabrication.kind === 'bolt' && part.fabrication.connection_name === axis &&
        part.fabrication.hardware_role === role && part.geometry, 'complete parent bolt role required');
      const geometry = part.geometry.clone().translate(0, 0, -20); allocated.add(geometry);
      geometry.computeBoundingBox();
      replacements.set(name, {...part, geometry, fabrication: {...part.fabrication,
        lower_cleat_revision: REVISION, world_translation_from_Z200_mm: [0, 0, -20]}});
    }
    const parts = parent.parts.map(part => replacements.get(part.name) || part);
    require(parts.length === 1021 && new Set(parts.map(part => part.name)).size === 1021 &&
      replacements.size === 24, 'receiver and hardware census differs');
    for (const name of replacements.keys()) old.get(name).geometry?.dispose();
    return {...parent, parts, design: {...parent.design, key: MODEL, qualified_for_design: false},
      meta: {...parent.meta, schema: data.schema, revision: REVISION, geometry_adopted: false,
        source_sha256: options.expectedSha256, decoded_sha256: options.decodedSha256, layout_sha256: options.layoutSha256,
        unchanged_visible_parts_reused: 997, translated_bolt_components: 20, replaced_receivers: 4,
        analysis_pass_transferred: false, complete_joint_acceptance: false, physical_release: false,
        optional_2026_extra: false, planning_mass_kg: null}};
  } catch (error) {
    for (const geometry of allocated) geometry.dispose();
    for (const part of parent.parts) part.geometry?.dispose();
    throw error;
  }
}
