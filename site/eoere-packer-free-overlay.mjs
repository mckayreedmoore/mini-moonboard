import {loadStandardStockScene as loadParent} from './eoere-standard-stock-overlay.mjs';
import {meshGeometry, decodeTypedArray, sha256} from './wood-joints-overlay.mjs';
import {validateV10ComposedParts} from './eoere-v10-overlay.mjs';

export const PACKER_FREE_MODEL = 'eoere-packer-free-standard-stock-preview';
export const PACKER_FREE_REVISION = 'v10-packer-free-flush-return-far-row-only-v1';
export const PACKER_FREE_STATUS = 'Packer-free standard 4×6 geometry trial · results pending. 112 bolt stacks, 24 angles and 66 Hillman screws. Nominal occupied clearance checked; complete connections and actual installation remain unqualified. No fabrication or climbing release.';
export const PACKER_FREE_ASSETS = Object.freeze({provenance: 'eoere-packer-free-provenance.json',
  provenanceSha256: '6730ce627aa2a44c1048d357b4d36dbdd379127cf75e0f6df0fd1a08a9e57ca0'});
const FROZEN_STATUS = 'Packer-free standard 4×6 frame preview. Matched geometry-specific results pending.';
const PARENT = '5364ab82cf3ae1afc90b5b099376211b06b592c20a3640e73fad44c9291e30ea';
const GEOMETRY = '9510653b41d2c0c710f4eea02c9867c44367cd2909d6b3af56716c74cfd68bde';
const RECEIPT = '73b097d9bcc364748ca08f897fca38cc2bdb7869cc04586e6706afb9b9d3d527';
const CLEARANCE = '94c383b75d1223cc87813bd70a011d26da4e384064dec348b34bc1cf3eae0057';
const BUILD = '04d8fb2f125a5f9f9b9aa75bc47ec3f9d93a631ceb863a2920d4243687df3a94';
const EXPORT = 'e19aa1ac5dacde0d9346dd76ecdf3eb5f24740e8ab321a96d943371d5f4c8944';
const SCENE = 'd411401ab67f5d29ce509800fcb0beac0dfed26188b90fc0af76bc05fa2ddd07';
const DECODED = '5bd6dc85faa6a764a5abd37327d8813870b98e3be00ffe678dc848daebb6cd61';
const RECEIPT_PATH = 'docs/bolted-frame-development/owner-frame-v10/packer-free/geometry-receipt.json';
const COUNTS = {Hillman_axes:66,angles:24,bolt_stacks:112,occupied_parts:1125,panels:6,plywood_cleats:4,sawn_members:20,spacer_pieces:40};
const SHA = /^[a-f0-9]{64}$/;
const require = (ok, message) => {if (!ok) throw new Error('Packer-free preview: '+message);};
const OMITTED = [1,2,3,4].map(n => 'v10_top_bolt_'+String(n).padStart(3, '0'));
const POSTS = ['eoere_bolt_006', 'eoere_bolt_009', 'eoere_bolt_010', 'eoere_bolt_013'];
const REMOVALS = ['top_packer_left', 'top_packer_right', ...OMITTED.flatMap(id =>
  ['head', 'head_washer', 'shaft', 'nut_washer', 'nut'].map(role => id+'_'+role)), ...POSTS.map(id => id+'_spacer')];
const FLAGS = ['current_response_computed', 'current_own_response_bank_recorded', 'historical_capacity_transferred',
  'structural_acceptance', 'complete_joint_qualified', 'complete_group_qualified', 'physical_force_bounds_established',
  'fabrication_released', 'climbing_released', 'purchase_authorized', 'physical_changes_authorized', 'current_alias_promoted'];
const finite = (values, n) => Array.isArray(values) && values.length === n && values.every(Number.isFinite);

