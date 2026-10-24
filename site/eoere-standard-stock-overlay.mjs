import {loadV10Scene, validateV10ComposedParts} from './eoere-v10-overlay.mjs';
import {meshGeometry, decodeTypedArray, sha256} from './wood-joints-overlay.mjs';
import {isV10RepositoryPath} from './eoere-v10-provenance.mjs';

export const STANDARD_STOCK_MODEL = 'eoere-standard-4x6-top-and-sides-preview';
export const STANDARD_STOCK_REVISION = 'v10-standard-4x6-top-and-sides-development-v1';
export const STANDARD_STOCK_ASSETS = Object.freeze({provenance: 'eoere-standard-stock-provenance.json',
  provenanceSha256: '5364ab82cf3ae1afc90b5b099376211b06b592c20a3640e73fad44c9291e30ea'});
const GEOMETRY = 'c06d790aaed7d915cc729afaf3f5e58c456429c18a79555f1faf182775129a37';
const RECEIPT = 'd9df40fe76e08f008391cb276b8c2136abae09820273b541d10d49b5648d9ef2';
const C13 = '32abbcfcd2552d3df189ea35ab8c1c49d738f447e0dca5d1596eae310766b99f';
const RESULT_SOURCES = {geometry_receipt: RECEIPT,
  response_bank: '41f76a1ab0c66a1e5c7056e572f32f5627a11290ce2ed2f3b7e611a72a4a2393',
  reference_review: 'ff06a91e51028061737743e3f4b873f7ec7a3e4789d1b331dd62cfb66c25419e',
  diagnostic_inventory: '6282b51057b903d3cc0be8846d899363be04e6bb6094015027b7babc7032ef8f'};
const CASES = ['a12-forward', 'a12-left', 'a12-rear', 'k12-right', 'k12-rear', 'a1-rear'];
const COUNTS = {Hillman_axes: 66, angles: 24, bolt_stacks: 116, occupied_parts: 1151,
  panels: 6, plywood_cleats: 4, sawn_members: 22, spacer_pieces: 44};
const FLAGS = ['structural_acceptance', 'complete_joint_qualified', 'complete_group_qualified', 'top_grid_qualified',
  'physical_force_bounds_established', 'fabrication_released', 'climbing_released', 'purchase_authorized', 'physical_changes_authorized',
  'current_alias_promoted', 'custom_packers_approved', 'old_side_indices_or_group_acceptance_transferred'];
const SHA = /^[a-f0-9]{64}$/;
const require = (ok, message) => {if (!ok) throw new Error('Standard stock viewer: '+message);};
const finite = (row, n) => Array.isArray(row) && row.length === n && row.every(Number.isFinite);
const sameCounts = value => Object.entries(COUNTS).every(([key, count]) => value?.[key] === count);
const sourceRef = ref => isV10RepositoryPath(ref?.path) && SHA.test(ref.sha256 || '');

