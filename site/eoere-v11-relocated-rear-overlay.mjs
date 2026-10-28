// Ignored preparation only. The caller supplies a pinned raw114 geometry stage;
// do not call loadMatchingRearScene, which also loads historical114 results.
import {meshGeometry} from './wood-joints-overlay.mjs';
import {validateV10ComposedParts} from './eoere-v10-overlay.mjs';

export const RELOCATED_REAR_MODEL = 'eoere-v11-relocated-rear-preview';
const require = (ok, message) => {if (!ok) throw new Error('Relocated rear preview: '+message);};
const equal = (a, b) => JSON.stringify([...a].sort()) === JSON.stringify([...b].sort());

export function applyRelocatedRearGeometry(THREE, parent, data, topologies) {
  require(data.schema === 'eoere_v11_relocated_rear_scene/v1' && data.key === RELOCATED_REAR_MODEL && data.revision === 'v11-relocated-rear-pair-v1', 'own model required');
  require(parent.parts.length === 1099 && parent.design.key === 'eoere-v11-matching-rear-bolts-preview' && parent.meta.geometry_only === true &&
    parent.meta.analysis_pending === true && parent.meta.current_response_computed === false, 'raw geometry-only114 parent required');
  require(data.geometry_only === true && data.current_response_computed === false && data.analysis_pending === true && data.trial_selected === false &&
    data.historical_capacity_transferred === false, 'own results remain pending');
  require(data.replacements.length === 4 && data.reuses.length === 20 && data.relocated_axis_ids.length === 4 && data.stack_updates.length === 4, 'four wood bodies and20 same-ID role updates required');
  const old = new Map(parent.parts.map(part => [part.name, part])), changed = new Map(), allocated = [];
  const checkBounds = (geometry, row) => {geometry.computeBoundingBox(); geometry.computeBoundingSphere(); const b = geometry.boundingBox;
    require([b.min.x,b.max.x,b.min.y,b.max.y,b.min.z,b.max.z].every((value, k) => Math.abs(value-row.target_bounds_xyz_mm[k]) < .55), 'actual checked bounds: '+row.name);};
  try {
    for (const row of data.replacements) {require(old.has(row.name), 'known replacement body'); const geometry = meshGeometry(THREE, row.mesh, topologies);
      allocated.push(geometry); checkBounds(geometry, row); const part = {...old.get(row.name), geometry}; delete part.path; changed.set(row.name, part);}
    for (const row of data.reuses) {
      const source = old.get(row.source_parent_name), axis = data.axis_bindings[row.fabrication.connection_name], m = row.matrix_row_major;
      require(source?.geometry && row.name === row.source_parent_name && m.length === 16 && m.every(Number.isFinite) &&
        m.every((value, k) => [3,7,11].includes(k) || Math.abs(value-([0,5,10,15].includes(k) ? 1 : 0)) < 1e-9), 'known same-ID role and pure translation');
      require(axis.point_xyz_mm.every((value, k) => Math.abs(value-source.fabrication.axis_point_xyz_mm[k]-m[4*k+3]) < 1e-6) &&
        axis.direction_xyz.every((value, k) => Math.abs(value-source.fabrication.axis_direction_xyz[k]) < 1e-8), 'composed old114 physical line must match');
      const geometry = source.geometry.clone().applyMatrix4(new THREE.Matrix4().set(...m)); allocated.push(geometry); checkBounds(geometry, row);
      const selection = data.stack_updates.find(item => item.axis_id === axis.id);
      const part = {...source, geometry, fabrication: {...source.fabrication, ...selection, ...row.fabrication}};
      delete part.path; changed.set(row.name, part);
    }
    require(changed.size === 24, '24 distinct changed descriptors');
    const parts = parent.parts.map(part => {const current = changed.get(part.name) ?? part, fabrication = {...current.fabrication,
      owner_frame_revision: data.revision, actual_parts_verified: false, complete_joint_qualified: false};
      for (const key of ['analysis_reference','conditional_force_only_reference','unsupported_mixed_capacity']) delete fabrication[key];
      fabrication.description = 'Unselected relocated rear-pair geometry trial. Four receiver bodies have new bores; four half-inch stack positions are translated. Own analysis pending; complete connections unqualified.';
      return {...current, fabrication};});
    validateV10ComposedParts(parts, data);
    const bolts = parts.filter(part => part.fabrication.kind === 'bolt');
    require(equal([...new Set(bolts.map(part => part.fabrication.connection_name))], data.all_axis_ids) &&
      bolts.filter(part => part.fabrication.hardware_role?.endsWith('washer')).length === 228 &&
      bolts.filter(part => part.fabrication.hardware_role?.startsWith('spacer')).length === 4, 'actual114-stack census');
    const retained = new Set(parts.map(part => part.geometry));
    for (const name of changed.keys()) {const geometry = old.get(name).geometry; if (!retained.has(geometry)) geometry?.dispose();}
    return {parts, bounds_mm: parent.bounds_mm.map(row => [...row]), design: {...parent.design, key: RELOCATED_REAR_MODEL, qualified_for_design: false},
      meta: {revision: data.revision, geometry_sha256: data.geometry_source.sha256, layout_sha256: data.geometry_receipt.sha256,
        counts: data.counts, geometry_only: true, analysis_pending: true, current_response_computed: false, trial_selected: false,
        planning_mass_kg: null, weight_interpolation_available: false, historical_capacity_transferred: false,
        actual_Cg_adopted: null, actual_Cdelta_adopted: null, complete_connection_capacity: null,
        structural_acceptance: false, purchase_authorized: false, fabrication_released: false, climbing_released: false,
        status: 'Unselected relocated upper-rear pair · 114 stacks · four spacers · geometry only; own results pending. No fabrication or climbing release.',
        portable_sources: {geometry: data.geometry_source, geometry_receipt: data.geometry_receipt, clearance: data.clearance_source}}};
  } catch (error) {allocated.forEach(geometry => geometry.dispose()); throw error;}
}