export function validatePackerFreeProvenance(data, exported) {
  require(data.schema === 'eoere_packer_free_viewer_provenance/v1' && data.model === PACKER_FREE_MODEL &&
    data.geometry_revision === PACKER_FREE_REVISION && data.geometry_sha256 === GEOMETRY &&
    data.geometry_receipt?.path === RECEIPT_PATH && data.geometry_receipt.sha256 === RECEIPT &&
    data.checked_clearance_sha256 === CLEARANCE && data.build_manifest_sha256 === BUILD &&
    Object.entries(COUNTS).every(([key,value]) => data.counts?.[key] === value), 'portable geometry identity/census differs');
  require(data.parent_provenance?.path === 'site/eoere-standard-stock-provenance.json' && data.parent_provenance.sha256 === PARENT &&
    data.scene?.path === 'site/eoere-packer-free-scene.json.gz' && data.scene.sha256 === SCENE && data.scene.decoded_sha256 === DECODED &&
    data.scene.bytes === 56842 && data.frozen_export?.path === 'site/eoere-packer-free-export.json' && data.frozen_export.sha256 === EXPORT && data.frozen_export.bytes === 628 &&
    data.source_export_manifest?.path === 'fea/generated/v10-packer-free-v1/viewer/export-v1/viewer-manifest.json' &&
    data.source_export_manifest.sha256 === EXPORT && data.source_scene?.path === 'fea/generated/v10-packer-free-v1/viewer/export-v1/scene-delta.json.gz' &&
    data.source_scene.sha256 === SCENE, 'preserved export or parent binding differs');
  require(data.status === PACKER_FREE_STATUS && data.geometry_only === true && data.matched_results_pending === true &&
    data.nominal_geometry_clear === true && data.packers_present === false && data.top_grid_qualified === false &&
    data.ignored_runtime_dependencies === false && data.unchanged_mesh_bytes_copied === 0 && data.raw_case_operator_banks_copied === false &&
    data.fresh_mesh_payloads === 1 && data.rigid_mesh_reuses === 42 && data.removed_parts === 26 &&
    data.actual_Cg_adopted === null && data.actual_Cdelta_adopted === null && data.complete_connection_capacity === null,
  'geometry-only pending scope differs');
  for (const name of FLAGS) require(data[name] === false, 'no result or qualification transfer: '+name);
  require(!['response_bank','result_sources','result_contract','declared_vector_reference','diagnostic_case_rows','diagnostic_components'].some(key => key in data),
    'no force metadata belongs to this geometry-only preview');
  require(exported.schema === 'eoere_packer_free_preview/v1' && exported.key === PACKER_FREE_MODEL && exported.revision === PACKER_FREE_REVISION &&
    exported.matched_results_pending === true && exported.current_alias_promoted === false && exported.status === FROZEN_STATUS &&
    exported.scene?.sha256 === SCENE && exported.scene.decoded_sha256 === DECODED && exported.receipt?.sha256 === RECEIPT,
  'original frozen export differs');
  const documents = [RECEIPT_PATH, 'docs/bolted-frame-development/README.md',
    'docs/bolted-frame-development/owner-frame-v10/owner-no-wood-packers-v1.json', 'docs/bolted-frame-development/builder-plan.md'];
  require(data.documents?.length === documents.length && documents.every(path => data.documents.some(row => row.path === path && typeof row.label === 'string')),
    'geometry/owner/scope documents required');
  return data;
}