export function validateStandardStockProvenance(data, status) {
  require(data.schema === 'eoere_standard_stock_viewer_provenance/v1' && data.model === STANDARD_STOCK_MODEL &&
    data.geometry_revision === STANDARD_STOCK_REVISION && data.geometry_sha256 === GEOMETRY &&
    data.geometry_receipt_sha256 === RECEIPT && sameCounts(data.counts), 'current identity/census differs');
  for (const flag of FLAGS) require(data[flag] === false && status[flag] === false, 'qualification boundary: '+flag);
  require(data.ignored_runtime_dependencies === false && data.unchanged_mesh_bytes_copied === 0 &&
    data.raw_case_operator_banks_copied === false && data.fresh_mesh_payloads === 11 && data.rigid_mesh_reuses === 128 &&
    data.removed_spacer_parts === 16, 'portable sharing scope differs');
  require(data.parent_scene?.path === 'site/eoere-v10-scene-13.json.gz' && data.parent_scene.sha256 === C13 &&
    sourceRef(data.scene) && data.scene.path === 'site/eoere-standard-stock-scene.json.gz' &&
    data.status?.path === 'site/eoere-standard-stock-status.json' &&
    data.status.sha256 === '7d69296b0216a1dd51657dde6316f9609a064c7ec43bacd50dce215c75eda717', 'portable parent/assets differ');
  require(status.schema === 'eoere_standard_side_stock_review_status/v1' && status.key === STANDARD_STOCK_MODEL &&
    status.geometry_sha256 === GEOMETRY && status.geometry_revision === STANDARD_STOCK_REVISION && status.status_revision === 2 &&
    status.current_response_computed === true && status.current_own_response_bank_recorded === true && status.matched_results_pending === false &&
    status.actual_Cg_adopted === null && status.actual_Cdelta_adopted === null && status.complete_connection_capacity === null,
  'own-result status or unresolved group/capacity differs');
  for (const [name, hash] of Object.entries(RESULT_SOURCES)) {
    require(data.result_sources?.[name]?.sha256 === hash && sourceRef(data.result_sources[name]) &&
      data.result_sources[name].path.startsWith('docs/bolted-frame-development/owner-frame-v10/standard-side-stock/') &&
      status.sources?.[name]?.sha256 === hash && status.sources[name].path === data.result_sources[name].path, 'current source join differs: '+name);
  }
  const contract = data.result_contract, rows = contract?.case_rows;
  require(Array.isArray(rows) && rows.length === 6 && new Set(rows.map(row => row.case_id)).size === 6 &&
    CASES.every(id => rows.some(row => row.case_id === id)) && new Set(rows.map(row => row.field?.sha256)).size === 6 &&
    contract.admission_gate_N === 1e-5 && rows.every(row => row.both_independent_replays_admitted === true &&
      Number.isFinite(row.gradient_inf_N) && row.gradient_inf_N <= 1e-5 && sourceRef(row.field) &&
      sourceRef(row.independent_replay) && sourceRef(row.independent_plywood_replay) && row.independent_replay.sha256 !== row.independent_plywood_replay.sha256) &&
    Math.abs(contract.maximum_gradient_inf_N-Math.max(...rows.map(row => row.gradient_inf_N))) < 1e-14,
  'six distinct own admitted fields and both replays required');
  const load = contract.load_contract;
  require(load?.weight_lb === 250 && load.downward_multiplier === 2 && load.horizontal_force_N === 300 && load.accessory_mass_kg === 25 &&
    load.duration_factor_CD === 1 && contract.diagnostic_case_rows === 15 && contract.diagnostic_components === 8 &&
    contract.actual_Cg_adopted === null && contract.actual_Cdelta_adopted === null && contract.complete_connection_capacity === null,
  'load or diagnostic/qualification scope differs');
  const vector = contract.declared_vector_reference;
  require(vector?.index === 0.9985001243183798 && vector.metric === 'maximum_shear_torsion_reference_upper' &&
    vector.component === 'base_side_left' && vector.case_id === 'a12-rear' && status.declared_vector_reference?.index === vector.index &&
    status.summary?.diagnostic_case_rows === 15 && status.summary.diagnostic_components === 8 &&
    /declared conditional vector section reference reaches 0\.998500/.test(status.status) && /Custom packers remain unapproved/.test(status.status),
  'declared conditional vector reference differs from the scalar comparison');
  require(Array.isArray(data.documents) && data.documents.every(row => typeof row.label === 'string' && isV10RepositoryPath(row.path)), 'document paths differ');
  return data;
}

export function validateStandardStockScene(data) {
  require(data.schema === 'eoere_standard_stock_geometry_patch/v1' && data.key === STANDARD_STOCK_MODEL && data.revision === STANDARD_STOCK_REVISION &&
    data.geometry_sha256 === GEOMETRY && data.geometry_receipt_sha256 === RECEIPT && data.parent_scene?.sha256 === C13 &&
    data.parent_scene.path === 'eoere-v10-scene-13.json.gz' && data.parent_part_count === 1167 && data.part_count === 1151 && sameCounts(data.counts),
  'scene identity/current geometry differs');
  for (const key of ['custom_packers_approved', 'historical_capacity_transferred', 'structural_acceptance', 'actual_parts_verified',
    'complete_joint_qualified', 'fabrication_released', 'climbing_released']) require(data[key] === false, 'scene qualification: '+key);
  require(data.replacements?.length === 11 && data.reuses?.length === 128 && data.removals?.length === 16 &&
    new Set([...data.replacements.map(row => row.name), ...data.reuses.map(row => row.name), ...data.removals]).size === 155, 'patch identities/census differ');
  for (const row of [...data.replacements, ...data.reuses]) require(typeof row.name === 'string' && finite(row.target_bounds_xyz_mm, 6) &&
    [0, 2, 4].every(i => row.target_bounds_xyz_mm[i] <= row.target_bounds_xyz_mm[i+1]), 'bound target identity/bounds required');
  for (const row of data.reuses) {
    const m = row.matrix_row_major;
    require(typeof row.source_parent_name === 'string' && SHA.test(row.source?.sha256 || '') && SHA.test(row.target?.sha256 || '') &&
      finite(m, 16) && JSON.stringify(m.slice(12)) === '[0,0,0,1]', 'bound rigid reuse required');
    for (let i=0;i<3;i++) for (let j=0;j<3;j++) require(Math.abs([0,1,2].reduce((sum, k) => sum+m[4*i+k]*m[4*j+k], 0)-(i === j ? 1 : 0)) < 1e-8,
      'reuse cannot scale or shear');
    require(Math.abs(m[0]*(m[5]*m[10]-m[6]*m[9])-m[1]*(m[4]*m[10]-m[6]*m[8])+m[2]*(m[4]*m[9]-m[5]*m[8])-1) < 1e-8, 'reuse cannot reflect');
  }
  require(data.stack_updates?.length === 116 && new Set(data.stack_updates.map(row => row.axis_id)).size === 116 &&
    data.axis_updates?.length === 4 && data.screw_axis_updates?.length === 2, 'current complete stack/screw metadata required');
  const top = data.stack_updates.filter(row => row.receiver_member_ids === 'base_rail_top');
  require(top.length === 16 && top.every(row => row.selected_product === 'G0341148' && row.selected_underhead_length_mm === 120.65 &&
    row.selected_nut_SKU === '2571' && row.selected_washer_SKU === '15023' && row.spacer_piece_count === 0 &&
    data.removals.includes(row.axis_id+'_spacer') && row.full_smooth_body_through_wood_and_steel === false), 'top stack/removal contract differs');
  for (const id of ['rail_rear_bolt_left_1', 'rail_rear_bolt_right_1']) {
    const row = data.stack_updates.find(item => item.axis_id === id);
    require(row && String(row.selected_product) === '400' && row.minimum_body_mm === 72.644 && row.minimum_full_body_mm === 72.644 &&
      /conditional|unqualified/i.test(row.minimum_body_basis || ''), 'conditional product400 body reference differs');
  }
  require(new Set(data.axis_updates.map(row => row.axis_id)).size === 4 && ['eoere_bolt_006', 'eoere_bolt_009', 'eoere_bolt_010', 'eoere_bolt_013'].every(id =>
    data.axis_updates.some(row => row.axis_id === id && Math.abs(row.tip_projection_beyond_nut_mm-17.907) < 1e-6)), 'current tip metadata differs');
  return data;
}