import {loadShorterBoltScene} from './eoere-v11-shorter-bolts-overlay.mjs';
import {applyMatchingRearDelta} from './eoere-v11-matching-rear-bolts-overlay.mjs';
import {decodeTypedArray,sha256} from './wood-joints-overlay.mjs';
export const RELOCATED_REAR_ASSETS = Object.freeze({"path": "site/eoere-v11-relocated-rear-provenance.json", "sha256": "aa85ff0be29a73222551a14091d736d62dc08116b94c703c503fabd0754cc0e0"});
async function readRelocatedAsset(ref) {
  require(ref.path.startsWith('site/') && !ref.path.includes('..'), 'portable site asset required');
  const response = await fetch(new URL(ref.path.slice(5), import.meta.url)); require(response.ok, 'asset unavailable');
  const raw = await response.arrayBuffer(); require(await sha256(raw) === ref.sha256, 'asset pin differs');
  const decoded = ref.path.endsWith('.gz') ? await new Response(new Blob([raw]).stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer() : raw;
  if (ref.path.endsWith('.gz')) require(await sha256(decoded) === ref.decoded_sha256, 'decoded scene pin differs');
  return JSON.parse(new TextDecoder().decode(decoded));
}
async function relocatedTopologies(data) {
  const rows = new Map();
  for (const [hash, row] of Object.entries(data.triangle_topologies)) {
    const indices = decodeTypedArray(row.triangle_indices_base64, row.triangle_component_type, row.index_count);
    require(await sha256(indices.bytes) === hash, 'triangle topology pin differs'); rows.set(hash, {...row, indices: indices.values});
  }
  return rows;
}
export async function loadRelocatedRearGeometryScene(THREE, options) {
  const provenance = await readRelocatedAsset(RELOCATED_REAR_ASSETS);
  require(provenance.model === RELOCATED_REAR_MODEL && provenance.geometry_only === true && provenance.trial_selected === false &&
    provenance.ignored_runtime_dependencies === false, 'unselected own geometry provenance required');
  const parentProvenance = await readRelocatedAsset(provenance.parent_provenance);
  const parentData = await readRelocatedAsset(parentProvenance.scene);
  const parent = applyMatchingRearDelta(THREE, await loadShorterBoltScene(THREE, options), parentData, await relocatedTopologies(parentData));
  const data = await readRelocatedAsset(provenance.scene);
  require(data.geometry_source.sha256 === provenance.geometry.sha256 && data.geometry_receipt.sha256 === provenance.geometry_receipt.sha256,
    'own physical source joins differ');
  const scene = applyRelocatedRearGeometry(THREE, parent, data, await relocatedTopologies(data));
  return {...scene, meta: {...scene.meta, provenance_sha256: RELOCATED_REAR_ASSETS.sha256}};
}
