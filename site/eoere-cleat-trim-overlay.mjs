// Two changed cleats inherit the preserved raised-rail display and its meshes.
import {meshGeometry, sha256, decodeTypedArray} from './wood-joints-overlay.mjs';
import {loadEoereBottomRailScene, EOERE_BOTTOM_RAIL_COUNTS} from './eoere-bottom-rail-overlay.mjs';

export const EOERE_CLEAT_TRIM_REVISION = 'eoere-rear-trimmed-cleats-v1';
export const EOERE_CLEAT_TRIM_PARENT = Object.freeze({url: 'eoere-bottom-rail-scene.json.gz',
  sha256: '28269c01354dd901ad87604fe80475fcbb19cf71ad6cebec29194e7fe94cf536',
  decoded_sha256: '7e01f4d4cf96c7ab5f2a4ccfb8e0404a7b460a50e23b308138bdd1a0d38d1087',
  layout_sha256: 'ecfb27653a12ac326b1ba8cf4b051038d3de43db775bfc8f43e6c1a36be3744b'});
const IDS = ['eoere_cleat_left', 'eoere_cleat_right'];
const SHA = /^[0-9a-f]{64}$/;
const FLAGS = ['candidate_accepted', 'complete_joint_acceptance', 'capacity_established',
  'fabrication_released', 'structural_released', 'climbing_released'];

function require(ok, message) {
  if (!ok) throw new Error(`Eoere cleat trim: ${message}`);
}

export function validateEoereCleatTrimPatch(data, layoutSha256) {
  require(SHA.test(layoutSha256 || '') && data?.schema === 'eoere_cleat_trim_review_patch/v1' &&
    data.candidate === 'compact-floor-flush-eoere-bolted-development' &&
    data.revision === EOERE_CLEAT_TRIM_REVISION && data.status === 'REVISE_UNEVALUATED_GEOMETRY',
  'new identity and unevaluated geometry disposition required');
  require(FLAGS.every(flag => data.release?.[flag] === false) &&
    Object.values(data.release).every(value => value === false) && data.mechanics_ready === false &&
    data.design?.qualified_for_design === false && data.design.key === 'eoere-bolted-trimmed-cleats-development',
  'physical qualification flags or design differ');
  require(Object.entries(EOERE_CLEAT_TRIM_PARENT).every(([key, value]) => data.parent_scene?.[key] === value) &&
    data.layout_report?.sha256 === layoutSha256 &&
    data.layout_report.path === 'docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/occupied-cleat-trim-v1.json',
  'preserved parent or new geometry binding differs');
  require(Object.entries(EOERE_BOTTOM_RAIL_COUNTS).every(([key, value]) => data.counts?.[key] === value),
    'unchanged complete inventory required');
  require(Array.isArray(data.solids) && data.solids.length === 2 &&
    new Set(data.solids.map(row => row.name)).size === 2 && data.solids.every(row =>
      IDS.includes(row.name) && row.id === row.name && row.mesh && !row.template_id && !row.transform &&
      row.fabrication?.kind === 'timber' && row.fabrication.trim_revision === EOERE_CLEAT_TRIM_REVISION &&
      typeof row.fabrication.description === 'string' && row.fabrication.description.length),
  'exactly the two world-coordinate cleat replacements required');
  const references = new Set(data.solids.map(row => row.mesh.triangle_topology_sha256));
  require(data.triangle_topologies && Object.keys(data.triangle_topologies).length === references.size &&
    [...references].every(digest => SHA.test(digest) && data.triangle_topologies[digest]),
  'only the replacement triangle topologies required');
  return data;
}

export async function loadEoereCleatTrimScene(THREE, options) {
  require(SHA.test(options.expectedSha256 || ''), 'expected patch hash required');
  const response = await fetch(options.url);
  require(response.ok, `patch request failed (${response.status})`);
  const bytes = await response.arrayBuffer();
  require(await sha256(bytes) === options.expectedSha256, 'patch bytes differ');
  const data = validateEoereCleatTrimPatch(JSON.parse(new TextDecoder('utf-8', {fatal: true}).decode(bytes)), options.layoutSha256);
  const topologies = new Map();
  for (const [digest, row] of Object.entries(data.triangle_topologies)) {
    require(['uint16', 'uint32'].includes(row.triangle_component_type) && Number.isInteger(row.triangle_count) &&
      row.triangle_count > 0 && row.index_count === row.triangle_count*3, 'invalid replacement topology');
    const decoded = decodeTypedArray(row.triangle_indices_base64, row.triangle_component_type, row.index_count);
    require(await sha256(decoded.bytes) === digest, 'replacement topology bytes differ');
    topologies.set(digest, {...row, indices: decoded.values});
  }
  const parent = await loadEoereBottomRailScene(THREE, {...options, url: EOERE_CLEAT_TRIM_PARENT.url,
    expectedSha256: EOERE_CLEAT_TRIM_PARENT.sha256, decodedSha256: EOERE_CLEAT_TRIM_PARENT.decoded_sha256,
    layoutSha256: EOERE_CLEAT_TRIM_PARENT.layout_sha256});
  const allocated = new Set();
  try {
    const replacements = new Map();
    for (const row of data.solids) {
      const old = parent.parts.find(part => part.name === row.name);
      require(old?.geometry && old.fabrication.kind === 'timber', 'preserved cleat geometry missing');
      const geometry = meshGeometry(THREE, row.mesh, topologies);
      allocated.add(geometry); geometry.computeBoundingBox();
      const box = geometry.boundingBox;
      const dimensions = ['x', 'y', 'z'].map(axis => box.max[axis]-box.min[axis]);
      require(dimensions.every(value => Number.isFinite(value) && value > 0) && Math.abs(dimensions[0]-38.1) < 0.11,
        'full cleat thickness and valid display envelope required');
      replacements.set(row.name, {...old, geometry, fabrication: {...old.fabrication, ...row.fabrication,
        dimensions_mm: dimensions, layer: 'eoere_cleat_trim_candidate', display_class: 'eoere_cleat_trim_candidate'}});
    }
    const parts = parent.parts.map(part => replacements.get(part.name) || part);
    require(parts.length === 1021 && new Set(parts.map(part => part.name)).size === 1021,
      'complete visible inventory differs');
    for (const name of IDS) parent.parts.find(part => part.name === name).geometry.dispose();
    return {...parent, parts, design: {...parent.design, ...data.design, qualified_for_design: false},
      meta: {...parent.meta, schema: data.schema, revision: data.revision, status: data.status,
        source_sha256: options.expectedSha256, decoded_sha256: options.expectedSha256,
        layout_sha256: options.layoutSha256, parent_scene_sha256: EOERE_CLEAT_TRIM_PARENT.sha256,
        unchanged_visible_parts_reused: 1019, replaced_cleats: 2, analysis_pass_transferred: false,
        complete_joint_acceptance: false, physical_release: false, planning_mass_kg: null}};
  } catch (error) {
    for (const geometry of allocated) geometry.dispose();
    for (const part of parent.parts) part.geometry?.dispose();
    throw error;
  }
}
