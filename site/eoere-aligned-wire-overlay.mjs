// Six rail and thirty cable meshes reuse the preserved trimmed-cleat display.
import {meshGeometry, sha256, decodeTypedArray} from './wood-joints-overlay.mjs';
import {loadEoereCleatTrimScene} from './eoere-cleat-trim-overlay.mjs';
import {EOERE_BOTTOM_RAIL_COUNTS} from './eoere-bottom-rail-overlay.mjs';

export const EOERE_ALIGNED_WIRE_PARENT = Object.freeze({url: 'eoere-cleat-trim-scene.json',
  sha256: 'e49ed92875c8de3dfafbab10755fb49175662c0c4a3eaf5affe247da04535c57',
  layout_sha256: '4223b78f85418b37832861d8eedc936381188e4e091750bbc8c112646d7f1056'});
export const EOERE_ALIGNED_RAIL_IDS = Object.freeze(['base_rail_bottom_left', 'base_rail_bottom_right',
  'base_rail_service_lower_left', 'base_rail_service_lower_right', 'base_rail_service_upper_left', 'base_rail_service_upper_right']);
export const EOERE_ALIGNED_WIRE_IDS = Object.freeze(['wire_001_A1_A2', 'wire_006_A6_A7', 'wire_007_A7_A8',
  'wire_017_B8_B7', 'wire_018_B7_B6', 'wire_023_B2_B1', 'wire_025_C1_C2', 'wire_030_C6_C7', 'wire_031_C7_C8',
  'wire_041_D8_D7', 'wire_042_D7_D6', 'wire_047_D2_D1', 'wire_049_E1_E2', 'wire_054_E6_E7', 'wire_055_E7_E8',
  'wire_073_G1_G2', 'wire_078_G6_G7', 'wire_079_G7_G8', 'wire_089_H8_H7', 'wire_090_H7_H6', 'wire_095_H2_H1',
  'wire_097_I1_I2', 'wire_102_I6_I7', 'wire_103_I7_I8', 'wire_113_J8_J7', 'wire_114_J7_J6', 'wire_119_J2_J1',
  'wire_121_K1_K2', 'wire_126_K6_K7', 'wire_127_K7_K8']);
const REVISION = 'eoere-grid-aligned-wire-cutouts-v1', SHA = /^[0-9a-f]{64}$/;
const IDS = [...EOERE_ALIGNED_RAIL_IDS, ...EOERE_ALIGNED_WIRE_IDS];
const FLAGS = ['candidate_accepted', 'complete_joint_acceptance', 'capacity_established',
  'fabrication_released', 'structural_released', 'climbing_released'];
function require(ok, message) { if (!ok) throw new Error(`Eoere aligned wire: ${message}`); }
const same = (first, second) => JSON.stringify(first) === JSON.stringify(second);

export function validateEoereAlignedWirePatch(data, layoutSha256) {
  require(SHA.test(layoutSha256 || '') && data?.schema === 'eoere_aligned_wire_cutouts_review_patch/v1' &&
    data.candidate === 'compact-floor-flush-eoere-bolted-development' && data.revision === REVISION &&
    data.status === 'REVISE_UNEVALUATED_GEOMETRY', 'distinct unevaluated geometry identity required');
  require(data.mechanics_ready === false && FLAGS.every(key => data.release?.[key] === false) &&
    Object.values(data.release).every(value => value === false) && data.design?.qualified_for_design === false &&
    data.design.key === 'eoere-bolted-aligned-wire-development', 'release or design flags differ');
  require(Object.entries(EOERE_ALIGNED_WIRE_PARENT).every(([key, value]) => data.parent_scene?.[key] === value) &&
    data.layout_report?.sha256 === layoutSha256 && data.layout_report.path ===
    'docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/occupied-aligned-wire-v1.json',
    'trimmed parent or geometry report binding differs');
  require(Object.entries(EOERE_BOTTOM_RAIL_COUNTS).every(([key, value]) => data.counts?.[key] === value),
    'complete frame inventory differs');
  require(same(data.changed_rail_ids, EOERE_ALIGNED_RAIL_IDS) && same(data.changed_wire_ids, EOERE_ALIGNED_WIRE_IDS) &&
    Array.isArray(data.solids) && data.solids.length === 36 && new Set(data.solids.map(row => row.name)).size === 36 &&
    data.solids.every(row => IDS.includes(row.name) && row.id === row.name && row.mesh && !row.transform &&
      !row.template_id && row.fabrication?.kind === (EOERE_ALIGNED_RAIL_IDS.includes(row.name) ? 'timber' : 'wire') &&
      row.fabrication.wire_cut_revision === REVISION), 'exact world-coordinate six-rail/thirty-wire replacements required');
  const references = new Set(data.solids.map(row => row.mesh.triangle_topology_sha256));
  require(data.triangle_topologies && Object.keys(data.triangle_topologies).length === references.size &&
    [...references].every(digest => SHA.test(digest) && data.triangle_topologies[digest]), 'only referenced replacement topologies required');
  return data;
}