export function validatePackerFreeDelta(data) {
  require(data.schema === 'eoere_packer_free_scene_delta/v1' && data.key === PACKER_FREE_MODEL &&
    data.revision === PACKER_FREE_REVISION && data.parent_provenance?.sha256 === PARENT, 'new explicit candidate/source required');
  for (const name of ['geometry_receipt', 'geometry_source', 'clearance_source', 'build_manifest'])
    require(typeof data[name]?.path === 'string' && SHA.test(data[name].sha256 || ''), 'actual bound source missing: '+name);
  require(data.geometry_source.sha256 === GEOMETRY && data.geometry_receipt.sha256 === RECEIPT &&
    data.clearance_source.sha256 === CLEARANCE && data.build_manifest.sha256 === BUILD, 'new candidate geometry required');
  require(data.packers_present === false && data.matched_results_pending === true && data.status === FROZEN_STATUS &&
    data.unchanged_mesh_bytes_copied === 0 && data.part_count === 1151-REMOVALS.length && data.counts?.occupied_parts === data.part_count &&
    data.counts.bolt_stacks === 112 && data.counts.Hillman_axes === 66 && data.counts.angles === 24 && data.counts.spacer_pieces === 40,
  'packer-free inventory/pending scope differs');
  for (const name of FLAGS) require(data[name] === false, 'no prior result or qualification transfer: '+name);
  require(!['response_bank','result_sources','result_contract','declared_vector_reference','diagnostic_case_rows','diagnostic_components'].some(key => key in data),
    'no inherited force metadata in the geometry-only delta');
  require(data.removals?.length === REMOVALS.length && new Set(data.removals).size === REMOVALS.length &&
    REMOVALS.every(id => data.removals.includes(id)), 'exact packer/stack/spacer removals required');
  require(data.replacements?.length === 1 && data.replacements[0].name === 'base_rail_top' && data.replacements[0].mesh && Array.isArray(data.reuses),
    'only one new top-rail mesh permitted');
  const requiredReuses = ['eoere_clip_single_top_left_1', 'eoere_clip_single_top_right_2',
    ...['eoere_bolt_001','eoere_bolt_005','eoere_bolt_017','eoere_bolt_018'].flatMap(id=>['head','head_washer','shaft','nut_washer','nut'].map(role=>id+'_'+role)),
    ...POSTS.flatMap(id=>['head','head_washer','shaft','nut_washer','nut'].map(role=>id+'_'+role))];
  require(requiredReuses.every(name=>data.reuses.some(row=>row.name===name))&&data.reuses.length===42,
    'moved and shortened hardware/angles need explicit bound mesh reuse');
  const changed = [...data.replacements, ...data.reuses];
  require(new Set([...changed.map(row => row.name), ...data.removals]).size === changed.length+REMOVALS.length, 'delta identities overlap');
  for (const row of changed) require(finite(row.target_bounds_xyz_mm, 6) && [0,2,4].every(k =>
    row.target_bounds_xyz_mm[k] <= row.target_bounds_xyz_mm[k+1]), 'finite ordered current CAD bounds required');
  for (const row of data.reuses) {
    const m = row.matrix_row_major;
    require(typeof row.source_parent_name === 'string' && SHA.test(row.source?.sha256 || '') && SHA.test(row.target?.sha256 || '') &&
      finite(m, 16) && JSON.stringify(m.slice(12)) === '[0,0,0,1]', 'bound current-parent rigid reuse required');
    for (let i=0;i<3;i++) for (let j=0;j<3;j++) require(Math.abs([0,1,2].reduce((sum,k) => sum+m[4*i+k]*m[4*j+k],0)-(i===j?1:0)) < 1e-8,
      'reuse cannot scale or shear');
    require(Math.abs(m[0]*(m[5]*m[10]-m[6]*m[9])-m[1]*(m[4]*m[10]-m[6]*m[8])+m[2]*(m[4]*m[9]-m[5]*m[8])-1) < 1e-8,
      'reuse cannot reflect');
  }
  require(data.stack_updates?.length === 112 && new Set(data.stack_updates.map(row => row.axis_id)).size === 112 &&
    !data.stack_updates.some(row => OMITTED.includes(row.axis_id)), '112 current complete stack records required');
  for (const id of POSTS) {
    const row = data.stack_updates.find(item => item.axis_id === id);
    require(row?.selected_product === 'G0341148' && row.selected_underhead_length_mm === 120.65 && row.spacer_piece_count === 0 &&
      row.selected_nut_SKU === '2571' && row.selected_washer_SKU === '15023', 'current shorter side-post stack required');
  }
  return data;
}

function bounds(geometry, row) {
  geometry.computeBoundingBox(); geometry.computeBoundingSphere();
  const b = geometry.boundingBox, actual = [b.min.x,b.max.x,b.min.y,b.max.y,b.min.z,b.max.z];
  require(actual.every((value,i) => Math.abs(value-row.target_bounds_xyz_mm[i]) < .55), 'display differs from target CAD bounds: '+row.name);
}