function checkBounds(geometry, row) {
  geometry.computeBoundingBox(); geometry.computeBoundingSphere();
  const b = geometry.boundingBox, bounds = [b.min.x, b.max.x, b.min.y, b.max.y, b.min.z, b.max.z];
  require(bounds.every((value, i) => Math.abs(value-row.target_bounds_xyz_mm[i]) < .55), 'display differs from target CAD bounds: '+row.name);
}

export function applyStandardStockScene(THREE, parent, input, topologies, provenance, status) {
  const data = validateStandardStockScene(input); validateStandardStockProvenance(provenance, status);
  require(parent.parts.length === 1167, 'complete C13 parent required');
  const old = new Map(parent.parts.map(part => [part.name, part])), changes = new Map(), allocated = [];
  try {
    require(data.removals.every(name => old.has(name)), 'removed parent spacer missing');
    for (const row of data.reuses) {
      const source = old.get(row.source_parent_name), previous = old.get(row.name);
      require(source?.geometry && previous, 'parent template/target missing');
      const geometry = source.geometry.clone().applyMatrix4(new THREE.Matrix4().set(...row.matrix_row_major)); allocated.push(geometry);
      checkBounds(geometry, row);
      const part = {...previous, geometry, fabrication: {...previous.fabrication, ...row.fabrication}}; delete part.path; changes.set(row.name, part);
    }
    for (const row of data.replacements) {
      const previous = old.get(row.name); require(previous, 'replacement parent missing');
      const geometry = meshGeometry(THREE, row.mesh, topologies); allocated.push(geometry); checkBounds(geometry, row);
      const bounds = row.target_bounds_xyz_mm;
      const part = {...previous, geometry, fabrication: {...previous.fabrication, ...row.fabrication,
        dimensions_mm: [0,1,2].map(k => bounds[2*k+1]-bounds[2*k])}}; delete part.path; changes.set(row.name, part);
    }
    const parts = parent.parts.filter(part => !data.removals.includes(part.name)).map(part => changes.get(part.name) || part);
    const selections = new Map(data.stack_updates.map(row => [row.axis_id, row])), axisMetadata = new Map(data.axis_updates.map(row => [row.axis_id, row]));
    const roles = new Map();
    for (const part of parts) if (part.fabrication?.kind === 'bolt') {
      const f = part.fabrication; if (!roles.has(f.connection_name)) roles.set(f.connection_name, []); roles.get(f.connection_name).push(f.hardware_role);
    }
    for (const part of parts) {
      const f = part.fabrication; if (!f) continue;
      const selection = f.kind === 'bolt' ? selections.get(f.connection_name) : null;
      if (f.kind === 'bolt') require(selection, 'current stack recipe missing');
      const packer = ['top_packer_left', 'top_packer_right'].includes(part.name);
      const description = packer ? 'Custom solid packer; stock, material and connection disposition remains open.' :
        selection ? `${f.connection_name}: ${selection.selected_bolt_grade}; nominal bolt length ${Number(selection.selected_underhead_length_mm).toFixed(3)} mm; delivered grade and fit unobserved. `+
          (String(selection.selected_product) === '400' ? '72.644 mm body floor is a conditional screw-type reference; exact product conformity remains unverified.' : '') :
          'Current standard 4×6 top and both side rails; member lengths provisional and actual material/fit unobserved.';
      part.fabrication = {...f, ...selection, ...axisMetadata.get(f.connection_name), kind: f.kind, hardware_role: f.hardware_role,
        connection_name: f.connection_name, stack_roles: selection ? roles.get(f.connection_name) : f.stack_roles,
        dimensions_mm: f.dimensions_mm, owner_frame_revision: STANDARD_STOCK_REVISION, actual_parts_verified: false,
        complete_joint_qualified: false, minimum_body_reference_qualified: false,
        ...(packer ? {stock_disposition: 'CUSTOM UNAPPROVED', custom_packer_approved: false} : {}),
        description: description+' Own six-case results recorded; full joint qualification remains open.',
        clearance_status: 'Bound nominal occupied geometry clear; actual fit unobserved'};
    }
    validateV10ComposedParts(parts, data);
    require(parts.filter(part => part.fabrication?.hardware_role?.startsWith('spacer')).length === 44, 'current spacer count differs');
    for (const part of parent.parts) if (changes.has(part.name) || data.removals.includes(part.name)) part.geometry?.dispose();
    return {...parent, parts, design: {...parent.design, key: STANDARD_STOCK_MODEL, qualified_for_design: false, documents: provenance.documents},
      meta: {revision: STANDARD_STOCK_REVISION, counts: COUNTS, status: status.status, source_sha256: provenance.scene.sha256,
        layout_sha256: RECEIPT, geometry_sha256: GEOMETRY, provenance_sha256: STANDARD_STOCK_ASSETS.provenanceSha256,
        current_response_computed: true, current_own_response_bank_recorded: true, matched_results_pending: false,
        actual_Cg_adopted: null, actual_Cdelta_adopted: null, complete_connection_capacity: null, complete_joint_acceptance: false,
        complete_group_qualified: false, top_grid_qualified: false, structural_acceptance: false, physical_release: false,
        complete_joint_qualified: false, complete_conditional_frame_evaluation: false, physical_force_bounds_established: false,
        actual_parts_verified: false, fabrication_released: false, climbing_released: false, physical_changes_authorized: false,
        purchase_authorized: false, custom_packers_approved: false, current_alias_promoted: false, analysis_pass_transferred: false,
        declared_vector_reference: status.declared_vector_reference, diagnostic_case_rows: 15, diagnostic_components: 8,
        portable_sources: provenance.result_sources, planning_mass_kg: null}};
  } catch (error) {
    allocated.forEach(geometry => geometry.dispose()); parent.parts.forEach(part => part.geometry?.dispose()); throw error;
  }
}