export async function loadEoereAlignedWireScene(THREE, options) {
  require(SHA.test(options.expectedSha256 || ''), 'expected scene hash required');
  const response = await fetch(options.url);
  require(response.ok, `patch request failed (${response.status})`);
  const bytes = await response.arrayBuffer();
  require(await sha256(bytes) === options.expectedSha256, 'patch bytes differ');
  const data = validateEoereAlignedWirePatch(JSON.parse(new TextDecoder('utf-8', {fatal: true}).decode(bytes)), options.layoutSha256);
  const topologies = new Map();
  for (const [digest, row] of Object.entries(data.triangle_topologies)) {
    require(['uint16', 'uint32'].includes(row.triangle_component_type) && Number.isInteger(row.triangle_count) &&
      row.triangle_count > 0 && row.index_count === row.triangle_count*3, 'invalid topology');
    const decoded = decodeTypedArray(row.triangle_indices_base64, row.triangle_component_type, row.index_count);
    require(await sha256(decoded.bytes) === digest, 'topology bytes differ');
    topologies.set(digest, {...row, indices: decoded.values});
  }
  const parent = await loadEoereCleatTrimScene(THREE, {...options, url: EOERE_ALIGNED_WIRE_PARENT.url,
    expectedSha256: EOERE_ALIGNED_WIRE_PARENT.sha256, layoutSha256: EOERE_ALIGNED_WIRE_PARENT.layout_sha256});
  const allocated = new Set();
  try {
    const replacements = new Map();
    for (const row of data.solids) {
      const old = parent.parts.find(part => part.name === row.name);
      require(old && old.fabrication.kind === row.fabrication.kind, 'parent owner missing');
      const geometry = meshGeometry(THREE, row.mesh, topologies);
      allocated.add(geometry); geometry.computeBoundingBox();
      const dimensions = ['x', 'y', 'z'].map(axis => geometry.boundingBox.max[axis]-geometry.boundingBox.min[axis]);
      require(dimensions.every(value => Number.isFinite(value) && value > 0), 'valid displayed extent required');
      const replacement = {...old, geometry, fabrication: {...old.fabrication, ...row.fabrication,
        dimensions_mm: dimensions, layer: 'eoere_aligned_wire_candidate', display_class: 'eoere_aligned_wire_candidate'}};
      delete replacement.path;
      replacements.set(row.name, replacement);
    }
    const parts = parent.parts.map(part => replacements.get(part.name) || part);
    require(parts.length === 1021 && new Set(parts.map(part => part.name)).size === 1021, 'visible inventory differs');
    for (const id of IDS) parent.parts.find(part => part.name === id).geometry?.dispose();
    return {...parent, parts, design: {...parent.design, ...data.design, qualified_for_design: false},
      meta: {...parent.meta, schema: data.schema, revision: data.revision, status: data.status,
        source_sha256: options.expectedSha256, decoded_sha256: options.expectedSha256,
        layout_sha256: options.layoutSha256, parent_scene_sha256: EOERE_ALIGNED_WIRE_PARENT.sha256,
        unchanged_visible_parts_reused: 985, replaced_rails: 6, replaced_wire_links: 30,
        analysis_pass_transferred: false, complete_joint_acceptance: false, physical_release: false, planning_mass_kg: null}};
  } catch (error) {
    for (const geometry of allocated) geometry.dispose();
    for (const part of parent.parts) part.geometry?.dispose();
    throw error;
  }
}