export function applyPackerFreeDelta(THREE, parent, input, topologies, makeMesh = meshGeometry) {
  const data = validatePackerFreeDelta(input);
  require(parent.parts.length === 1151 && parent.design?.key === 'eoere-standard-4x6-top-and-sides-preview' &&
    parent.meta?.provenance_sha256 === PARENT, 'exact portable stock parent required');
  const old = new Map(parent.parts.map(part => [part.name, part])), changed = new Map(), allocated = [];
  try {
    require(data.removals.every(name => old.has(name)), 'removed parent part missing');
    for (const row of data.reuses) {
      const previous = old.get(row.name), source = old.get(row.source_parent_name); require(previous && source?.geometry, 'parent reuse source/target missing');
      const geometry = source.geometry.clone().applyMatrix4(new THREE.Matrix4().set(...row.matrix_row_major)); allocated.push(geometry); bounds(geometry,row);
      const part = {...previous, geometry}; delete part.path; changed.set(row.name,part);
    }
    for (const row of data.replacements) {
      const previous = old.get(row.name); require(previous, 'top-rail parent missing');
      const geometry = makeMesh(THREE,row.mesh,topologies); allocated.push(geometry); bounds(geometry,row);
      const part = {...previous, geometry}; delete part.path; changed.set(row.name,part);
    }
    let parts = parent.parts.filter(part => !data.removals.includes(part.name)).map(part => changed.get(part.name)||part);
    const selections = new Map(data.stack_updates.map(row => [row.axis_id,row])), roles = new Map();
    for (const part of parts) if (part.fabrication?.kind === 'bolt') {
      const f = part.fabrication; if (!roles.has(f.connection_name)) roles.set(f.connection_name,[]); roles.get(f.connection_name).push(f.hardware_role);
    }
    parts = parts.map(part => {
      const f = part.fabrication; if (!f) return part;
      const selection = f.kind === 'bolt' ? selections.get(f.connection_name) : null;
      if (f.kind === 'bolt') require(selection,'new complete stack recipe missing');
      const row = [...data.replacements,...data.reuses].find(item => item.name === part.name), box = row?.target_bounds_xyz_mm;
      return {...part, fabrication: {...f,...selection, kind:f.kind, connection_name:f.connection_name, hardware_role:f.hardware_role,
        stack_roles:selection?roles.get(f.connection_name):f.stack_roles, dimensions_mm:box?[0,1,2].map(k=>box[2*k+1]-box[2*k]):f.dimensions_mm,
        owner_frame_revision:data.revision, actual_parts_verified:false, complete_joint_qualified:false, minimum_body_reference_qualified:false,
        description:(selection?`${f.connection_name}: ${selection.selected_bolt_grade}; nominal bolt length ${Number(selection.selected_underhead_length_mm).toFixed(3)} mm; `:
          'Packer-free standard 4×6 frame; member lengths provisional; ')+
          'actual material, hardware grade and fit unobserved. Matched geometry-specific results pending.'}};
    });
    validateV10ComposedParts(parts,data);
    require(!parts.some(part=>['top_packer_left','top_packer_right'].includes(part.name)) &&
      parts.filter(part=>part.fabrication?.hardware_role?.startsWith('spacer')).length===40,'no packers and 40 spacers required');
    for (const part of parent.parts) if (changed.has(part.name)||data.removals.includes(part.name)) part.geometry?.dispose();
    return {...parent,parts,design:{...parent.design,key:PACKER_FREE_MODEL,qualified_for_design:false,documents:[]},
      meta:{revision:data.revision,counts:data.counts,status:data.status,layout_sha256:data.geometry_receipt.sha256,
        matched_results_pending:true,current_response_computed:false,current_own_response_bank_recorded:false,
        packers_present:false,actual_Cg_adopted:null,actual_Cdelta_adopted:null,complete_connection_capacity:null,
        structural_acceptance:false,physical_release:false,complete_joint_acceptance:false,complete_group_qualified:false,
        top_grid_qualified:false,purchase_authorized:false,current_alias_promoted:false,analysis_pass_transferred:false,planning_mass_kg:null,
        parent_sources:{provenance:data.parent_provenance},portable_sources:{geometry_receipt:data.geometry_receipt,
          geometry:data.geometry_source,clearance:data.clearance_source,build_manifest:data.build_manifest}}};
  } catch(error) {
    allocated.forEach(geometry=>geometry.dispose());parent.parts.forEach(part=>part.geometry?.dispose());throw error;
  }
}

async function readAsset(name, expected) {
  const response = await fetch(new URL(name, import.meta.url));
  require(response.ok, 'portable asset unavailable: '+name);
  const raw = await response.arrayBuffer();
  require(await sha256(raw) === expected, 'portable asset bytes changed: '+name);
  return raw;
}

// The public parent supplies shared mesh data only. Its force status is discarded by applyPackerFreeDelta.
export async function loadPackerFreeScene(THREE, options, parentLoader = loadParent) {
  const provenance = JSON.parse(new TextDecoder().decode(await readAsset(PACKER_FREE_ASSETS.provenance, PACKER_FREE_ASSETS.provenanceSha256)));
  const exported = JSON.parse(new TextDecoder().decode(await readAsset('eoere-packer-free-export.json', EXPORT)));
  validatePackerFreeProvenance(provenance, exported);
  const encoded = await readAsset('eoere-packer-free-scene.json.gz', SCENE);
  const decoded = await new Response(new Blob([encoded]).stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer();
  require(await sha256(decoded) === DECODED, 'decoded frozen delta changed');
  const data = validatePackerFreeDelta(JSON.parse(new TextDecoder().decode(decoded))), topologies = new Map();
  for (const [hash, row] of Object.entries(data.triangle_topologies)) {
    const indices = decodeTypedArray(row.triangle_indices_base64, row.triangle_component_type, row.index_count);
    require(await sha256(indices.bytes) === hash, 'topology bytes changed');
    topologies.set(hash, {...row, indices:indices.values});
  }
  const result = applyPackerFreeDelta(THREE, await parentLoader(THREE, options), data, topologies);
  return {...result, design:{...result.design, documents:provenance.documents},
    meta:{...result.meta, status:PACKER_FREE_STATUS, geometry_sha256:GEOMETRY,
      provenance_sha256:PACKER_FREE_ASSETS.provenanceSha256, source_sha256:SCENE,
      source_export_manifest:provenance.source_export_manifest,
      portable_sources:{...result.meta.portable_sources, geometry_receipt:provenance.geometry_receipt}}};
}