export async function loadStandardStockScene(THREE, options, parentLoader = loadV10Scene) {
  const response = await fetch(STANDARD_STOCK_ASSETS.provenance); require(response.ok, 'provenance unavailable');
  const bytes = await response.arrayBuffer(); require(await sha256(bytes) === STANDARD_STOCK_ASSETS.provenanceSha256, 'provenance bytes differ');
  const provenance = JSON.parse(new TextDecoder().decode(bytes));
  const statusResponse = await fetch(provenance.status.path.slice(5)); require(statusResponse.ok, 'status unavailable');
  const statusBytes = await statusResponse.arrayBuffer(); require(await sha256(statusBytes) === provenance.status.sha256, 'status bytes differ');
  const status = JSON.parse(new TextDecoder().decode(statusBytes)); validateStandardStockProvenance(provenance, status);
  const sceneResponse = await fetch(provenance.scene.path.slice(5)); require(sceneResponse.ok, 'scene unavailable');
  const encoded = await sceneResponse.arrayBuffer(); require(await sha256(encoded) === provenance.scene.sha256, 'scene bytes differ');
  const decoded = await new Response(new Blob([encoded]).stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer();
  require(await sha256(decoded) === provenance.scene.decoded_sha256, 'decoded scene differs');
  const data = validateStandardStockScene(JSON.parse(new TextDecoder().decode(decoded))), topologies = new Map();
  for (const [hash, row] of Object.entries(data.triangle_topologies)) {
    const indices = decodeTypedArray(row.triangle_indices_base64, row.triangle_component_type, row.index_count);
    require(await sha256(indices.bytes) === hash, 'topology bytes differ'); topologies.set(hash, {...row, indices: indices.values});
  }
  const parent = await parentLoader(THREE, options);
  return applyStandardStockScene(THREE, parent, data, topologies, provenance, status);
}
